from typing import Dict, Any
from datetime import datetime, date

from flask_login import login_required, current_user
from flask import (
    redirect, url_for, abort,
    flash,
    request, session,
    current_app,
    )

from calvincTools.utils import (
    checkTemplate_and_render,
    coerce_date,
    )

from forms.ActualCounts.CountEntryForm import CountEntryForm, RelatedMaterialInfo, RelatedScheduleInfo
from models import ActualCounts, MaterialList, WhsePartTypes

from database import app_db


@login_required
def fnCountEntryView(
        recNum = None, MatlNum = None, reqDate = None,
        gotoCommand = None
        ):

    # defauls parms
    if recNum is None: recNum = 0
    reqDate = coerce_date(reqDate)

    # the string 'None' is not the same as the value None
    if MatlNum=='None' or MatlNum is None: MatlNum=0
    if gotoCommand=='None': gotoCommand=None

    FormMain = CountEntryForm
    FormSubs = {'matl': RelatedMaterialInfo, 'schedule': RelatedScheduleInfo}

    modelMain = FormMain.Meta.model
    modelSubs = {key:S.Meta.model for key, S in FormSubs.items()}

    prefixvals = {
        'main': 'counts',
        'matl': 'matl',
        'schedule': 'schedule',
    }
    initialvals = {
        'main': {'CountDate': reqDate,'Counter':current_user.username},
        'matl': {},
        'schedule': {'CountDate': reqDate},
    }
    initialobj = {
        'main': modelMain(**initialvals['main']),
        'matl': modelSubs['matl'](**initialvals['matl']),
        'schedule': modelSubs['schedule'](**initialvals['schedule']),
    }

    # process main form
    mainFm = FormMain(prefix=prefixvals['main'], obj=initialobj['main'])   # Note that you don't have to pass request.form to Flask-WTF; it will load automatically. And the convenient validate_on_submit will check if it is a POST request and if it is valid.
    matlSubFm = FormSubs['matl'](prefix=prefixvals['matl'], obj=initialobj['matl'])
    schedSet = FormSubs['schedule'](prefix=prefixvals['schedule'], obj=initialobj['schedule'])

    changes_saved:Dict[str, Any] = {
        'main': False,
        'matl': False,
        'schedule': False
        }
    chgd_dat = {
        'main': [],
        'matl': [],
        'schedule': []
        }

    # if request.method == 'POST' and mainFm.validate_on_submit() and matlSubFm.validate_on_submit(): # and schedSet.validate_on_submit():
    if mainFm.validate_on_submit() and matlSubFm.validate_on_submit(): # and schedSet.validate_on_submit():
        postedRecNum = int(mainFm.id.data or 0)
        if postedRecNum > 0:
            currRec = app_db.session.get(modelMain, postedRecNum)
            if currRec is None:
                abort(404)
        else:
            currRec = modelMain()

        try:
            matlRecNum = int(mainFm.Material_id.data or 0)
        except (TypeError, ValueError):
            matlRecNum = 0
        matlRec = app_db.session.get(modelSubs['matl'], matlRecNum) if matlRecNum > 0 else None
        if matlRec is None:
            mainFm.Material_id.errors.append('Select a valid Material.')
            return checkTemplate_and_render(
                'ActualCounts/frm_CountEntry_NEW.html',
                frmMain=mainFm,
                newRecord_flag=(postedRecNum == 0),
                frmMatlInfo=matlSubFm,
                todayscounts=None,
                matlchoiceForm={'gotoItem': '', 'choicelist': []},
                noSchedInfo=True,
                frmSchedInfo=schedSet,
                changes_saved=changes_saved,
                changed_data=chgd_dat,
            )

        before_main = {
            field.short_name: getattr(currRec, field.short_name)
            for field in mainFm
            if field.short_name != 'csrf_token' and hasattr(currRec, field.short_name)
        }
        mainFm.populate_obj(currRec)
        currRec.id = postedRecNum or None
        currRec.Material_id = matlRecNum

        chgd_dat['main'] = [
            f'{field}={getattr(currRec, field)}'
            for field, oldValue in before_main.items()
            if getattr(currRec, field) != oldValue
        ]
        if postedRecNum == 0:
            chgd_dat['main'].append('new record')

        if chgd_dat['main']:
            app_db.session.add(currRec)
            app_db.session.commit()
            changes_saved['main'] = currRec.id

        # Description is display-only in this subform; keep persisted value on POST.
        if hasattr(matlSubFm, 'Description'):
            matlSubFm.Description.data = getattr(matlRec, 'Description', None)

        # now changes to material record
        chgd_dat['matl'] = ["changes to material record not supported at this time"]

        # we build the new record to present. We don't want to carry any POST state forward, but we do want to show the user the record they just saved.
        # We use the post-if POST/GET logic here so that changes_saved and chgd_dat will be passed into context.
        currRec = initialobj['main']
        matlRec = initialobj['matl']

    else:   ## rec.method != 'POST'

        # TODO: add protection against no records
        recFirstPK = getattr(modelMain.query.order_by(modelMain.id).first(), 'id', 0)
        recLastPK = getattr(modelMain.query.order_by(modelMain.id.desc()).first(), 'id', 0)

        if gotoCommand is None:
            pass
        elif gotoCommand == 'New':
            recNum = 0
        elif gotoCommand == 'First':
            recNum = recFirstPK or 0
        elif gotoCommand == 'Last':
            recNum = recLastPK or 0
        elif gotoCommand == 'Prev':
            try:
                if recNum <= 0:
                    recNum = recLastPK
                elif recNum <= recFirstPK:
                    recNum = recFirstPK
                else:
                    recNum = getattr(modelMain.query.filter(modelMain.id < recNum).order_by(modelMain.id.desc()).first(), 'id', 0)
            except Exception:
                recNum = 0
        elif gotoCommand == 'Next':
            try:
                if recNum <= 0:
                    recNum = recFirstPK
                elif recNum >= recLastPK:
                    recNum = recLastPK
                else:
                    recNum = getattr(modelMain.query.filter(modelMain.id > recNum).order_by(modelMain.id).first(), 'id', 0)
            except Exception:
                recNum = 0
        elif gotoCommand == 'ChgKey':
            pass
        else:
            raise ValueError(f"Invalid gotoCommand: {gotoCommand}")
        # endif gotoCommand

        savedRec = app_db.session.get(modelMain, recNum)
        if savedRec is None:
            currRec = initialobj['main']
        elif ((reqDate is not None and reqDate != savedRec.CountDate)
                or (MatlNum != 0 and MatlNum != savedRec.Material_id)):
            currRec = modelMain(
                **{column.name: getattr(savedRec, column.name) for column in savedRec.__table__.columns}
            )
            currRec.CountDate = reqDate or savedRec.CountDate
        else:
            currRec = savedRec

        if MatlNum != 0 and MatlNum != currRec.Material_id:
            currRec.Material_id = MatlNum
        model_class = modelSubs['matl']
        matlRecNum = int(getattr(currRec, 'Material_id', 0) or 0)
        matlRec = app_db.session.get(model_class, matlRecNum) or initialobj['matl']

    #endif rec.method == 'POST'

    # at this point, currRec and matlRec s/b correct
    # prep the forms for display, using the current records (or initial values if no record exists)
    if currRec:
        mainFm = FormMain(formdata=None, obj=currRec, prefix=prefixvals['main'])
    else:
        mainFm = FormMain(formdata=None, obj=initialvals['main'],  prefix=prefixvals['main'])
    if matlRec and getattr(matlRec, 'id', None):
        matlSubFm = FormSubs['matl'](formdata=None, obj=matlRec, prefix=prefixvals['matl'])
        matlRecNum = matlRec.id
    else:
        matlSubFm = FormSubs['matl'](formdata=None, obj=initialvals['matl'], prefix=prefixvals['matl'])
        matlRecNum = 0

    # all counts for this Material today
    if matlRec:
        matchDate = reqDate
        if currRec.id is not None: matchDate = currRec.CountDate
        todayscounts = modelMain.query.filter(modelMain.CountDate==matchDate,modelMain.Material_id==matlRecNum).all()
    else:
        # todayscounts = modelMain()
        todayscounts = None
    # endif matlRec

    # schedule info for this material and date
    schedinfo = None
    if currRec and matlRec:
        getDate = currRec.CountDate
        schedinfo = modelSubs['schedule'].query.filter(modelSubs['schedule'].CountDate==getDate, modelSubs['schedule'].Material_id==matlRec.id).first()
    else:
        schedinfo = None
    # endif currRec and matlRec
    if not schedinfo:
        schedFm = FormSubs['schedule'](formdata=None, obj=initialvals['schedule'], prefix=prefixvals['schedule'])
    else:
        schedFm = FormSubs['schedule'](formdata=None, obj=schedinfo, prefix=prefixvals['schedule'])
    # endif schedinfo

    # CountEntryForm MaterialList dropdown
    matlchoiceForm = {}
    if matlRecNum:     # this implies matlRec exists and is a real record, so we can use it to populate the dropdown
        assert matlRec is not None, "matlRec should not be None when MatlNum is provided"
        # matlchoiceForm['gotoItem'] = matlRec        # the template pulls Material from this record
        matlchoiceForm['gotoItem'] = f'{matlRec.Material}:{matlRec.org.orgname}'
    else:
        ## matlchoiceForm['gotoItem'] = {'Material':MatlNum}
        matlchoiceForm['gotoItem'] = ''
    matlchoiceForm['choicelist'] = [{'id': rec.id, 'Material_org': f'{rec.Material}:{rec.org.orgname}'} for rec in  MaterialList.query.all()]

    # display the form
    cntext = {'frmMain': mainFm,
            'newRecord_flag': (currRec.id is None or currRec.id==0),
            'frmMatlInfo': matlSubFm,
            'todayscounts': todayscounts,
            'matlchoiceForm':matlchoiceForm,
            'noSchedInfo':(not schedinfo),
            'frmSchedInfo': schedFm,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            }
    templt = 'ActualCounts/frm_CountEntry_NEW.html'
    return checkTemplate_and_render(templt, **cntext)
