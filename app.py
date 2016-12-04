# -*- coding: UTF-8 -*-
from datetime import datetime, timedelta

import jwt
from flask import Flask, abort, send_from_directory
from flask_restful import reqparse, fields, marshal, Api, Resource, inputs
from flask_login import login_required, LoginManager, current_user
from werkzeug.security import check_password_hash
from mongoengine import connect, NotUniqueError

from models import Message, User


EMAIL_REGEX = r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'

app = Flask(__name__)
login_manager = LoginManager(app)
api = Api(app)


@login_manager.user_loader
def load_user(user_id):
    return User.objects(id=user_id).first()


@login_manager.request_loader
def load_user_from_request(request):
    try:
        api_key = request.headers['Authorization']
        token = api_key.replace('JWT ', '', 1)
        payload = jwt.decode(token, 'secret')
        return User.objects(id=payload['id']).first()
    except Exception:
        return None


@app.route('/')
def index():
    return send_from_directory('static/html', 'index.html')


class Registration(Resource):
    def __init__(self):
        self._fields = {
            'name': fields.String,
            'email': fields.String
        }
        self._parser = reqparse.RequestParser()
        self._parser.add_argument('name', required=True)
        self._parser.add_argument('email', type=inputs.regex(EMAIL_REGEX),
                                  required=True)
        self._parser.add_argument('password', required=True)

    def post(self):
        request_data = self._parser.parse_args(strict=True)
        user = User(**request_data)
        try:
            user.set_password(user.password)
            user.save()
        except NotUniqueError:
            return abort(400, 'Not unique user name')
        # TODO add user email validation
        return marshal(user, self._fields), 201


class Login(Resource):
    def __init__(self):
        self._parser = reqparse.RequestParser()
        self._parser.add_argument('login', required=True)
        self._parser.add_argument('password', required=True)

    def post(self):
        request_data = self._parser.parse_args()
        user = User.objects(name=request_data['login']).first()
        if user is None:
            user = User.objects(email=request_data['login']).first()
        if user and check_password_hash(user.password, request_data['password']):
            payload = {
                'exp': datetime.utcnow() + timedelta(days=1),
                'id': str(user.id)
            }
            token = jwt.encode(payload, 'secret').decode('utf-8')
            return {'token': token}
        else:
            abort(400, 'Bad username or password')

# TODO add logout


class Chat(Resource):
    decorators = [login_required]

    def __init__(self):
        self._fields = {
            'user': fields.String,
            'message': fields.String
        }

        self._parser = reqparse.RequestParser()
        self._parser.add_argument('message')

    def get(self):
        return [marshal(message, self._fields) for message in Message.objects]

    def post(self):
        request_data = self._parser.parse_args(strict=True)
        user = User.objects(id=current_user.id).first()
        message = Message(user, request_data['message'])
        message.save()
        return marshal(message, self._fields), 201


# Resources registration
api.add_resource(Registration, '/registration')
api.add_resource(Login, '/login')
api.add_resource(Chat, '/chat')

if __name__ == '__main__':
    connect('chat')
    app.run(debug=True)

# TODO fix login
# TODO add app fabric
# TODO add logging
# TODO research restful status codes
