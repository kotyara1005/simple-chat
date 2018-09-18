import functools

import marshmallow
from flask import request, jsonify
from flask.views import View
from werkzeug.exceptions import MethodNotAllowed, NotFound

from chat.models import db


class ApiError(Exception):
    def __init__(self, data, status):
        self.data = data
        self.status = status


def handle_error(error):
    response = jsonify(error.data)
    response.status_code = error.status
    return response


def validate(**fields):
    schema = type('Schema', (marshmallow.Schema,), fields)()

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if request.is_json:
                data = request.json
            else:
                data = request.form.to_dict()
            result = schema.load(data)
            if result.errors:
                raise ApiError(result.errors, 400)
            kwargs.update(result.data)
            return func(*args, **kwargs)
        return wrapper
    return decorator


class CommitOnSuccess:
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is None:
            db.session.commit()
        else:
            db.session.rollback()
        return False

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper


class RESTView(View):
    model: db.Model = None

    def get_query(self) -> db.Query:
        raise NotImplementedError()

    @classmethod
    def get_query_for_user(cls):
        raise NotImplementedError()

    @classmethod
    def get_or_404(cls, pk):
        entry = cls.get_query_for_user().filter_by(id=pk).first()
        if entry is None:
            raise NotFound()
        return entry

    @CommitOnSuccess()
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
            [
                entry.to_dict()
                for entry in self.get_query_for_user().all()
            ]
        )

    def create(self, **kwargs):
        with CommitOnSuccess():
            entry = self.model(**kwargs)
            db.session.add(entry)
        return jsonify(entry.to_dict())

    def retrieve(self, pk):
        return jsonify(self.get_or_404(pk).to_dict())

    def update(self, pk, **kwargs):
        entry = self.get_or_404(pk)
        for key, value in kwargs:
            setattr(entry, key, value)
        return jsonify(entry.to_dict())

    def destroy(self, pk):
        entry = self.get_or_404(pk)
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
