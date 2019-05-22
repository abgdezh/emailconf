import json

from flask import render_template, flash, redirect, url_for, request, session
from flask_login import current_user, login_user, logout_user, login_required


from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.urls import url_parse

from itsdangerous import URLSafeTimedSerializer

import pika

from web_app import app
import web_app
from web_app.models import *
from web_app.forms import LoginForm, RegisterForm, ConfirmationForm
from config import Config

@app.route('/')
@app.route('/index')
@login_required
def index():
    print('Index')
    session['username'] = current_user.username
    user = {'username': current_user.username}
    return render_template('index.html', user=user, title='Home')


@app.route('/login', methods=['GET', 'POST'])
def login():
    print('Login')
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
    print('Logout')
    logout_user()
    return redirect(url_for('login'))
    
    
def produce(email, link):
    credentials = pika.credentials.PlainCredentials(username='smausygr', password='j8gprHGwQWNY-sAyDrbMgTSj8hLu77eJ')
    conn_params = pika.ConnectionParameters(host='macaw.rmq.cloudamqp.com', virtual_host='smausygr', credentials=credentials)
    connection = pika.BlockingConnection(conn_params)
    channel = connection.channel()
    channel.basic_publish(exchange='', routing_key='first-queue', body=json.dumps((email, link)))
    channel.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    print('Register')
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data, password_hash=generate_password_hash(form.password.data), is_active=False)
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            flash('This user already exists')
            return redirect('/register')
        serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
        link = serializer.dumps([form.username.data])
        email = form.email.data
        produce(link, email)
        flash('Check your email (' + email + ')')
        return redirect('/login')
    return render_template('register.html', title='Sign up', form=form)
    
@app.route('/confirm/<code>', methods=['GET', 'POST'])
def confirm(code):
    print('Confirm')
    try:
        serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
        data = serializer.loads(
            code
        )
    except Exception as e:
        print(e)
        return redirect(url_for('login'))
    form = ConfirmationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=data[0]).first()
        user.is_active = True
        db.session.commit()
        flash('User confirmed')
        return redirect(url_for('login'))
    return render_template('confirm.html', title='Confirm', form=form)
    
@app.route('/forget')
@login_required
def forget():
    print('Forget')
    flash('This user was forgotten')
    logout_user()
    user = User.query.filter_by(username=session['username']).delete()
    db.session.commit()
    return redirect(url_for('register'))
