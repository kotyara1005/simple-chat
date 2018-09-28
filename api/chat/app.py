# -*- coding: UTF-8 -*-
import functools

from flask import Flask

import config
from chat.api import auth, stream
from chat.views import front, message, user
from chat.models import db
from chat.utils import ApiError, handle_error


def create_app():
    app = Flask(__name__, static_folder=config.STATIC_FOLDER)
    app.config.from_object(config)
    app.debug = config.DEBUG
    app.errorhandler(ApiError)(handle_error)
    app.register_blueprint(user.create_blueprint(), url_prefix='/api')
    app.before_request(auth.setup_user)
    app.register_blueprint(message.create_blueprint(), url_prefix='/api')
    app.register_blueprint(front.bp, url_prefix='')
    db.init_app(app)
    stream.streamer.init_app(app)

    app.before_first_request(functools.partial(db.create_all, app=app))

    return app

# TODO add tests
# TODO add logout
# TODO add indexes
