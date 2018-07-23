from flask_wtf import FlaskForm
from wtforms import FileField, SelectField
from wtforms.validators import DataRequired


class FaceUploadForm(FlaskForm):
    file = FileField('Face', validators=[DataRequired()])


class FaceEditForm(FlaskForm):
    person = SelectField('Person', coerce=int)
