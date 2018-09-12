from chat import auth

from flask import Blueprint, redirect, render_template, url_for, request
from flask_login import current_user

bp = Blueprint(__name__, __name__, template_folder='templates')


@bp.route('/')
def index():
    if current_user.is_anonymous:
        return redirect(url_for('chat.front.login'))
    else:
        return redirect(url_for('chat.front.chat'))


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        auth.login()
        return redirect(url_for('chat.front.chat'))
    return render_template('login.html')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        auth.register()
        return redirect(url_for('chat.front.login'))
    return render_template('registration.html')


@bp.route('/chat')
def chat():
    return render_template('chat.html')

