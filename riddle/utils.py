from flask import jsonify, Response


def error_response(
    message: str, details: list[dict] | tuple[dict, ...] | dict = ()
) -> Response:
    if isinstance(details, dict):
        details = (details,)
    return jsonify(msg=message, details=details)
