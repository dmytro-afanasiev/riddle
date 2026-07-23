from functools import wraps
from http import HTTPStatus

import msgspec
from flask import Flask, jsonify, request


def validate_body(model: type[msgspec.Struct]):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            raw = request.get_data() or b"{}"
            payload = msgspec.json.decode(raw, type=model, strict=False)
            return fn(*args, payload=payload, **kwargs)

        return wrapper

    return decorator


def validate_query(model: type[msgspec.Struct]):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            data = request.args or {}
            payload = msgspec.convert(dict(data), type=model, strict=False)
            return fn(*args, query=payload, **kwargs)

        return wrapper

    return decorator


def init_app(app: Flask):
    @app.errorhandler(msgspec.ValidationError)
    def handle_validation_error(err: msgspec.ValidationError):
        return jsonify(msg=str(err), details={}), HTTPStatus.BAD_REQUEST

    @app.errorhandler(msgspec.DecodeError)
    def handle_decode_error(err: msgspec.DecodeError):
        return jsonify(msg="malformed json body", details={}), HTTPStatus.BAD_REQUEST
