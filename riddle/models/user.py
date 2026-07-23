import hashlib
import secrets
import time
from datetime import datetime, timezone
from enum import IntEnum
from sqlite3 import Connection

from riddle.constants import TOKEN_LIFETIME_SECONDS
import click
import msgspec
from flask import Flask, current_app
from werkzeug.security import check_password_hash, generate_password_hash

from riddle.db import get_db


class UserStatus(IntEnum):
    PENDING = 0
    APPROVED = 1
    REJECTED = 2


class User(msgspec.Struct, frozen=True, eq=False, order=False, kw_only=True):
    id: int
    username: str
    password_hash: str
    status: UserStatus
    created_at: datetime


class UserRepo:
    __slots__ = ("_con",)

    def __init__(self, con: Connection):
        self._con = con

    def exists(self, username: str) -> bool:
        return (
            self._con.execute(
                "SELECT id from users where username = ? LIMIT 1", (username,)
            ).fetchone()
            is not None
        )

    def create(self, username: str, password: str) -> None:
        h = generate_password_hash(password)
        with self._con:
            self._con.execute(
                "INSERT INTO users (username, password_hash, status) VALUES (?, ?, ?)",
                (username, h, UserStatus.PENDING.value),
            )

    def get(self, username: str) -> User | None:
        item = self._con.execute(
            "SELECT * from users where username = ? LIMIT 1", (username,)
        ).fetchone()
        if item is None:
            return None
        return User(
            id=item["id"],
            username=item["username"],
            password_hash=item["password_hash"],
            status=UserStatus(item["status"]),
            created_at=datetime.fromtimestamp(item["created_at"], tz=timezone.utc),
        )

    def check_password(self, user: User, password: str) -> bool:
        return check_password_hash(user.password_hash, password)

    def create_token(self, user_id: int) -> tuple[str, int]:
        token = secrets.token_urlsafe(32)
        created_at = int(time.time())
        expires_at = TOKEN_LIFETIME_SECONDS + created_at

        with self._con:
            self._con.execute(
                "INSERT INTO tokens (user_id, token_hash, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (
                    user_id,
                    self.generate_token_hash(token),
                    created_at,
                    expires_at,
                ),
            )
        return token, expires_at

    def revoke_token(self, token: str):
        with self._con:
            self._con.execute(
                "UPDATE tokens SET revoked = 1 where token_hash = ?",
                (self.generate_token_hash(token),),
            )

    def generate_token_hash(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def get_by_token(self, token: str) -> User | None:
        item = self._con.execute(
            """
            SELECT tokens.user_id, users.username, users.status, users.created_at
            FROM tokens
            JOIN users ON users.id = tokens.user_id
            WHERE tokens.token_hash = ?
            AND tokens.revoked = 0
            AND tokens.expires_at > ?
            AND users.status = ?
            LIMIT 1
            """,
            (
                self.generate_token_hash(token),
                int(time.time()),
                UserStatus.APPROVED.value,
            ),
        ).fetchone()
        if item is None:
            return None
        return User(
            id=item["user_id"],
            username=item["username"],
            password_hash="",
            status=UserStatus(item["status"]),
            created_at=datetime.fromtimestamp(item["created_at"], tz=timezone.utc),
        )

    def approve_user(self, user: User):
        with self._con:
            self._con.execute(
                "UPDATE users SET status = ? where id = ?",
                (UserStatus.APPROVED, user.id),
            )


@click.command("approve-user", help="Approves a user")
@click.argument("username", type=str)
def approve_user(username: str):
    repo = UserRepo(get_db())
    user = repo.get(username)
    if not user:
        click.echo("No such user", err=True)
        raise click.exceptions.Exit(1)
    repo.approve_user(user)
    click.echo("Success")


def init_app(app: Flask) -> None:
    app.cli.add_command(approve_user)
