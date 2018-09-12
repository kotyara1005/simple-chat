from flask import Blueprint
from flask_login import current_user
from marshmallow import fields
from werkzeug.exceptions import MethodNotAllowed, Forbidden

from chat.models import db, Message, Conversation, Participant
from chat.utils import (
    RESTView,
    validate,
    user_id_to_kwargs,
    commit_on_success,
    register_view,
)


class ConversationView(RESTView):
    model = Conversation

    @classmethod
    def get_query(cls) -> db.Query:
        # TODO check rights
        return cls.model.query

    @validate()
    @user_id_to_kwargs
    def create(self, **kwargs):
        return super().create(**kwargs)

    def update(self, pk, **kwargs):
        raise MethodNotAllowed()

    @classmethod
    @commit_on_success
    def add_participant(cls, conversation_id, user_id):
        conversation = cls.get_query().get(conversation_id)
        if conversation.user_id != current_user.id:
            raise Forbidden()
        participant = Participant(
            user_id=user_id,
            conversation_id=conversation_id,
        )
        db.session.add(participant)

    @classmethod
    @commit_on_success
    def delete_participant(cls, conversation_id, user_id):
        conversation = cls.get_query().get(conversation_id)
        if conversation.user_id != current_user.id:
            raise Forbidden()
        participant = Participant.query.filter_by(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        db.session.delete(participant)

    @classmethod
    @validate(
        text=fields.String()
    )
    @commit_on_success
    def send_message(cls, conversation_id, text):
        conversation = cls.get_query().get(conversation_id)
        if conversation.user_id != current_user.id:
            raise Forbidden()
        message = Message(
            conversation_id=conversation_id,
            user_id=current_user.id,
            text=text,
        )
        db.session.add(message)


def create_blueprint():
    blueprint = Blueprint(__name__, __name__)
    register_view(ConversationView, blueprint, 'conversation_api', '/conversation/')
    blueprint.add_url_rule('/participant', 'add_participant', ConversationView.add_participant, methods=('POST',))
    blueprint.add_url_rule('/participant', 'delete_participant', ConversationView.delete_participant, methods=('DELETE',))
    blueprint.add_url_rule('/message', 'message', ConversationView.send_message, methods=('POST',))
    return blueprint
