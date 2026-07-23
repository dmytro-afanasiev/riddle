import hashlib
import hmac
from http import HTTPMethod, HTTPStatus

import msgspec
from flask import Blueprint, g

from riddle.constants import INVALID_FINALE_ATTEMPT_MESSAGES_FILEPATH
from riddle.db import get_db
from riddle.kv import KVKey, KVStore
from riddle.models.attempt import FinaleAttemptRepo
from riddle.utils import RandomStringJsonFileProvider, error_response
from riddle.validation import validate_body
from riddle.views.auth import require_auth

finale_bp = Blueprint("finale", __name__)


g_phrase_hash: str | None = None
g_valid_users: set[int] = set()

g_invalid_finale_attempt_messages_provider = RandomStringJsonFileProvider(
    INVALID_FINALE_ATTEMPT_MESSAGES_FILEPATH
)


def _get_phrase_hash() -> str | None:
    global g_phrase_hash
    if g_phrase_hash is None:
        val = KVStore(get_db()).get(KVKey.LAST_PHRASE_HASH)
        if val is KVStore.MISSING:
            return None
        g_phrase_hash = val
    return g_phrase_hash


class FinaleTry(msgspec.Struct, frozen=True, order=False, eq=False):
    phrase: str


@finale_bp.route("/finale/try", methods=[HTTPMethod.POST])
@require_auth
@validate_body(FinaleTry)
def finale_try(payload: FinaleTry):
    expected = _get_phrase_hash()
    if expected is None:
        return error_response(message="not configured"), HTTPStatus.SERVICE_UNAVAILABLE

    db = get_db()
    attempt = FinaleAttemptRepo(db).create(user=g.user, inp=payload.phrase)

    given = hashlib.sha256(payload.phrase.encode("utf-8")).hexdigest()
    if not hmac.compare_digest(expected, given):
        return error_response(
            message=g_invalid_finale_attempt_messages_provider.get_random(),
        ), HTTPStatus.UNAUTHORIZED

    KVStore(db).set_user_valid_attempt_id(g.user, attempt_id=attempt.id)
    g_valid_users.add(g.user.id)
    return {"msg": "You're goddamn right"}, HTTPStatus.OK


@finale_bp.route("/finale/check", methods=[HTTPMethod.GET])
@require_auth
def finale_check():
    if g.user.id in g_valid_users:
        return "", HTTPStatus.OK
    val = KVStore(get_db()).get_user_valid_attempt_id(g.user)
    if val is None:
        return "", HTTPStatus.UNAUTHORIZED
    g_valid_users.add(g.user.id)
    return "", HTTPStatus.OK
