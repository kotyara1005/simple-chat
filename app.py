# -*- coding: UTF-8 -*-
from flask import Flask, abort
from flask_restful import reqparse, fields, marshal, Api, Resource, inputs
from flask_login import login_required, LoginManager, current_user
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
    # TODO improve authorization algorithm
    api_key = request.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Basic ', '', 1)
        user = User.objects(id=api_key).first()
        if user:
            return user
    return None


@app.route('/')
def index():
    return 'Index'


class Registration(Resource):
    def __init__(self):
        self._fields = {
            'name': fields.String,
            'email': fields.String
        }
        self._parser = reqparse.RequestParser()
        self._parser.add_argument('name')
        self._parser.add_argument('email', type=inputs.regex(EMAIL_REGEX))
        self._parser.add_argument('password')

    def post(self):
        request_data = self._parser.parse_args(strict=True)
        # TODO add data validation
        user = User(**request_data)
        try:
            user.save()
        except NotUniqueError:
            return abort(400, 'Not unique user name')
        # TODO add user email validation
        return marshal(user, self._fields), 201

# TODO add login
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
api.add_resource(Chat, '/chat')

if __name__ == '__main__':
    connect('chat')
    app.run()

# TODO add app fabric
# TODO find out how to get objects right
# TODO add logging
# TODO research restful status codes
