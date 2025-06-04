from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from . import main


@main.route('/')
def index():
    return render_template('index.html')

@main.route('/home')
def home():
    return render_template('home.html')

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename.endswith('.png'):
            # обработка на изображението тук
            flash("Файлът е приет!", "success")
            return redirect(url_for('main.upload'))
        else:
            flash("Моля, качете валиден .png файл.", "danger")
    return render_template("upload.html")


@main.route('/draw', methods=['GET', 'POST'])
def draw():
    if request.method == 'POST':
        digit = request.form.get('digit')
        if digit and digit.isdigit() and 0 <= int(digit) <= 9:
            # обработка на въведената цифра тук
            flash(f"Цифрата {digit} е приета!", "success")
            return redirect(url_for('main.draw'))
        else:
            flash("Моля, въведете валидна цифра (0-9).", "danger")
    return render_template("draw.html")