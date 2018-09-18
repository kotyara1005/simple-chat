# -*- coding: UTF-8 -*-
import datetime

import jwt
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    password = db.Column(db.String())
    email = db.Column(db.String())
    conversations = db.relationship("Participant", back_populates="user")

    def __str__(self):
        return self.name

    def set_password(self, password):
        self.password = generate_password_hash(
            password,
            method='pbkdf2:sha256',
            salt_length=64,
        )

    def create_token(self, expires):
        payload = {
            'exp': expires,
            'id': str(self.id)
        }
        return jwt.encode(payload, 'secret').decode('utf-8')

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
        )


class Conversation(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey(User.id), nullable=False)
    name = db.Column(db.String())
    participants = db.relationship("Participant", back_populates="conversation")
    messages = db.relationship("Message")

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            participants=[participant.user.to_dict() for participant in self.participants],
            messages=[message.to_dict() for message in self.messages],
        )


class Participant(db.Model):
    user_id = db.Column(db.Integer(), db.ForeignKey(User.id), primary_key=True)
    conversation_id = db.Column(db.Integer(), db.ForeignKey(Conversation.id), primary_key=True)
    user = db.relationship(User, back_populates="conversations")
    conversation = db.relationship(Conversation, back_populates="participants")


class Message(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    conversation_id = db.Column(db.Integer(), db.ForeignKey(Conversation.id), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey(User.id))
    text = db.Column(db.String(), nullable=False)
    create_date = db.Column(db.DateTime(), default=lambda: datetime.datetime.utcnow().replace(microsecond=0))

    def to_dict(self):
        return dict(
            id=self.id,
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            text=self.text,
        )
