import sqlite3
from flask import current_app, g, Flask
from riddle.constants import DATABASE_NAME
import click


def get_db() -> sqlite3.Connection:
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_NAME, autocommit=False)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
    return db


def close_db(exception=None) -> None:
    db = getattr(g, "_database", None)
    if db is not None:
        delattr(g, "_database")
        db.close()


def init_db():
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))
    db.commit()


@click.command("init-db", help="Creates necessary tables")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
def init_db_command(yes):
    if not yes:
        click.confirm("This will drop and recreate all tables. Continue?", abort=True)
    init_db()
    click.echo("Tables were created")


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
