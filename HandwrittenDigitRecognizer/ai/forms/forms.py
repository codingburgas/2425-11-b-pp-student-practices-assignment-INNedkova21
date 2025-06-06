from flask_wtf import FlaskForm
from wtforms import SubmitField
from flask_wtf.file import FileField, FileRequired, FileAllowed

class UploadForm(FlaskForm):
    image = FileField('Изображение', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png', 'jpeg'], 'Само изображения!')
    ])
    submit = SubmitField('Разпознай')
