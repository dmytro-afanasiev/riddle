import hashlib
import hmac
import random
from http import HTTPMethod, HTTPStatus

from flask import Blueprint, g
from pydantic import BaseModel

from riddle.db import get_db
from riddle.kv import KVKey, KVStore
from riddle.models.attempt import FinaleAttemptRepo
from riddle.utils import error_response
from riddle.validation import validate_body
from riddle.views.auth import require_auth

finale_bp = Blueprint("finale", __name__)

_USER_MESSAGES = (
    "not this time, dude",
    "did you just guess randomly? because feels like",
    "bro, you can do better",
    "maybe it's not yours",
    "stop it, stop it, i cannot take wrong answers any more",
    "Yeap, you did it. Just kidding...",
    "You are stubborn as a bull",
    "not yours...",
    "drink some green tea, relax, you have time",
    "aah, just tear up that notebook, fuck it",
)

_AI_MESSAGES = (
    "bad try — bad day, yo",
    "not your day, pal",
    "you really don't know it, do you",
    "nah, that ain't it",
    "swing and a miss",
    "the phrase remains unbroken",
    "close... just kidding, not even close",
    "impressive confidence, wrong answer",
    "the universe says no",
    "try again, brave soul",
    "bold guess, wrong guess",
    "that's a negatory, ghost rider",
    "you're technically not correct — the worst kind of not correct",
    "your guess has been filed under 'nope'",
    "plot twist: that's not it",
    "legends say the right answer is still out there",
    "have you tried turning your brain off and on again",
    "the answer machine rejected your application",
    "error 401: phrase unauthorized",
    "somewhere, a wrong answer buzzer just went off",
    "your guess wandered into the wrong neighborhood",
    "that guess just got voted off the island",
    "nice guess, wrong dimension though",
    "the magic 8-ball says: absolutely not",
    "your guess called — it wants its dignity back",
    "so close yet so astronomically far",
)

_FAIL_MESSAGES = _USER_MESSAGES + _AI_MESSAGES

_phrase_hash: str | None = None
_valid_users: set[int] = set()


def _get_phrase_hash() -> str | None:
    global _phrase_hash
    if _phrase_hash is None:
        val = KVStore(get_db()).get(KVKey.LAST_PHRASE_HASH)
        if val is KVStore.MISSING:
            return None
        _phrase_hash = val
    return _phrase_hash


class FinaleTry(BaseModel):
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
            message=random.choice(_FAIL_MESSAGES)
        ), HTTPStatus.UNAUTHORIZED

    KVStore(db).set_user_valid_attempt_id(g.user, attempt_id=attempt.id)
    _valid_users.add(g.user.id)
    return {"msg": "You're goddamn right"}, HTTPStatus.OK


@finale_bp.route("/finale/check", methods=[HTTPMethod.GET])
@require_auth
def finale_check():
    if g.user.id in _valid_users:
        return "", HTTPStatus.OK
    val = KVStore(get_db()).get_user_valid_attempt_id(g.user)
    if val is None:
        return "", HTTPStatus.UNAUTHORIZED
    _valid_users.add(g.user.id)
    return "", HTTPStatus.OK
