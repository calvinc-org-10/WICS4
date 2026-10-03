from models import CountSchedule


import wtforms as forms
from flask_wtf import FlaskForm
from wtforms.validators import Disabled


class RelatedScheduleInfo(FlaskForm):
    id = forms.IntegerField(validators=[Disabled()])
    CountDate = forms.DateField(validators=[Disabled()])
    Counter = forms.StringField(validators=[Disabled()])
    Priority = forms.StringField(validators=[Disabled()])
    ReasonScheduled = forms.StringField(validators=[Disabled()])
    Notes = forms.StringField(validators=[Disabled()])

    class Meta(FlaskForm.Meta):
        model = CountSchedule