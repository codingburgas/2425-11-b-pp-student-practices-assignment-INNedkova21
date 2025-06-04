from flask import render_template, redirect, url_for, flash, request, Blueprint, session
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from . import auth
from HandwrittenDigitRecognizer.models.user import User
from HandwrittenDigitRecognizer.app import db
from .forms.login_form import LoginForm
from .forms.register_form import RegisterForm


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if 'first_name' in session and 'last_name' in session and 'role' in session:
        flash("Вече сте влезли в системата.", "info")
        return redirect(url_for('main.home'))

    form = LoginForm()
    if request.method == 'GET':
        return render_template("login.html", form=form)
    elif request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(Email=email).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)

            session['first_name'] = user.first_name
            session['last_name'] = user.last_name

            flash('Успешно влизане!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Грешен имейл или парола', 'danger')
    else:
        print(form.errors)
    return render_template('login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if 'first_name' in session and 'last_name' in session and 'role' in session:
        flash("Вече сте влезли в системата.", "info")
        return redirect(url_for('main.home'))

    form = RegisterForm()
    if request.method == 'GET':
        return render_template("register.html", form=form)
    elif request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Паролите не съвпадат. Опитайте отново.", "danger")
            return render_template("register.html", form=form)

        if User.query.filter_by(Email=email).first():
            flash("Имейлът вече е регистриран.", "danger")
            return render_template("register.html", form=form)

        hashed_password = generate_password_hash(password)

        new_user = User(
            FirstName=first_name,
            LastName=last_name,
            Email=email,
            Password=hashed_password,
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Регистрацията беше успешна! Можете да влезете.", "success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            print(f"Error during registration: {e}")
            flash("Възникна грешка при регистрацията. Опитайте отново.", "danger")

    return render_template("register.html", form=form)

@auth.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash('Успешно излязохте от системата.', 'success')
    return redirect(url_for('main.dashboard'))