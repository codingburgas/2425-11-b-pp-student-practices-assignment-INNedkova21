from flask import current_app, render_template, url_for
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from HandwrittenDigitRecognizer.extensions import mail

def generate_token(email):
    # Generates a secure token for a given email using the application's secret key.
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirm')

def confirm_token(token, expiration=3600):
    # Validates and decodes the token, returning the email if the token is valid and not expired.
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        return serializer.loads(token, salt='email-confirm', max_age=expiration)
    except:
        return False

def send_confirmation_email(user_email):
    # Sends a confirmation email to the specified email address with an activation link.
    token = generate_token(user_email)
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    html = render_template('confirm.html', confirm_url=confirm_url)

    msg = Message('Потвърди имейла си', recipients=[user_email], html=html)
    mail.send(msg)