from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user
from . import auth
from HandwrittenDigitRecognizer.models.user import User
from HandwrittenDigitRecognizer.app import db
from .forms.login_form import LoginForm
from .forms.register_form import RegisterForm


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(Email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Невалиден имейл или парола')
    return render_template('login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(Email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Регистрацията е успешна!')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.dashboard'))
