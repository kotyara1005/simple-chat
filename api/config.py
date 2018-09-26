# -*- coding: UTF-8 -*-
DEBUG = True

SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'

SECRET_KEY = 'secret'

STATIC_FOLDER = None
STREAM_EXCHANGE_NAME = ''
STREAM_RABBIT_URL = ''

try:
    from local_config import *
except ImportError:
    pass
