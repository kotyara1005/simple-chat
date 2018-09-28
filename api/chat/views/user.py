from flask import (
    Blueprint,
)
from marshmallow import fields
from werkzeug.exceptions import MethodNotAllowed, Forbidden

from chat.api.auth import current_user
from chat.models import User, db
from chat.utils import validate, RESTView, register_view


class UserView(RESTView):
    model = User

    def get_query(self) -> db.Query:
        return self.model.query

    def create(self, **kwargs):
        raise MethodNotAllowed()

    @validate(
        id=fields.Integer(),
        name=fields.String(),
    )
    def update(self, pk, **kwargs):
        if current_user.id != pk:
            raise Forbidden()
        return super().update(pk, **kwargs)

    def destroy(self, pk):
        if current_user.id != pk:
            raise Forbidden()
        return super().destroy(pk)


def create_blueprint():
    blueprint = Blueprint(__name__, __name__)
    register_view(UserView, blueprint, 'user_api', '/user/')
    return blueprint