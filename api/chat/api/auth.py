import contextlib
import functools

import jwt
from flask import (
    request,
    g,
    redirect,
    current_app,
)
from werkzeug.local import LocalProxy

from chat.models import User


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


def clear_auth_cookie(response):
    response.set_cookie(current_app.config['AUTH_COOKIE_NAME'], '', expires=0)
