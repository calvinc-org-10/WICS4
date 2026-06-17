import uuid, os, re as regex, ast, json, time

from flask import (
    current_app,
    session, 
    request, make_response, Response, 
    jsonify, stream_with_context,
    )
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

from sqlalchemy import text
from sqlalchemy.sql import select

from openpyxl import load_workbook
from wtforms import SubmitField

from async_tasks import huey

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


    client_phase = request.form.get('phase', None)
    reqid = request.cookies.get('reqid', None)  # where's thee reqid kept?  # eventually, delete the use of cookies for this and just pass the reqid back and forth in the request body or something; using cookies was just a quick way to get it working without having to change the frontend code much, but it's not ideal since it relies on the client to keep track of the reqid correctly and send it back with each request, which could lead to issues if the client doesn't do that correctly.  Passing the reqid back and forth in the request body would be more reliable and easier to manage, but would require changes to the frontend code to include the reqid in each request.

    if request.method == 'POST':
        # check if the mandatory commits have been done and change the status code if so
        if reqid is not None:
            mandatory_commit_key = f'MatlX{reqid}'
            mandatory_commit_list = ['03A', '03D']
            if async_comm.async_comm_exists(mandatory_commit_key):
                mandatory_commits_recorded = async_comm.get_async_comm_state(mandatory_commit_key).statecode # type: ignore
                if all((c in str(mandatory_commits_recorded)) for c in mandatory_commit_list):
                    proc_MatlListSAPSprsheet_99_FinalProc(reqid)
                    async_comm.delete_async_comm(mandatory_commit_key)

        if client_phase=='init-upl':
            # start Huey consumer (or at least make sure it's running) and save the pid in a cookie so we can kill it later in the cleanup proc.  When we can start Huey programmatically, this is where we start it and get the pid.
            # reqid = subprocess.Popen(
                # ['python', f'huey_consumer.py', 'app.huey -w 4']
            # ).pid
            # retinfo.set_cookie('reqid',str(reqid))

            reqid = uuid.uuid4()
            while async_comm.async_comm_exists(reqid):
                reqid = uuid.uuid4()

            UpdateExistFldList = request.form.getlist('UpIfCh')
            proc_MatlListSAPSprsheet_00InitUMLasync_comm(reqid, UpdateExistFldList)

            if request.form.get('use-local-copy', False) == 'use-local-copy':
                UMLSSName = request.files.get('SAPFile').filename # type: ignore
            else:
                UMLSSName = proc_MatlListSAPSprsheet_00CopyUMLSpreadsheet(reqid)
            #endif use local copy
            proc_MatlListSAPSprsheet_01ReadSpreadsheet(reqid, UMLSSName)

            acomm = async_comm.get_async_comm_state(reqid)    # something's very wrong if this doesn't exist
            retinfo = make_response(jsonify(acomm))
            # retinfo.set_cookie('reqid',str(reqid))
            return retinfo
        elif client_phase=='waiting':
            acomm = async_comm.get_async_comm_state(reqid)    # something's very wrong if this doesn't exist
            retinfo = make_response(jsonify(acomm))
            return retinfo
        elif client_phase=='wantresults':
            stmt = select(tmpMaterialListUpdate).where(tmpMaterialListUpdate.recStatus.startswith('err'))
            ImpErrList = app_db.session.execute(stmt).mappings().all()
            stmt = select(tmpMaterialListUpdate).where(tmpMaterialListUpdate.recStatus=='ADD')
            AddedMatlsList = app_db.session.execute(stmt).mappings().all()
            stmt = select(tmpMaterialListUpdate).where(tmpMaterialListUpdate.recStatus.startswith('DEL'))
            RemvdMatlsList = app_db.session.execute(stmt).mappings().all()
            cntext = {
                'ImpErrList':ImpErrList,
                'AddedMatls':AddedMatlsList,
                'RemvdMatls':RemvdMatlsList,
                }
            templt = 'Material/frmUpdateMatlListfromSAP_done.html'
            return checkTemplate_and_render(templt, cntext)
        elif client_phase=='cleanup-after-failure':
            pass
        elif client_phase=='resultspresented':
            proc_MatlListSAPSprsheet_99_Cleanup(reqid)
            retinfo = make_response(jsonify(success=True))
            # retinfo.delete_cookie('reqid')

            return retinfo
        else:
            return
        #endif client_phase
    else:   # req.method != 'POST'
        # (hopefully,) this is the initial phase; all others will be part of a POST request

        cntext = {
            'reqid': -1,
            }
        templt = 'Material/frmUpdateMatlListfromSAP_phase0.html'
        return checkTemplate_and_render(templt, **cntext)
    #endif req.method = 'POST'
# fnunUpdateMatlListfromSAP

