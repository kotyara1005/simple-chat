from flask import Blueprint, jsonify, request
from marshmallow import fields
from werkzeug.exceptions import MethodNotAllowed, Forbidden

from chat.stream import streamer
from chat.auth import current_user, user_id_to_kwargs, login_required
from chat.models import db, Message, Conversation, Participant
from chat.utils import (
    RESTView,
    validate,
    CommitOnSuccess,
    register_view,
)


class ConversationView(RESTView):
    model = Conversation

    @classmethod
    def get_query(cls) -> db.Query:
        return cls.model.query

    @classmethod
    def get_query_for_user(cls):
        return cls.get_query().filter(
            Conversation.id.in_(db.session.query(Participant.conversation_id).filter_by(user_id=current_user.id))
        )

    @validate()
    @login_required()
    @user_id_to_kwargs
    def create(self, user_id, **kwargs):
        with CommitOnSuccess():
            conversation = self.model(user_id=user_id, name='test', **kwargs)
            db.session.add(conversation)
            db.session.flush()

            db.session.add(
                Participant(
                    user_id=user_id,
                    conversation_id=conversation.id,
                )
            )
        return jsonify(conversation.to_dict())

    def update(self, pk, **kwargs):
        raise MethodNotAllowed()

    @classmethod
    @login_required()
    def add_participant(cls, conversation_id, user_id):
        conversation = cls.get_query().get(conversation_id)
        if conversation.user_id != current_user.id:
            raise Forbidden()

        with CommitOnSuccess():
            participant = Participant(
                user_id=user_id,
                conversation_id=conversation_id,
            )
            db.session.add(participant)
        return jsonify(participant)

    @classmethod
    @login_required()
    def delete_participant(cls, conversation_id, user_id):
        conversation = cls.get_query().get(conversation_id)
        if conversation.user_id != current_user.id:
            raise Forbidden()
        with CommitOnSuccess():
            participant = Participant.query.filter_by(
                conversation_id=conversation_id,
                user_id=user_id,
            )
            db.session.delete(participant)
        return jsonify(participant.to_dict())

    @classmethod
    @validate(
        text=fields.String()
    )
    @login_required()
    def send_message(cls, conversation_id, text):
        conversation = cls.get_query().get(conversation_id)
        if current_user.id not in (participant.user_id for participant in conversation.participants):
            raise Forbidden()

        with CommitOnSuccess():
            message = Message(
                conversation_id=conversation_id,
                user_id=current_user.id,
                text=text,
            )
            db.session.add(message)
        response = jsonify(message.to_dict())
        streamer.send(response.get_data(), {'groupName': conversation_id})
        return response

    @classmethod
    @login_required()
    def get_messages(cls, conversation_id):
        conversation = cls.get_or_404(conversation_id)

        messages = Message.query.filter(
            Message.conversation_id == conversation.id,
        )
        if request.if_modified_since:
            messages = messages.filter(
                Message.create_date > request.if_modified_since,
            )
        messages = messages.all()
        response = jsonify([message.to_dict() for message in messages])

        if messages:
            response.last_modified = messages[-1].create_date
        return response


def create_blueprint():
    blueprint = Blueprint(__name__, __name__)
    register_view(ConversationView, blueprint, 'conversation_api', '/conversation/')
    blueprint.add_url_rule('/conversation/<int:conversation_id>/participant', 'add_participant', ConversationView.add_participant, methods=('POST',))
    blueprint.add_url_rule('/conversation/<int:conversation_id>/participant', 'delete_participant', ConversationView.delete_participant, methods=('DELETE',))
    blueprint.add_url_rule('/conversation/<int:conversation_id>/message', 'send_message', ConversationView.send_message, methods=('POST',))
    blueprint.add_url_rule('/conversation/<int:conversation_id>/message', 'get_message', ConversationView.get_messages, methods=('GET',))
    return blueprint
