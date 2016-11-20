# -*- coding: UTF-8 -*-
from mongoengine import Document, fields
from flask_login import UserMixin


class Message(Document):
    user = fields.StringField(required=True)
    message = fields.StringField(required=True)


class User(Document, UserMixin):
    name = fields.StringField(required=True)
    password = fields.StringField(required=True)
