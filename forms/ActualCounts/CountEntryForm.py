from flask_wtf import FlaskForm
import wtforms as forms
from wtforms.validators import DataRequired, Disabled, Optional

from models import ActualCounts, MaterialList, WhsePartTypes, CountSchedule, choices_for_whseparttypes
from database import Repository, app_db


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


class RelatedMaterialInfo(FlaskForm):
    id = forms.HiddenField(validators=[Optional()])
    Description = forms.StringField(validators=[Optional()], render_kw={"disabled": True})
    # PartType_id = forms.HiddenField()
    PartType_id = forms.SelectField(choices=[])
    #                             app_db.session.query(WhsePartTypes).order_by(WhsePartTypes.WhsePartType).all())
    TypicalContainerQty = forms.StringField()
    TypicalPalletQty = forms.StringField()
    Notes = forms.StringField()
    
    class Meta(FlaskForm.Meta):
        model = MaterialList

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load choices at runtime (request/app context), not at module import.
        self.PartType_id.choices = choices_for_whseparttypes()  # type: ignore[assignment]


class RelatedScheduleInfo(FlaskForm):
    id = forms.IntegerField(validators=[Disabled()])
    CountDate = forms.DateField(validators=[Disabled()])
    Counter = forms.StringField(validators=[Disabled()])
    Priority = forms.StringField(validators=[Disabled()])
    ReasonScheduled = forms.StringField(validators=[Disabled()])
    Notes = forms.StringField(validators=[Disabled()])
    
    class Meta(FlaskForm.Meta):
        model = CountSchedule

