import functools

import marshmallow
from flask import request, jsonify
from flask.views import View
from flask_login import current_user
from werkzeug.exceptions import MethodNotAllowed

from chat.models import db


class ApiError(Exception):
    def __init__(self, data, status):
        self.data = data
        self.status = status


def handle_error(error):
    response = jsonify(error.data)
    response.status_code = error.status
    return response


def validate(source='json', **fields):
    schema = type('Schema', (marshmallow.Schema,), fields)()

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = schema.load(getattr(request, source))
            if result.errors:
                raise ApiError(result.errors, 400)
            kwargs.update(result.data)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def user_id_to_kwargs(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        kwargs['user_id'] = current_user.id
        return func(*args, **kwargs)
    return wrapper


def commit_on_success(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            db.session.commit()
            return result
        except Exception as error:
            db.session.rollback()
            raise error
    return wrapper


class RESTView(View):
    model: db.Model = None

    def get_query(self) -> db.Query:
        raise NotImplementedError()

    @commit_on_success
    def dispatch_request(self, pk=None):
        method = request.method.upper()
        if method == 'GET':
            if pk is None:
                return self.list()
            else:
                return self.retrieve(pk)
        elif method == 'POST':
            return self.create()
        elif method == 'PUT':
            return self.update(pk)
        elif method == 'DELETE':
            return self.destroy(pk)
        else:
            raise MethodNotAllowed()

    def list(self):
        # TODO add limit offset
        return jsonify(
            [entry.to_dict() for entry in self.get_query().all()]
        )

    def create(self, **kwargs):
        entry = self.model(**kwargs)
        db.session.add(entry)
        return jsonify(entry.to_dict())

    def retrieve(self, pk):
        return jsonify(self.get_query().get_or_404(pk).to_dict())

    def update(self, pk, **kwargs):
        entry = self.get_query().get_or_404(pk)
        for key, value in kwargs:
            setattr(entry, key, value)
        return jsonify(entry.to_dict())

    def destroy(self, pk):
        entry = self.get_query().get_or_404(pk)
        db.session.delete(entry)
        return jsonify({})


def register_view(view, app, endpoint, url, pk_type='int'):
    view_func = view.as_view(endpoint)
    app.add_url_rule(
        url,
        defaults={'pk': None},
        view_func=view_func,
        methods=('GET',),
    )
    app.add_url_rule(url, view_func=view_func, methods=('POST',))
    app.add_url_rule(
        '%s<%s:%s>' % (url, pk_type, 'pk'),
        view_func=view_func,
        methods=('GET', 'PUT', 'DELETE'),
    )