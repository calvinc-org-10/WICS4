from typing import Dict, Any, List
from datetime import datetime, date

from flask_login import login_required, current_user
from flask import (
    redirect, url_for, abort,
    flash, 
    request, session, 
    current_app,
    )

from calvincTools.utils import checkTemplate_and_render

from forms.CountEntryForm import CountEntryForm, RelatedMaterialInfo, RelatedScheduleInfo
from models import ActualCounts, MaterialList, WhsePartTypes

from database import app_db


def _coerce_date(date_to_coerce: object) -> date:
    """Convert route/request date values into a date object for form/model use."""
    if isinstance(date_to_coerce, datetime):
        return date_to_coerce.date()
    if isinstance(date_to_coerce, date):
        return date_to_coerce
    if isinstance(date_to_coerce, str):
        cleaned = date_to_coerce.strip()
        if cleaned:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%m-%d-%Y"):
                try:
                    return datetime.strptime(cleaned, fmt).date()
                except ValueError:
                    continue
    return datetime.today().date()

@login_required
def fnCountEntryView( 
        recNum = None, MatlNum = None, reqDate = None,
        gotoCommand = None
        ):

    # defauls parms
    if recNum is None: recNum = 0
    reqDate = _coerce_date(reqDate)

    # the string 'None' is not the same as the value None
    if MatlNum=='None' or MatlNum is None: MatlNum=0
    if gotoCommand=='None': gotoCommand=None

    FormMain = CountEntryForm
    FormSubs = [S for S in [RelatedMaterialInfo, RelatedScheduleInfo]]
    matlSubIndx = 0
    schdSubIndx = 1

    modelMain = FormMain.Meta.model
    modelSubs = [S.Meta.model for S in FormSubs]
    
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
        'matl': modelSubs[matlSubIndx](**initialvals['matl']),
        'schedule': modelSubs[schdSubIndx](**initialvals['schedule']),
    }

    # process main form
    mainFm = FormMain(prefix=prefixvals['main'], obj=initialobj['main'])   # Note that you don’t have to pass request.form to Flask-WTF; it will load automatically. And the convenient validate_on_submit will check if it is a POST request and if it is valid.
    matlSubFm = FormSubs[matlSubIndx](prefix=prefixvals['matl'], obj=initialobj['matl'])
    schedSet = FormSubs[schdSubIndx](prefix=prefixvals['schedule'], obj=initialobj['schedule'])

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
        formRec = modelMain()
        mainFm.populate_obj(formRec)
        recNum = int(getattr(formRec, 'id', 0) or 0)
        currRec = app_db.session.get(modelMain, recNum) or modelMain()

        matlformRec = modelSubs[matlSubIndx]()
        matlSubFm.populate_obj(matlformRec)
        matlRecNum = int(getattr(matlformRec, 'id', 0))
        model_class = modelSubs[matlSubIndx]
        matlRec = app_db.session.get(model_class, matlRecNum) or model_class()

        # Description is display-only in this subform; keep persisted value on POST.
        if hasattr(matlSubFm, 'Description'):
            matlSubFm.Description.data = getattr(matlRec, 'Description', None)

        #schedRecs = modelSubs[schdSubIndx].objects.filter(org=_userorg, CountDate=req.POST[prefixvals['main']+'-CountDate'], Material=matlRec)

        # what's changed in main form?
        chgd_dat['main'] = [
            f'{field.short_name}={field.data}' 
            for field in mainFm if hasattr(currRec, field.short_name) and getattr(currRec, field.short_name) != field.data
        ]
        if len(chgd_dat['main']) > 0:
            formRec.save()
            changes_saved['main'] = formRec.id
        
        # now changes to material record
        chgd_dat['matl'] = [
            f'{field.short_name}={field.data}'
            for field in matlSubFm
            if field.short_name != 'Description'
            and hasattr(matlRec, field.short_name)
            and getattr(matlRec, field.short_name) != field.data
        ]
        if len(chgd_dat['matl']) > 0:
            matlformRec.save()
            changes_saved['matl'] = matlRec.id

            # count schedule subform
            # if schedSet.has_changed():
            #      schedSet.save()
            #      chgd_dat['schedule'] = schedSet.changed_data
            #      changes_saved['schedule'] = True

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
            # if currRec:
            #     currRec.CountDate = reqDate
            #     matlRec = modelSubs[matlSubIndx].query.get(MatlNum)
            #     currRec.Material_id = MatlNum
            #     currRec.Material = matlRec
            pass
        else:
            raise ValueError(f"Invalid gotoCommand: {gotoCommand}")
        # endif gotoCommand

        currRec = app_db.session.get(modelMain, recNum) or initialobj['main']

        if MatlNum != 0 and MatlNum != currRec.Material_id:
            currRec.Material_id = MatlNum
        model_class = modelSubs[matlSubIndx]
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
        matlSubFm = FormSubs[matlSubIndx](formdata=None, obj=matlRec, prefix=prefixvals['matl'])
        matlRecNum = matlRec.id
    else:
        matlSubFm = FormSubs[matlSubIndx](formdata=None, obj=initialvals['matl'], prefix=prefixvals['matl'])
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
        schedinfo = modelSubs[schdSubIndx].query.filter(modelSubs[schdSubIndx].CountDate==getDate, modelSubs[schdSubIndx].Material_id==matlRec.id).first()
    else:
        schedinfo = None    
    # endif currRec and matlRec
    if not schedinfo: 
        schedFm = FormSubs[schdSubIndx](formdata=None, obj=initialvals['schedule'], prefix=prefixvals['schedule'])
    else: 
        schedFm = FormSubs[schdSubIndx](formdata=None, obj=schedinfo, prefix=prefixvals['schedule'])
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
    templt = 'frm_CountEntry.html'
    return checkTemplate_and_render(templt, **cntext)

