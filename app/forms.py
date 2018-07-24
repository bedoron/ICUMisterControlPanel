from flask_wtf import FlaskForm
from wtforms import FileField, SelectField, TextField, StringField, HiddenField, SelectMultipleField
from wtforms.validators import DataRequired


class FaceUploadForm(FlaskForm):
    file = FileField('Face', validators=[DataRequired()])


class FaceEditForm(FlaskForm):
    person = SelectField('Person', coerce=int)


class PersonCreateForm(FlaskForm):
    name = StringField('Person name', validators=[DataRequired()])
    id = HiddenField('object_id')
