from flask import render_template, flash, redirect, url_for, request
from web_app import app
import web_app
from config import Config
from web_app.forms import LoginForm, RegisterForm, ConfirmationForm
from flask_login import current_user, login_user, logout_user, login_required
from flask_mail import Message

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.urls import url_parse

from web_app.models import *

from itsdangerous import URLSafeTimedSerializer



@app.route('/')
@app.route('/index')
@login_required
def index():
    user = {'username': current_user.username}
    return render_template('index.html', user=user, title='Home')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None:
            flash('User does not exist')
            return redirect(url_for('login'))
        if not user.check_password(form.password.data):
            flash('Password is incorrect')
            return redirect(url_for('login'))
        if not user.is_active:
            flash('Confirm your email')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@login_required
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, password_hash=generate_password_hash(form.password.data), is_active=False)
        db.session.add(user)
        db.session.commit()
        serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
        dumped = serializer.dumps([form.username.data])
        msg = Message("Confirmation Letter",
                       sender="emailconf@bk.ru",
                       recipients=[form.email.data])
        msg.body = "Please confirm your email address and visit http://127.0.0.1:5000/confirm/" + dumped
        web_app.mail.send(msg)
        flash('Check your email')
        return redirect('/login')
    return render_template('register.html', title='Sign up', form=form)
    
@app.route('/confirm/<code>', methods=['GET', 'POST'])
def confirm(code):
    serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
    data = serializer.loads(
        code
    )
    form = ConfirmationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=data[0]).first()
        user.is_active = True
        db.session.commit()
        flash('User confirmed')
        return redirect(url_for('login'))
    return render_template('confirm.html', title='Confirm', form=form)
