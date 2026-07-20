from typing import Annotated
from flask import Blueprint, jsonify, request, g
from functools import wraps
from datetime import datetime, timezone
from riddle.models.user import UserRepo, UserStatus
from riddle.db import get_db
from riddle.utils import error_response
from http import HTTPMethod, HTTPStatus
from riddle.validation import validate_body
from pydantic import BaseModel, StringConstraints

auth_bp = Blueprint("auth", __name__)

Username = Annotated[
    str, StringConstraints(pattern=r"^[A-Za-z0-9]+$", min_length=4, max_length=32)
]
Password = Annotated[str, StringConstraints(min_length=8)]


class RegisterPost(BaseModel):
    username: Username
    password: Password


class LoginPost(BaseModel):
    username: Username
    password: Password


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return error_response("auth token required"), HTTPStatus.UNAUTHORIZED
        token = header.removeprefix("Bearer ").strip()
        if not token:
            return error_response("auth token required"), HTTPStatus.UNAUTHORIZED
        if len(token) != 43:
            return error_response("invalid or expired token"), HTTPStatus.UNAUTHORIZED

        repo = UserRepo(get_db())
        user = repo.get_by_token(token)
        if user is None:
            return error_response("invalid or expired token"), HTTPStatus.UNAUTHORIZED
        g.user = user
        g.token = token
        return f(*args, **kwargs)

    return wrapper


@auth_bp.route("/auth/register", methods=[HTTPMethod.POST])
@validate_body(RegisterPost)
def register(payload: RegisterPost):
    repo = UserRepo(get_db())
    if repo.exists(payload.username):
        return error_response("user already exists"), HTTPStatus.CONFLICT
    repo.create(payload.username, payload.password)
    return "", HTTPStatus.CREATED


@auth_bp.route("/auth/login", methods=[HTTPMethod.POST])
@validate_body(LoginPost)
def login(payload: LoginPost):
    repo = UserRepo(get_db())
    user = repo.get(payload.username)
    if user is None:
        return error_response("invalid credentials"), HTTPStatus.UNAUTHORIZED
    if user.status is not UserStatus.APPROVED:
        return error_response("invalid credentials"), HTTPStatus.UNAUTHORIZED
    if not repo.check_password(user, payload.password):
        return error_response("invalid credentials"), HTTPStatus.UNAUTHORIZED

    token, expires_at = repo.create_token(
        user_id=user.id,
    )

    return jsonify(
        token=token,
        expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
    )


@auth_bp.route("/auth/logout", methods=[HTTPMethod.POST])
@require_auth
def logout():
    UserRepo(get_db()).revoke_token(g.token)
    return ""


@auth_bp.route("/auth/whoami", methods=[HTTPMethod.GET])
@require_auth
def whoami():
    return jsonify(username=g.user.username, created_at=g.user.created_at.isoformat())
