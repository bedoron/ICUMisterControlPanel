from flask_wtf import Form
from wtforms import FileField
from wtforms.validators import DataRequired


class FaceUploadForm(Form):
    file = FileField('Face', validators=[DataRequired()])
