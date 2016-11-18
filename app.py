# -*- coding: UTF-8 -*-
from flask import Flask, request, abort
from flask_restful import reqparse, fields, marshal, Api, Resource
from mongoengine import connect

from models import Message


app = Flask(__name__)
api = Api(app)


@app.route('/')
def index():
    return 'Index'


class Chat(Resource):
    _fields = {
        'user': fields.String,
        'message': fields.String
    }

    def get(self):
        return [marshal(message, self._fields) for message in Message.objects]

    def post(self):
        if request.is_json:
            request_data = request.get_json()
            message = Message(request_data['user'], request_data['message'])
            message.save()
            return marshal(message, self._fields), 201
        else:
            abort(400)

api.add_resource(Chat, '/chat')

if __name__ == '__main__':
    connect('chat')
    app.run()
