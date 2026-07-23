import random
import typing as t

import msgspec.json
from flask import Response, jsonify
from flask.json.provider import JSONProvider


def error_response(message: str, details: dict | None = None) -> Response:
    return jsonify(msg=message, details=details or {})


class MSGSpecJsonProvider(JSONProvider):
    mimetype = "application/json"

    def __init__(self, app) -> None:
        super().__init__(app)

        self._encoder = msgspec.json.Encoder()
        self._decoder = msgspec.json.Decoder()

    def dumps(self, obj: t.Any, **kwargs: t.Any) -> str:
        return self._encoder.encode(obj)  # type: ignore

    def loads(self, s: str | bytes, **kwargs: t.Any) -> t.Any:
        return self._decoder.decode(s)


class RandomStringJsonFileProvider:
    __slots__ = "_filepath", "_clues"

    def __init__(self, filepath: str):
        self._filepath = filepath
        self._clues: list[str] | None = None

    @property
    def clues(self) -> list[str]:
        if self._clues is not None:
            return self._clues
        with open(self._filepath, "r") as f:
            self._clues = msgspec.json.decode(f.read(), type=list[str])
        return self._clues

    def get_random(self) -> str:
        return random.choice(self.clues)
