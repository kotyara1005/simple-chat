# -*- coding: UTF-8 -*-
import datetime

import jwt
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    password = db.Column(db.String())
    email = db.Column(db.String())
    conversations = db.relationship("Participant", back_populates="user")

    @classmethod
    def login(cls, name, password):
        user = cls.query.filter_by(name=name).first()
        if not (user and check_password_hash(user.password, password)):
            return None, None

        expires = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        return user.create_token(expires), expires

    @classmethod
    def register(cls, name, password):
        try:
            user = User(name=name)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
        except:
            return None
        return user

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
        return jwt.encode(payload, current_app.config['SECRET_KEY']).decode('utf-8')

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
