import uuid, os, re as regex, ast, json, time

from flask import (
    current_app,
    session, flash,
    request, make_response, Response, 
    jsonify, stream_with_context,
    )
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

from wtforms import SubmitField

from calvincTools.utils import (
    checkTemplate_and_render,
    ExcelWorkbook_fileext,
    )

from calvincTools.models import (cParameters, )
from app import app as thisapp
from database import (app_db,)
from models import (
    tmpMaterialListUpdate, SAPPlants_org,
    async_comm
    )
    

####################################################################################
####################################################################################
####################################################################################

class testForm01(FlaskForm):
    testfield1 = StringField('Test Field 1', validators=[DataRequired()])
    testfield2 = StringField('Test Field 2', validators=[DataRequired()])
    submit = SubmitField('Submit')


@login_required
def testformlayout():

    theform = testForm01()

    if request.method == 'POST':
        # check if the mandatory commits have been done and change the status code if so
        if theform.validate_on_submit():
            flash('Form submitted successfully!', 'success')
            # Process form data here (e.g., save to database)
            return make_response(jsonify({'message': 'Form submitted successfully!'}), 200)
        else:
            flash('Form validation failed. Please check your input.', 'danger')
            return make_response(jsonify({'message': 'Form validation failed.'}), 400)
        # endif form.validate_on_submit()
    else:   # req.method != 'POST'
        # (hopefully,) this is the initial phase; all others will be part of a POST request

        cntext = {
            'newRecord_flag': True,
            'form': theform,
            'reqid': -1,
            }
        templt = '_newcode/test01.html'
        return checkTemplate_and_render(templt, **cntext)
    #endif req.method = 'POST'
# testformlayout()

