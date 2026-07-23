from flask import jsonify, Response
import msgspec.json
import typing as t
from flask.json.provider import JSONProvider


def error_response(
    message: str, details: list[dict] | tuple[dict, ...] | dict = ()
) -> Response:
    if isinstance(details, dict):
        details = (details,)
    return jsonify(msg=message, details=details)


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
