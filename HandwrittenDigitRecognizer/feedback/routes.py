from flask import render_template, request, redirect, url_for, flash, abort, jsonify
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from ..models.feedback import Feedback
from ..models.user import User
from ..models.prediction import Prediction
from ..extensions import db
from . import feedback
import os
from datetime import datetime, timezone, timedelta

BULGARIA_TZ = timezone(timedelta(hours=2))

@feedback.route('/feedback', methods=['GET', 'POST'])
@login_required
def give_feedback():
    if current_user.Role != 'User':
        abort(403)

    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')

        if not rating:
            flash('Моля, изберете оценка.', 'error')
            return redirect(url_for('feedback.feedback'))

        feedback_entry = Feedback(UserID=current_user.ID, Rating=int(rating), Comment=comment)
        db.session.add(feedback_entry)
        db.session.commit()
        flash('Благодарим за обратната връзка!', 'success')
        return redirect(url_for('feedback.give_feedback'))

    return render_template('feedback.html')


@feedback.route('/admin/feedback', endpoint='admin_feedback')
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


@feedback.route('/delete_feedback/<int:feedback_id>', methods=['DELETE'])
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