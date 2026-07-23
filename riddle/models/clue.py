import subprocess
import time
from datetime import datetime, timezone
from enum import IntEnum
from sqlite3 import Connection
from typing import Generator

import click
import msgspec
from flask import Flask
from riddle.constants import DATABASE_NAME

from riddle.db import get_db
from riddle.models.user import User, UserRepo


class ClueStatus(IntEnum):
    PENDING = 0
    ANSWERED = 1
    REJECTED = 2


class ClueRequest(msgspec.Struct, frozen=True, kw_only=True, eq=False, order=False):
    id: int
    user_id: int
    username: str
    created_at: datetime
    page: int
    description: str
    level: int
    status: ClueStatus
    answer: str | None = None
    closed_at: datetime | None = None


class ClueRequestRepo:
    __slots__ = ("_con",)

    def __init__(self, con: Connection):
        self._con = con

    def create(self, user: User, page: int, description: str, level: int) -> None:
        with self._con:
            self._con.execute(
                "INSERT INTO clue_requests (user_id, username, page, description, level) VALUES (?, ?, ?, ?, ?) RETURNING *",
                (user.id, user.username, page, description, level),
            )

    def get_latest_timestamp(self, user_id: int) -> int | None:
        item = self._con.execute(
            "SELECT created_at FROM clue_requests WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        if item is None:
            return None
        return item["created_at"]

    def get_next_clue(self, user_id: int) -> ClueRequest | None:
        """
        Returns the next clue to be answered
        """
        item = self._con.execute(
            "SELECT * FROM clue_requests WHERE user_id = ? AND status = ? ORDER BY created_at ASC LIMIT 1",
            (
                user_id,
                ClueStatus.PENDING.value,
            ),
        ).fetchone()
        if item is None:
            return None
        return ClueRequest(
            id=item["id"],
            user_id=item["user_id"],
            username=item["username"],
            created_at=datetime.fromtimestamp(item["created_at"], tz=timezone.utc),
            page=item["page"],
            description=item["description"],
            level=item["level"],
            status=ClueStatus(item["status"]),
        )

    def close_clue(self, id: int, status: ClueStatus, answer: str = "") -> None:
        with self._con:
            self._con.execute(
                "UPDATE clue_requests SET status = ?, answer = ?, closed_at = ? where id = ?",
                (status.value, answer, int(time.time()), id),
            )

    def query(
        self,
        user_id: int,
        ascending: bool = False,
        limit: int | None = None,
        offset: int = 0,
        status: ClueStatus | None = None,
    ) -> Generator[ClueRequest, None, None]:
        if offset and limit is None:
            raise AssertionError("invalid usage")

        q = "SELECT * FROM clue_requests WHERE user_id = ?"

        if status is not None:
            q += " AND status = ?"

        q += f" ORDER BY created_at {'ASC' if ascending else 'DESC'}"

        if limit is not None:
            q += f" LIMIT {limit} OFFSET {offset}"
        for item in self._con.execute(
            q, (user_id,) if status is None else (user_id, status.value)
        ):
            yield ClueRequest(
                id=item["id"],
                user_id=item["user_id"],
                username=item["username"],
                created_at=datetime.fromtimestamp(item["created_at"], tz=timezone.utc),
                page=item["page"],
                description=item["description"],
                level=item["level"],
                status=ClueStatus(item["status"]),
                answer=item["answer"],
                closed_at=datetime.fromtimestamp(item["closed_at"], tz=timezone.utc)
                if item["closed_at"] is not None
                else None,
            )


@click.command("get-pending-clues", help="Returns pending clues for a user")
@click.argument("username", type=str)
def get_pending(username: str):
    repo = UserRepo(get_db())
    user = repo.get(username)
    if not user:
        click.echo("No such user", err=True)
        raise click.exceptions.Exit(1)
    # NOTE: technically an SQL injection but this CLI command is only for local usage
    subprocess.run(
        [
            "sqlite3",
            "-column",
            "-header",
            DATABASE_NAME,
            f"SELECT id, page, level, description FROM clue_requests WHERE user_id = '{user.id}' AND status = {ClueStatus.PENDING.value} ORDER BY created_at ASC",
        ]
    )


def _finish_clue(username: str, status: ClueStatus, answer: str = ""):
    repo = UserRepo(get_db())
    user = repo.get(username)
    if not user:
        click.echo("No such user", err=True)
        raise click.exceptions.Exit(1)
    repo = ClueRequestRepo(get_db())
    clue = repo.get_next_clue(user.id)
    if not clue:
        click.echo("No clues are there")
        return
    repo.close_clue(clue.id, status, answer)


@click.command("answer-clue", help="Sets the answer to a clue")
@click.argument("username", type=str)
@click.argument("answer", type=str)
def answer_clue(username: str, answer: str):
    return _finish_clue(username, ClueStatus.ANSWERED, answer)


@click.command("reject-clue", help="Rejects a clue without an answer")
@click.argument("username", type=str)
def reject_clue(username: str):
    return _finish_clue(username, ClueStatus.REJECTED, "")


def init_app(app: Flask) -> None:
    app.cli.add_command(get_pending)
    app.cli.add_command(answer_clue)
    app.cli.add_command(reject_clue)
