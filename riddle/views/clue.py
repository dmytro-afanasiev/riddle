import time
from datetime import datetime, timezone
from http import HTTPMethod, HTTPStatus
from typing import Literal

from flask import Blueprint, current_app, g
from pydantic import BaseModel, Field

from riddle.db import get_db
from riddle.models.clue import ClueRequestRepo, ClueStatus
from riddle.utils import error_response
from riddle.validation import validate_body, validate_query
from riddle.views.auth import require_auth

clue_bp = Blueprint("clue", __name__)


class CluesPost(BaseModel):
    page: int = Field(ge=0, le=203)
    description: str | None = Field(None)
    level: int = Field(ge=0, le=9)


class CluesGet(BaseModel):
    limit: int = Field(16, ge=1)
    offset: int = Field(0, ge=0)
    ascending: bool = False
    status: Literal["PENDING", "ANSWERED", "REJECTED"] | None = None


@clue_bp.route("/clues", methods=[HTTPMethod.POST])
@require_auth
@validate_body(CluesPost)
def request_clue(payload: CluesPost):
    repo = ClueRequestRepo(get_db())
    latest = repo.get_latest_timestamp(g.user.id)
    now = int(time.time())
    if (
        latest is not None
        and (available_at := latest + current_app.config["CLUE_REQUEST_PERIOD_SECONDS"])
        > now
    ):
        to_wait = available_at - now
        return error_response(
            f"clue request will be available at {datetime.fromtimestamp(available_at, tz=timezone.utc).isoformat()}",
            {"seconds_to_wait": to_wait},
        ), HTTPStatus.TOO_MANY_REQUESTS
    repo.create(
        user=g.user,
        page=payload.page,
        description=payload.description or "",
        level=payload.level,
    )
    return "", HTTPStatus.CREATED


@clue_bp.route("/clues", methods=[HTTPMethod.GET])
@require_auth
@validate_query(CluesGet)
def get_clues(query: CluesGet):
    repo = ClueRequestRepo(get_db())

    if query.status is not None:
        status = ClueStatus[query.status]
    else:
        status = None

    return [
        item.dto()
        for item in repo.query(
            user_id=g.user.id,
            ascending=query.ascending,
            limit=query.limit,
            offset=query.offset,
            status=status,
        )
    ], HTTPStatus.OK
