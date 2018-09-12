import contextlib
from datetime import datetime, timedelta

import jwt
from flask import Blueprint, abort, make_response, jsonify
from flask_login import LoginManager, current_user
from marshmallow import fields
from werkzeug.exceptions import MethodNotAllowed, Forbidden
from werkzeug.security import check_password_hash

import config
from chat.models import User, db
from chat.utils import validate, RESTView, register_view


def load_user(user_id):
    return User.objects(id=user_id).first()


def load_user_from_request(request):
    with contextlib.suppress():
        api_key = request.headers['Authorization']
        token = api_key.replace('JWT ', '', 1)
        payload = jwt.decode(token, config.SECRET_KEY)
        return User.query.get_or_404(payload['id'])


def create_manager(app):
    login_manager = LoginManager(app)
    login_manager.user_loader(load_user)
    login_manager.request_loader(load_user_from_request)
    return login_manager


@validate(
    name=fields.String(required=True),
    password=fields.String(required=True),
)
def register(name, password):
    user = User(name=name)
    try:
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
    except:
        abort(400, 'Error')
    return '{}', 201


@validate(
    name=fields.String(required=True),
    password=fields.String(required=True),
)
def login(name, password):
    user = User.query.filter_by(name=name).first()
    if not (user and check_password_hash(user.password, password)):
        abort(400, 'Bad username or password')

    expires = datetime.utcnow() + timedelta(days=1)
    token = user.create_token(expires)

    response = make_response()
    response.set_cookie(
        config.AUTH_COOKIE_NAME,
        token,
        expires=expires.timestamp(),
    )
    return jsonify({'token': token})


def logout():
    response = make_response()
    response.set_cookie(config.AUTH_COOKIE_NAME, '', expires=0)
    return response


class UserView(RESTView):
    model = User

    def get_query(self) -> db.Query:
        return self.model.query

    def create(self, **kwargs):
        raise MethodNotAllowed()

    @validate(
        id=fields.Integer(),
        name=fields.String(),
    )
    def update(self, pk, **kwargs):
        if current_user.id != pk:
            raise Forbidden()
        return super().update(pk, **kwargs)

    def destroy(self, pk):
        if current_user.id != pk:
            raise Forbidden()
        return super().destroy(pk)


def create_blueprint():
    blueprint = Blueprint(__name__, __name__)
    blueprint.add_url_rule('/register', 'register', register, methods=('POST',))
    blueprint.add_url_rule('/login', 'login', login, methods=('POST',))
    blueprint.add_url_rule('/logout', 'logout', logout, methods=('POST',))
    register_view(UserView, blueprint, 'user_api', '/user/')
    return blueprint
