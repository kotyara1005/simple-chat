# -*- coding: UTF-8 -*-
DEBUG = True

DB_NAME = 'chat'

SECRET_KEY = 'secret'

STATIC_FOLDER = None

try:
    from chat_app.config.local_settings import *
except ImportError:
    pass
