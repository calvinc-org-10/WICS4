from flask_wtf import FlaskForm
import wtforms as forms
from wtforms.validators import DataRequired, Optional

from models import CountSchedule


class CountScheduleRecordForm(FlaskForm):
    id = forms.IntegerField(validators=[Optional()])
    CountDate = forms.DateField(validators=[DataRequired()])
    # Material = forms.CharField(required=True)
        # Material is handled this way because of the way it's done in the html.
        # later, create a DropdownText widget??
    Material_id = forms.HiddenField()
    Counter = forms.StringField(validators=[Optional()])
    Priority = forms.StringField(validators=[Optional()])
    ReasonScheduled = forms.StringField(validators=[Optional()])
    Requestor = forms.StringField(validators=[Optional()])
    Requestor_userid_id = forms.HiddenField()
    RequestFilled = forms.BooleanField()
    Notes  = forms.StringField()

    class Meta(FlaskForm.Meta):
        model = CountSchedule


