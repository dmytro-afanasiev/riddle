import json
from enum import Enum, StrEnum
from sqlite3 import Connection
from typing import Any

from riddle.models.user import User


class KVKey(StrEnum):
    LAST_PHRASE_HASH = "last_phrase_hash"
    LAST_PHRASE_VALID_ATTEMPT_ID_PREFIX = "last_phrase_valid_attempt_id"

    @classmethod
    def last_phrase_valid_attempt_id_user(cls, user_id: int) -> str:
        return cls.LAST_PHRASE_VALID_ATTEMPT_ID_PREFIX + ":" + str(user_id)


class KVStore:
    __slots__ = ("_con",)
    MISSING = object()

    def __init__(self, con: Connection):
        self._con = con

    @staticmethod
    def _sanitize_key(key: str | KVKey) -> str:
        if isinstance(key, Enum):
            return key.value
        return key

    def set(self, key: str | KVKey, value: Any) -> None:
        key = self._sanitize_key(key)
        with self._con:
            self._con.execute(
                """
                INSERT INTO kv (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = strftime('%s', 'now')
                """,
                (key, json.dumps(value, separators=(",", ":"))),
            )

    def get(self, key: str | KVKey, default: Any = MISSING) -> Any:
        key = self._sanitize_key(key)
        item = self._con.execute(
            "SELECT value FROM kv WHERE key = ? LIMIT 1", (key,)
        ).fetchone()
        if item is None:
            return default
        return json.loads(item["value"])

    def delete(self, key: str | KVKey) -> bool:
        key = self._sanitize_key(key)
        with self._con:
            cur = self._con.execute("DELETE FROM kv WHERE key = ?", (key,))
            return cur.rowcount > 0

    def get_user_valid_attempt_id(self, user: int | User, /) -> int | None:
        user_id = user if isinstance(user, int) else user.id

        val = self.get(KVKey.last_phrase_valid_attempt_id_user(user_id))
        if val is self.MISSING:
            return None
        return val

    def set_user_valid_attempt_id(self, user: int | User, /, attempt_id: int) -> None:
        user_id = user if isinstance(user, int) else user.id

        self.set(KVKey.last_phrase_valid_attempt_id_user(user_id), attempt_id)
