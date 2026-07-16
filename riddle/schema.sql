DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS tokens;
DROP TABLE IF EXISTS clue_requests;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    status INTEGER NOT NULL DEFAULT 0 CHECK (status IN (0, 1, 2)),
    created_at TIMESTAMP NOT NULL DEFAULT (strftime('%s', 'now'))
);
CREATE TABLE tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT (strftime('%s', 'now')),
    expires_at TIMESTAMP NOT NULL,
    revoked INTEGER NOT NULL DEFAULT 0 CHECK (revoked IN (0, 1)),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX idx_tokens_user_id ON tokens(user_id);

CREATE TABLE clue_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT (strftime('%s', 'now')),
    page INTEGER NOT NULL,
    description TEXT NOT NULL DEFAULT "",
    level INTEGER NOT NULL DEFAULT 0 CHECK (level BETWEEN 0 AND 9),
    status INTEGER NOT NULL DEFAULT 0 CHECK (status IN (0, 1, 2)),
    answer TEXT,
    closed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
);
CREATE INDEX idx_clue_requests_user_id_created_at_desc ON clue_requests(user_id, created_at DESC);
