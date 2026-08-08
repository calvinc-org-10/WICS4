from flask_wtf import FlaskForm
import wtforms as forms
from wtforms.validators import DataRequired, Disabled, Optional

from models import (
    ActualCounts, MaterialList, WhsePartTypes, CountSchedule, MfrPNtoMaterial,
    choices_for_whseparttypes, choices_for_organizations,
    )
from database import Repository, app_db


class CountsSubForm(FlaskForm):    
    id = forms.IntegerField(validators=[Optional()])
    CountDate = forms.DateField()
    Counter = forms.StringField()
    CTD_QTY_Expr = forms.StringField()
    LOCATION = forms.StringField()
    LocationOnly = forms.BooleanField()
    FLAG_PossiblyNotRecieved = forms.BooleanField()
    FLAG_MovementDuringCount = forms.BooleanField()
    Notes = forms.StringField(validators=[Optional()])

    class Meta(FlaskForm.Meta):
        model = ActualCounts

class ScheduleSubForm(FlaskForm):
    id = forms.IntegerField(validators=[Optional()])
    CountDate = forms.DateField()
    Counter = forms.StringField()
    Priority = forms.StringField()
    ReasonScheduled = forms.StringField()
    Notes = forms.StringField(validators=[Optional()])

    class Meta(FlaskForm.Meta):
        model = CountSchedule

class MfrPNSubForm(FlaskForm):
    id = forms.IntegerField(validators=[Optional()])
    MfrPN = forms.StringField()
    Manufacturer = forms.StringField()
    Notes = forms.StringField(validators=[Optional()])

    class Meta(FlaskForm.Meta):
        model = MfrPNtoMaterial

class MaterialForm(FlaskForm):
    # id = forms.IntegerField(validators=[Optional()])
    id = forms.HiddenField()
    org_id = forms.SelectField(choices=[], validators=[DataRequired()])
    Material = forms.StringField(validators=[DataRequired()])
    Description = forms.StringField(validators=[DataRequired()])
    PartType_id = forms.SelectField(choices=[])
    SAPMaterialType = forms.StringField(validators=[Optional()])
    SAPMaterialGroup = forms.StringField(validators=[Optional()])
    Plant = forms.StringField(validators=[Optional()])
    SAPABC = forms.StringField(validators=[Optional()])
    SAPMPN = forms.StringField(validators=[Optional()])
    SAPManuf = forms.StringField(validators=[Optional()])
    Price = forms.DecimalField(validators=[Optional()])
    PriceUnit = forms.IntegerField(validators=[Optional()]) 
    Currency = forms.StringField(validators=[Optional()])
    TypicalContainerQty = forms.StringField(validators=[Optional()]) 
    TypicalPalletQty = forms.StringField(validators=[Optional()])
    Notes  = forms.StringField()

    # Child collections rendered in the Material tabs.
    counts = forms.FieldList(forms.FormField(CountsSubForm), min_entries=0)
    schedule = forms.FieldList(forms.FormField(ScheduleSubForm), min_entries=0)
    MfrPN = forms.FieldList(forms.FormField(MfrPNSubForm), min_entries=0)

    subforms = {
        # Keep mapping for compatibility with existing caller code.
        'counts': counts,
        'schedule': schedule,
        'MfrPN': MfrPN,
    }

    class Meta(FlaskForm.Meta):
        model = MaterialList

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load choices at runtime (request/app context), not at module import.
        self.org_id.choices = choices_for_organizations()       # type: ignore[assignment]
        self.PartType_id.choices = choices_for_whseparttypes()  # type: ignore[assignment]

 
class MaterialCountSummaryLine(forms.Form):
    Material = forms.StringField(validators=[Optional()], render_kw={"disabled": True})
    CountDate = forms.DateField(validators=[Optional()], render_kw={"disabled": True})
    CountQTY_Eval = forms.IntegerField(validators=[Optional()], render_kw={"disabled": True})
    SAPDate = forms.DateField(validators=[Optional()], render_kw={"disabled": True})
    SAPQty = forms.StringField(validators=[Optional()], render_kw={"disabled": True})
    Diff = forms.StringField(validators=[Optional()], render_kw={"disabled": True})
    Accuracy = forms.StringField(validators=[Optional()], render_kw={"disabled": True})

# class MfrPNtoMaterialForm(forms.Form):
#     class Meta:
#         model = MfrPNtoMaterial
#         fields = ['id', 'MfrPN', 'Manufacturer', 'Material', 'Notes',]
#         # fields = '__all__'

