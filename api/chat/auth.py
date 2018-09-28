import contextlib
import functools

import jwt
from flask import (
    Blueprint,
    abort,
    make_response,
    jsonify,
    request,
    g,
    redirect,
    current_app,
)
from marshmallow import fields
from werkzeug.exceptions import MethodNotAllowed, Forbidden
from werkzeug.local import LocalProxy

from chat.models import User, db
from chat.utils import validate, RESTView, register_view


def _get_user():
    return getattr(g, 'user')


current_user = LocalProxy(_get_user)


def login_required(redirect_to=None):
    # TODO fix redirects
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user:
                if redirect_to is None:
                    return '', 401
                return redirect(redirect_to)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def user_id_to_kwargs(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        kwargs['user_id'] = current_user.id
        return func(*args, **kwargs)
    return wrapper


def setup_user():
    g.user = None
    with contextlib.suppress(Exception):
        api_key = request.headers.get('Authorization')
        if api_key is None:
            api_key = request.cookies.get(
                current_app.config['AUTH_COOKIE_NAME'],
                '',
            )
        token = api_key.replace('JWT ', '', 1)
        payload = jwt.decode(token, current_app.config['SECRET_KEY'])
        g.user = User.query.filter_by(id=payload['id']).first()


def set_auth_cookie(response, value, expires):
    response.set_cookie(
        current_app.config['AUTH_COOKIE_NAME'],
        value,
        expires=expires.timestamp(),
    )


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
    token, expires = User.login(name, password)
    if token is None:
        abort(401, "Wrong credentials")
    response = jsonify({'token': token})
    set_auth_cookie(response, token, expires)
    return response


def logout():
    response = make_response()
    response.set_cookie(current_app.config['AUTH_COOKIE_NAME'], '', expires=0)
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
