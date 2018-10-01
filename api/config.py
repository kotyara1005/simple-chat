# -*- coding: UTF-8 -*-
DEBUG = True

SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://user:password@chat_postgres:5432/chat'

AUTH_COOKIE_NAME = 'auth'
AUTH_SECRET_KEY = 'secret'

STATIC_FOLDER = None

STREAM_EXCHANGE_NAME = 'MessageStream'
STREAM_RABBIT_URL = 'amqp://guest:guest@rabbit:5672/'

try:
    from local_config import *
except ImportError:
    pass
