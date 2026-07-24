import time
from datetime import datetime, timezone
from http import HTTPMethod, HTTPStatus
from typing import Annotated, Literal

import msgspec
from flask import Blueprint, g, jsonify

from riddle.constants import (
    CLUE_REQUEST_PERIOD_SECONDS,
    RANDOM_CLUES_FILEPATH,
)
from riddle.db import get_db
from riddle.models.clue import ClueRequestRepo, ClueStatus
from riddle.utils import RandomStringJsonFileProvider, error_response
from riddle.validation import validate_body, validate_query
from riddle.views.auth import require_auth
from riddle.kv import KVKey, KVStore

clue_bp = Blueprint("clue", __name__)

g_random_clues_provider = RandomStringJsonFileProvider(RANDOM_CLUES_FILEPATH)


class CluesPost(msgspec.Struct, frozen=True, eq=False, order=False):
    page: Annotated[int, msgspec.Meta(ge=0, le=203)]
    level: Annotated[int, msgspec.Meta(ge=0, le=9)]
    description: str | None = None


class CluesGet(msgspec.Struct, frozen=True, eq=False, order=False):
    limit: Annotated[int, msgspec.Meta(ge=1)] = 16
    offset: Annotated[int, msgspec.Meta(ge=0)] = 0
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
        and (available_at := latest + CLUE_REQUEST_PERIOD_SECONDS) > now
    ):
        to_wait = available_at - now
        return error_response(
            "clue request is currently not available",
            {
                "seconds_to_wait": to_wait,
                "available_at": datetime.fromtimestamp(available_at, tz=timezone.utc),
            },
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

    gen = repo.query(
        user_id=g.user.id,
        ascending=query.ascending,
        limit=query.limit,
        offset=query.offset,
        status=status,
    )
    return list(gen), HTTPStatus.OK


@clue_bp.route("/clues/random", methods=[HTTPMethod.GET])
@require_auth
def get_random_clue():

    kv = KVStore(get_db())
    kv.increment(KVKey.random_clue_requests_user(g.user.id))

    resp = jsonify(msg=g_random_clues_provider.get_random())
    resp.headers["Cache-Control"] = "no-store"
    return resp
