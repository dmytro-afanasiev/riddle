import sys
import hashlib
from riddle.db import get_db
from riddle.app import make_app
from riddle.kv import KVKey, KVStore


def main():
    app = make_app()
    with app.app_context():
        kv = KVStore(get_db())
        kv.set(
            KVKey.LAST_PHRASE_HASH,
            hashlib.sha256(sys.argv[1].encode("utf-8")).hexdigest(),
        )


if __name__ == "__main__":
    main()
