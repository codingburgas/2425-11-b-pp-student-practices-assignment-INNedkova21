from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from ..models.feedback import Feedback
from ..models.user import User
from ..models.prediction import Prediction
from ..extensions import db
from . import users
import os
from datetime import datetime, timezone, timedelta

upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')

# Българска часова зона (UTC+2)
BULGARIA_TZ = timezone(timedelta(hours=2))


@users.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_password or not new_password or not confirm_password:
            flash("Всички полета са задължителни.", "error")
        elif not check_password_hash(current_user.Password, current_password):
            flash("Текущата парола е грешна.", "error")
        elif new_password != confirm_password:
            flash("Новата парола не съвпада с потвърждението.", "error")
        elif len(new_password) < 6:
            flash("Паролата трябва да е поне 6 символа.", "error")
        else:
            current_user.Password = generate_password_hash(new_password)
            try:
                db.session.commit()
                flash("Паролата е сменена успешно.", "success")
            except:
                db.session.rollback()
                flash("Възникна грешка при смяната на паролата.", "error")

    return render_template('profile.html')


@users.route('/admin/users')
@login_required
def admin_users():
    if current_user.Role != 'Administrator':
        abort(403)
    users_list = User.query.order_by(User.CreatedAt.desc()).all()
    return render_template('admin_users.html', users=users_list)


@users.route('/admin/user/<int:user_id>')
@login_required
def admin_user_details(user_id):
    if current_user.Role != 'Administrator':
        abort(403)

    user = User.query.get_or_404(user_id)
    predictions = Prediction.query.filter_by(UserID=user.ID).order_by(Prediction.CreatedAt.desc()).all()
    for p in predictions:
        p.filename = os.path.basename(p.ImagePath)
    return render_template('admin_user_details.html', user=user, predictions=predictions)


@users.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.Role != 'Administrator':
        abort(403)

    user = User.query.get_or_404(user_id)

    Feedback.query.filter_by(UserID=user.ID).delete()

    Prediction.query.filter_by(UserID=user.ID).delete()

    try:
        db.session.delete(user)
        db.session.commit()
        flash('Потребителят беше изтрит успешно.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Грешка при изтриване: {e}', 'danger')

    return redirect(url_for('users.admin_users'))