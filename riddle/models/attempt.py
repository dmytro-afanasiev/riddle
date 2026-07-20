import dataclasses
from datetime import datetime, timezone
from sqlite3 import Connection

from riddle.models.user import User


@dataclasses.dataclass(slots=True, repr=False, eq=False, kw_only=True, frozen=True)
class FinaleAttempt:
    id: int
    user_id: int
    username: str
    created_at: datetime
    input: str


class FinaleAttemptRepo:
    __slots__ = ("_con",)

    def __init__(self, con: Connection):
        self._con = con

    def create(self, user: User, inp: str) -> FinaleAttempt:
        with self._con:
            cur = self._con.execute(
                "INSERT INTO finale_attempts (user_id, username, input) VALUES (?, ?, ?) RETURNING *",
                (user.id, user.username, inp),
            )
            row = cur.fetchone()
            assert row is not None
        return FinaleAttempt(
            id=row["id"],
            user_id=user.id,
            username=user.username,
            created_at=datetime.fromtimestamp(row["created_at"], tz=timezone.utc),
            input=inp,
        )
