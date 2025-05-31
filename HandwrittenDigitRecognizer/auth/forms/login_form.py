from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class LoginForm(FlaskForm):
    email = StringField('Имейл', validators=[DataRequired(), Email()])
    password = PasswordField('Парола', validators=[DataRequired()])
    submit = SubmitField('Вход')