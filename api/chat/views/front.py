from flask import Blueprint, redirect, render_template, url_for, request, abort

from chat.api import auth
from chat.models import User

bp = Blueprint(__name__, __name__, template_folder='templates')


@bp.route('/')
def index():
    if not auth.current_user:
        return redirect(url_for('chat.views.front.login'))
    else:
        return redirect(url_for('chat.views.front.chat_list'))


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        data = request.values.to_dict()
        token, expires = User.login(
            data['name'],
            data['password'],
        )
        if token is None:
            abort(401, "Wrong credentials")
        response = redirect(url_for('chat.views.front.chat_list'))
        auth.set_auth_cookie(response, token, expires)
        return response
    return render_template('login.html')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        data = request.values.to_dict()
        user = User.register(
            data['name'],
            data['password'],
        )
        if user is None:
            return abort(400)
        return redirect(url_for('chat.views.front.login'))
    return render_template('registration.html')


@bp.route('/chat/<int:pk>/')
@auth.login_required()
def chat(pk):
    return render_template('chat.html', pk=pk)


@bp.route('/list')
@auth.login_required()
def chat_list():
    return render_template('list.html')


@bp.route('/logout', methods=('POST',))
def logout():
    response = redirect(url_for('chat.views.front.login'))
    auth.clear_auth_cookie(response)
    return response
