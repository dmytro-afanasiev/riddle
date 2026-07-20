from flask import Flask


def make_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object("riddle.config.Config")

    from riddle.views.health import health_bp

    app.register_blueprint(health_bp)

    from riddle.views.auth import auth_bp

    app.register_blueprint(auth_bp)

    from riddle.views.clue import clue_bp

    app.register_blueprint(clue_bp)

    from riddle.views.finale import finale_bp

    app.register_blueprint(finale_bp)

    from . import db

    db.init_app(app)

    from . import validation

    validation.init_app(app)

    from riddle.models import clue

    clue.init_app(app)

    from riddle.models import user

    user.init_app(app)

    return app
