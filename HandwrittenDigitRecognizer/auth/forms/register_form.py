from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class RegisterForm(FlaskForm):
    first_name = StringField('Име:', validators=[DataRequired()])
    last_name = StringField('Фамилия:', validators=[DataRequired()])
    email = StringField('Имейл:', validators=[DataRequired(), Email()])
    password = PasswordField('Парола:', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField()
    submit = SubmitField('Регистрация')
