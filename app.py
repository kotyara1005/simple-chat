# -*- coding: UTF-8 -*-
from collections import namedtuple

from flask import Flask, request, abort
from flask.views import MethodView
from flask.json import jsonify

Record = namedtuple('Record', 'user message')
app = Flask(__name__)


@app.route('/')
def index():
    return 'Index'


class Chat(MethodView):
    data = []

    def get(self):
        if len(self.data) < 10:
            return jsonify(self.data)
        else:
            return jsonify(self.data[-10:])

    def post(self):
        if request.is_json:
            request_data = request.get_json()
            self.data.append(Record(request_data['user'],
                                    request_data['message']))
            return 'OK'
        else:
            abort(400)
app.add_url_rule('/chat', view_func=Chat.as_view('chat'))

if __name__ == '__main__':
    app.run()
