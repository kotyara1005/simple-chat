# -*- coding: UTF-8 -*-
from flask import Flask, request, abort
from flask_restful import reqparse, inputs, fields, marshal, Api, Resource
from mongoengine import connect

from models import Message


app = Flask(__name__)
api = Api(app)


@app.route('/')
def index():
    return 'Index'


class Chat(Resource):
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
