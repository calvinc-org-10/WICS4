from flask_wtf import FlaskForm
import wtforms as forms
from wtforms.validators import DataRequired, Optional

from models import ActualCounts, WhsePartTypes


class CountEntryForm(FlaskForm):
    id = forms.IntegerField(validators=[Optional()])
    CountDate = forms.DateField(validators=[DataRequired()])
    CycCtID = forms.StringField()
    # Material = forms.StringField(validators=[DataRequired()])
        # Material is handled this way because of the way it's done in the html.
        # later, create a DropdownText widget??
    Material_id = forms.HiddenField()
    Counter = forms.StringField(validators=[DataRequired()])
    LocationOnly = forms.BooleanField()
    LOCATION = forms.StringField(validators=[DataRequired()])
    CTD_QTY_Expr = forms.StringField()
    FLAG_PossiblyNotRecieved = forms.BooleanField()
    FLAG_MovementDuringCount = forms.BooleanField()
    PKGID_Desc = forms.StringField()
    TAGQTY = forms.StringField()
    Notes  = forms.StringField()

    class Meta(FlaskForm.Meta):
        model = ActualCounts

