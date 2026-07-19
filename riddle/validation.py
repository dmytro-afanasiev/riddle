from pydantic import BaseModel, ValidationError
from http import HTTPStatus
from flask import request, Flask, jsonify
from functools import wraps


def validate_body(model: type[BaseModel]):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True) or {}
            payload = model.model_validate(data)
            return fn(*args, payload=payload, **kwargs)

        return wrapper

    return decorator


def validate_query(model: type[BaseModel]):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            data = request.args or {}
            payload = model.model_validate(data)
            return fn(*args, query=payload, **kwargs)

        return wrapper

    return decorator


def init_app(app: Flask):
    @app.errorhandler(ValidationError)
    def handle_validation_error(err: ValidationError):
        return jsonify(
            msg="Invalid json body came", details=err.errors(include_url=False, include_input=False)
        ), HTTPStatus.BAD_REQUEST
