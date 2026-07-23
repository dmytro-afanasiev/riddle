import os


class Config:
    TESTING = False
    SECRET_KEY: str = os.getenv("RIDDLE_SECRET_KEY") or "devsecretkey"
