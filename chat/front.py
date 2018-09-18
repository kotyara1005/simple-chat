from chat import auth

from flask import Blueprint, redirect, render_template, url_for, request

bp = Blueprint(__name__, __name__, template_folder='templates')


@bp.route('/')
def index():
    if not auth.current_user:
        return redirect(url_for('chat.front.login'))
    else:
        return redirect(url_for('chat.front.chat_list'))


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        return auth.login()
        return redirect(url_for('chat.front.chat'))
    return render_template('login.html')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        auth.register()
        return redirect(url_for('chat.front.login'))
    return render_template('registration.html')


@bp.route('/chat/<int:pk>/')
@auth.login_required()
def chat(pk):
    return render_template('chat.html', pk=pk)


@bp.route('/list')
@auth.login_required()
def chat_list():
    return render_template('list.html')

# TODO disable redirects
