from models import MaterialList, choices_for_whseparttypes


import wtforms as forms
from flask_wtf import FlaskForm
from wtforms.validators import Optional


class RelatedMaterialInfo(FlaskForm):
    id = forms.HiddenField(validators=[Optional()])
    Material = forms.HiddenField(validators=[Optional()])
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