# -*- coding: UTF-8 -*-
from mongoengine import Document, fields, CASCADE
from flask_login import UserMixin


class User(Document, UserMixin):
    name = fields.StringField(required=True, unique=True)
    password = fields.StringField(required=True)

    def __str__(self):
        return self.name


class Message(Document):
    user = fields.ReferenceField(User, dbref=True, reverse_delete_rule=CASCADE)
    message = fields.StringField(required=True)
