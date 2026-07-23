"""
Contains some constants and that not bound to application context
"""

import os

TOKEN_LIFETIME_SECONDS: int = (
    int(os.getenv("RIDDLE_TOKEN_LIFETIME_SECONDS", 60 * 60 * 10)) or 60 * 60 * 10
)
CLUE_REQUEST_PERIOD_SECONDS: int = (
    int(os.getenv("RIDDLE_CLUE_REQUEST_PERIOD_SECONDS", 60 * 60 * 24)) or 60 * 60 * 24
)
DATABASE_NAME: str = os.getenv("RIDDLE_DATABASE_NAME") or "riddle.db"
RANDOM_CLUES_FILEPATH = os.getenv("RIDDLE_RANDOM_CLUES_FILEPATH") or "random_clues.json"
INVALID_FINALE_ATTEMPT_MESSAGES_FILEPATH = (
    os.getenv("RIDDLE_INVALID_FINALE_ATTEMPT_MESSAGES_FILEPATH")
    or "invalid_finale_attempt_messages.json"
)
