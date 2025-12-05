from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class RecordForm(FlaskForm):
    title = StringField(
        'Title',
        validators=[DataRequired(), Length(min=1, max=140)]
    )
    content = TextAreaField(
        'Content',
        validators=[Length(max=2000)]
    )
    submit = SubmitField('Save Record')