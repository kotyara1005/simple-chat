# -*- coding: UTF-8 -*-
from mongoengine import Document, fields


class Message(Document):
    user = fields.StringField(required=True)
    message = fields.StringField(required=True)
