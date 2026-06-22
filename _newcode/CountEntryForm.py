from flask_wtf import FlaskForm
import wtforms as forms
from wtforms.validators import DataRequired, Disabled

from models import ActualCounts, MaterialList, WhsePartTypes, CountSchedule, choices_for_whseparttypes
from database import Repository, app_db


class CountEntryForm(FlaskForm):
    id = forms.IntegerField()
    CountDate = forms.DateField(validators=[DataRequired()])
    CycCtID = forms.StringField()
    Material = forms.StringField(validators=[DataRequired()])
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

    # handle Material <-> Material_id conversion 
        
    # move to pre-processing before save, or to the view?
    # def save(self, req: str|HttpRequest|User):
    #     dbUsing = user_db(req)
    #     # dbmodel = self.Meta.model
    #     required_fields = ['CountDate', 'Material', 'Counter'] #id handled separately
    #     PriK = self['id'].value()
    #     M = MaterialList.objects.using(dbUsing).get(pk=self.data['MatlPK']) 
    #     if not str(PriK).isnumeric(): PriK = -1
    #     existingrec = dbmodel.objects.using(dbUsing).filter(pk=PriK).exists()
    #     if existingrec: rec = dbmodel.objects.using(dbUsing).get(pk=PriK)
    #     else:   rec = dbmodel()
    #     for fldnm in self.changed_data + required_fields:
    #         if fldnm=='id': continue
    #         if fldnm=='Material':
    #             setattr(rec,fldnm, M)
    #         else:
    #             setattr(rec, fldnm, self.cleaned_data[fldnm])
        
    #     rec.save(using=dbUsing)
    #     return rec


class RelatedMaterialInfo(FlaskForm):
    Description = forms.StringField(validators=[Disabled()])
    PartType = forms.SelectField(choices=[])
    #                             app_db.session.query(WhsePartTypes).order_by(WhsePartTypes.WhsePartType).all())
    TypicalContainerQty = forms.StringField()
    TypicalPalletQty = forms.StringField()
    Notes = forms.StringField()
    
    class Meta(FlaskForm.Meta):
        model = MaterialList

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load choices at runtime (request/app context), not at module import.
        self.PartType.choices = choices_for_whseparttypes()  # type: ignore[assignment]

    # def __init__(self, id, *args, **kwargs) -> None:
    #     super().__init__(*args, **kwargs)
    #     self.id = id
    #     self.fields['PartType'].queryset=WhsePartTypes.objects.all().order_by('WhsePartType').all()
    # def save(self, req:str|HttpRequest|User):
    #     dbUsing = user_db(req)
    #     dbmodel = self.Meta.model
    #     required_fields = [] #id handled separately
    #     PriK = self.id
    #     if not str(PriK).isnumeric(): PriK = -1
    #     existingrec = dbmodel.objects.using(dbUsing).filter(pk=PriK).exists()
    #     if existingrec: rec = dbmodel.objects.using(dbUsing).get(pk=PriK)
    #     else:  raise Exception('Saving Related Material with no PK')  # rec = dbmodel()
    #     for fldnm in self.changed_data + required_fields:
    #         if fldnm=='id': continue
    #         if fldnm=='Material':
    #             # no special processing - Material is a string here, not a ForeignField
    #             setattr(rec, fldnm, self.cleaned_data[fldnm])
    #         else:
    #             setattr(rec, fldnm, self.cleaned_data[fldnm])
        
    #     rec.save(using=dbUsing)
    #     return rec


class RelatedScheduleInfo(FlaskForm):
    CountDate = forms.DateField(validators=[Disabled()])
    Counter = forms.StringField(validators=[Disabled()])
    Priority = forms.StringField(validators=[Disabled()])
    ReasonScheduled = forms.StringField(validators=[Disabled()])
    Notes = forms.StringField(validators=[Disabled()])
    
    class Meta(FlaskForm.Meta):
        model = CountSchedule

    # def __init__(self, id, *args, **kwargs) -> None:
    #     super().__init__(*args, **kwargs)
    #     self.id = id
    # def save(self, req:str|HttpRequest|User):
    #     dbUsing = user_db(req)
    #     dbmodel = self.Meta.model
    #     required_fields = ['CountDate', 'Material'] #id handled separately
    #     PriK = self.id
    #     M = MaterialList.objects.using(dbUsing).get(pk=self.data['MatlPK']) 
    #     if not str(PriK).isnumeric(): PriK = -1
    #     existingrec = dbmodel.objects.using(dbUsing).filter(pk=PriK).exists()
    #     if existingrec: rec = dbmodel.objects.using(dbUsing).get(pk=PriK)
    #     else:  raise Exception('Saving Related Schedule Info with no PK')   # rec = dbmodel()
    #     for fldnm in self.changed_data + required_fields:
    #         if fldnm=='id': continue
    #         if fldnm=='Material':
    #             setattr(rec,fldnm, M)
    #         else:
    #             setattr(rec, fldnm, self.cleaned_data[fldnm])
        
    #     rec.save(using=dbUsing)
    #     return rec

