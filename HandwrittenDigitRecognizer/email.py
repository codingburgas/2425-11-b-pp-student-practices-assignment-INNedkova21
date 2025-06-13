from flask import current_app, render_template, url_for
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from HandwrittenDigitRecognizer.extensions import mail

def generate_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm')

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        return serializer.loads(token, salt='email-confirm', max_age=expiration)
    except:
        return False

def send_confirmation_email(user_email):
    token = generate_token(user_email)
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    html = render_template('confirm.html', confirm_url=confirm_url)

    msg = Message('Потвърди имейла си', recipients=[user_email], html=html)
    mail.send(msg)