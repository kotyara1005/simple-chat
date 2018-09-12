from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user

bp = Blueprint(__name__, __name__, template_folder='templates')


@bp.route('/')
def index():
    if current_user.is_anonymous:
        return redirect(url_for('chat.front.login'))
    else:
        return redirect(url_for('chat.front.chat'))


@bp.route('/login')
def login():
    return render_template('login.html')


@bp.route('/register')
def register():
    return render_template('registration.html')


@bp.route('/chat')
def chat():
    return render_template('chat.html')

