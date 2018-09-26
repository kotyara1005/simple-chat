import pika
from flask import current_app


class Stream:
    def __init__(self, app=None):
        self._app = app
        self.connection = None
        self.channel = None
        if app is not None:
            self.init_app(app)
        self.connect()
        self.channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type='fanout',
        )

    @property
    def app(self):
        return self._app or current_app

    @property
    def exchange_name(self):
        return self.app.config.get('STREAM_EXCHANGE_NAME')

    @staticmethod
    def init_app(app):
        app.config.setdefault('STREAM_EXCHANGE_NAME', '')
        app.config.setdefault('STREAM_RABBIT_URL', None)

    def connect(self):
        self.connection = pika.BlockingConnection(
            pika.URLParameters(self.app.config['STREAM_RABBIT_URL'])
        )
        self.channel = self.connection.channel()

    def send(self, body, headers):
        return self.channel.basic_publish(
            exchange=self.exchange_name,
            routing_key='anonymous.info',
            body=body,
            properties=pika.BasicProperties(
                headers=headers
            ),
        )


streamer = Stream()
