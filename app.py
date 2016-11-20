# -*- coding: UTF-8 -*-
from flask import Flask
from flask_restful import reqparse, fields, marshal, Api, Resource
from flask_login import login_required, LoginManager
from mongoengine import connect

from models import Message, User


app = Flask(__name__)
login_manager = LoginManager(app)
api = Api(app)


@login_manager.user_loader
def load_user(user_id):
    return User.objects(id=user_id)


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
# TODO add user registration
# TODO add logout


class Chat(Resource):
    decorators = [login_required]

    def __init__(self):
        self._fields = {
            'user': fields.String,
            'message': fields.String
        }

        self._parser = reqparse.RequestParser()
        self._parser.add_argument('user')
        self._parser.add_argument('message')

    def get(self):
        return [marshal(message, self._fields) for message in Message.objects]

    def post(self):
        request_data = self._parser.parse_args(strict=True)
        message = Message(request_data['user'], request_data['message'])
        message.save()
        return marshal(message, self._fields), 201

api.add_resource(Chat, '/chat')

if __name__ == '__main__':
    connect('chat')
    app.run()

# TODO add app fabric
# TODO find out how to get objects right
