# -*- coding: UTF-8 -*-
DEBUG = True

SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'

AUTH_COOKIE_NAME = 'auth'
SECRET_KEY = 'secret'

STATIC_FOLDER = None

STREAM_EXCHANGE_NAME = 'MessageStream'
STREAM_RABBIT_URL = 'amqp://guest:guest@rabbit:5672/'

try:
    from local_config import *
except ImportError:
    pass
