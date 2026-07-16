from datetime import datetime, timezone
import time
from riddle.db import get_db
from riddle.views.auth import require_auth
from riddle.utils import error_response
from http import HTTPMethod, HTTPStatus
from riddle.validation import validate_body
from pydantic import BaseModel, Field
from flask import Blueprint, g, current_app
from riddle.models.clue import ClueRequestRepo


clue_bp = Blueprint("clue", __name__)


class CluePost(BaseModel):
    page: int = Field(ge=0, le=203)
    description: str | None = Field(None)
    level: int = Field(ge=0, le=9)


@clue_bp.route("/clues", methods=[HTTPMethod.POST])
@require_auth
@validate_body(CluePost)
def request_clue(payload: CluePost):
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
