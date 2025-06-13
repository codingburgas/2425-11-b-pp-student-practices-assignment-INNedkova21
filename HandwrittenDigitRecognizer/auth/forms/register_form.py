from flask_wtf import FlaskForm
from wtforms.fields.choices import RadioField
from wtforms.fields.simple import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, DataRequired


class RegisterForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Парола', validators=[DataRequired()])
    confirm_password = PasswordField('Потвърдете паролата', validators=[DataRequired(), EqualTo('password')])
    role = RadioField('Роля', choices=[('User', 'Потребител'), ('Admin', 'Администратор')], default='User', validators=[DataRequired()])
    submit = SubmitField('Регистрация')