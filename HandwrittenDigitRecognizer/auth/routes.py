from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import auth
from HandwrittenDigitRecognizer.models.user import User
from HandwrittenDigitRecognizer.app import db
from .forms.login_form import LoginForm
from .forms.register_form import RegisterForm
from HandwrittenDigitRecognizer.email import send_confirmation_email, confirm_token

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if 'first_name' in session and 'last_name' in session:
        flash("Вече сте влезли в системата.", "info")
        return redirect(url_for('main.home'))

    form = LoginForm()
    if request.method == 'GET':
        return render_template("login.html", form=form)
    elif request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(Email=email).first()
        if user and check_password_hash(user.Password, form.password.data):
            if not user.Confirmed:
                flash('Моля, потвърдете своя имейл адрес преди да влезете.', 'warning')
                return redirect(url_for('auth.login'))

            login_user(user)
            session['first_name'] = user.FirstName
            session['last_name'] = user.LastName

            # flash('Успешно влизане!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Грешен имейл или парола', 'danger')
    return render_template('login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if 'first_name' in session and 'last_name' in session:
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
        role = request.form.get('role', 'User')

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
            Role=role,
            Confirmed=False
        )

        try:
            db.session.add(new_user)
            db.session.commit()

            send_confirmation_email(new_user.Email)

            flash("Регистрацията беше успешна! Провери имейла си за потвърждение.", "info")
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            print(f"Грешка при регистрация: {e}")
            flash("Възникна грешка при регистрацията. Опитайте отново.", "danger")

    return render_template("register.html", form=form)

@auth.route('/confirm/<token>')
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash('Линкът е невалиден или е изтекъл.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(Email=email).first_or_404()
    if user.Confirmed:
        flash('Имейлът вече е потвърден.', 'info')
    else:
        user.Confirmed = True
        db.session.commit()
        flash('Имейлът беше успешно потвърден!', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/logout')
def logout():
    logout_user()
    session.clear()
    flash('Успешно излязохте от системата.', 'success')
    return redirect(url_for('main.index'))