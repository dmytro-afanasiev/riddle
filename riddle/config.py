import os


class Config:
    TESTING = False
    SECRET_KEY: str = os.getenv("RIDDLE_SECRET_KEY") or "devsecretkey"
    DATABASE_NAME: str = os.getenv("RIDDLE_DATABASE_NAME") or "riddle.db"

    TOKEN_LIFETIME_SECONDS: int = (
        int(os.getenv("RIDDLE_TOKEN_LIFETIME_SECONDS", 60 * 60 * 10)) or 60 * 60 * 10
    )
    CLUE_REQUEST_PERIOD_SECONDS: int = (
        int(os.getenv("RIDDLE_CLUE_REQUEST_PERIOD_SECONDS", 60 * 60 * 24))
        or 60 * 60 * 24
    )
