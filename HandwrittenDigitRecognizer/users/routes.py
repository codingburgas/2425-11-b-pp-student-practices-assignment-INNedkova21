from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from ..models.feedback import Feedback
from ..models.user import User
from ..models.prediction import Prediction
from ..extensions import db
from . import users
import os
from datetime import datetime

upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')


@users.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    error = None
    success = None

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_password or not new_password or not confirm_password:
            error = "Всички полета са задължителни."
        elif not check_password_hash(current_user.Password, current_password):
            error = "Текущата парола е грешна."
        elif new_password != confirm_password:
            error = "Новата парола не съвпада с потвърждението."
        elif len(new_password) < 6:
            error = "Паролата трябва да е поне 6 символа."
        else:
            current_user.Password = generate_password_hash(new_password)
            try:
                db.session.commit()
                success = "Паролата е сменена успешно."
            except:
                db.session.rollback()
                error = "Възникна грешка при смяната на паролата."

    return render_template('profile.html', error=error, success=success)


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


@users.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.Role != 'Administrator':
        abort(403)

    user_to_delete = User.query.get_or_404(user_id)

    if user_to_delete.ID == current_user.ID:
        flash('Не можеш да изтриеш собствения си акаунт!', 'warning')
        return redirect(url_for('users.admin_users'))

    try:
        Prediction.query.filter_by(UserID=user_to_delete.ID).delete()
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('Потребителят беше успешно изтрит.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Грешка при изтриването: ' + str(e), 'danger')

    return redirect(url_for('users.admin_users'))


@users.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if current_user.Role != 'User':
        abort(403)

    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')

        if not rating:
            flash('Моля, изберете оценка.', 'error')
            return redirect(url_for('users.feedback'))

        feedback = Feedback(UserID=current_user.ID, Rating=int(rating), Comment=comment)
        db.session.add(feedback)
        db.session.commit()
        flash('Благодарим за обратната връзка!', 'success')
        return redirect(url_for('users.feedback'))

    return render_template('feedback.html')

@users.route('/admin/feedback', endpoint='admin_feedback')
@login_required
def admin_feedback():
    if current_user.Role != 'Administrator':
        abort(403)

    all_feedback = Feedback.query.order_by(Feedback.CreatedAt.desc()).all()
    feedback_list = []
    for feedback in all_feedback:
        user = feedback.user
        full_name = f"{user.FirstName} {user.LastName}" if user else 'неизвестен'
        
        # Форматиране на датата в български формат
        formatted_date = feedback.CreatedAt.strftime('%d.%m.%Y %H:%M')
        
        feedback_list.append({
            'ID': feedback.ID,
            'UserID': feedback.UserID,
            'Username': full_name,
            'Email': user.Email if user else '',
            'Rating': feedback.Rating,
            'Comment': feedback.Comment,
            'CreatedAt': formatted_date
        })

    return render_template('admin_feedback.html', feedbacks=feedback_list)


@users.route('/delete_feedback/<int:feedback_id>', methods=['DELETE'])
@login_required
def delete_feedback(feedback_id):
    print(f"DELETE FEEDBACK CALLED: {feedback_id}")  # Debug print
    if current_user.Role != 'Administrator':
        print("NOT ADMIN")  # Debug print
        return jsonify({'success': False, 'error': 'Нямате права за тази операция'})

    feedback = Feedback.query.get_or_404(feedback_id)
    print(f"FEEDBACK FOUND: {feedback.ID}")  # Debug print
    
    try:
        db.session.delete(feedback)
        db.session.commit()
        print("FEEDBACK DELETED SUCCESSFULLY")  # Debug print
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"ERROR DELETING FEEDBACK: {e}")  # Debug print
        return jsonify({'success': False, 'error': str(e)})