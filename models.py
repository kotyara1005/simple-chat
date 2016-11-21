# -*- coding: UTF-8 -*-
from werkzeug.security import generate_password_hash
from mongoengine import Document, fields, CASCADE
from flask_login import UserMixin


class User(Document, UserMixin):
    name = fields.StringField(required=True, unique=True)
    password = fields.StringField(required=True)
    email = fields.StringField(required=True, unique=True)

    def __str__(self):
        return self.name

    def set_password(self, password):
        self.password = generate_password_hash(password,
                                               method='pbkdf2:sha512',
                                               salt_length=64)


class Message(Document):
    user = fields.ReferenceField(User, dbref=True, reverse_delete_rule=CASCADE)
    message = fields.StringField(required=True)
