
from flask_login import login_required, current_user
from flask import (
    # redirect, url_for, 
    abort,
    flash,
    # request, session,
    # current_app,
    )

from calvincTools.utils import (
    checkTemplate_and_render,
    coerce_date,
    )

from forms.CountSchedule.CountScheduleRecordForm import CountScheduleRecordForm
from forms.Material.RelatedMaterialInfoForm import RelatedMaterialInfo
# from WICS.procs_misc import HolidayList
# from WICS.procs_CountSchedule import fnCountScheduleRecordExists

from models import MaterialList
from database import app_db


def _fnCountSchedRecViewCommon(variation,
            recNum = 0, MatlNum = 0, reqDate = None,
            gotoCommand = None, **kwargs
            ):

    # flags indicating whether key parameters were given
    MatlNumPassed = MatlNum is not None
    reqDatePassed = reqDate is not None
    recNumPassed = recNum is not None
    
    # defauls parms
    if not recNumPassed: recNum = 0
    reqDate = coerce_date(reqDate)
    #// review this logic for handling default non-workdays
    # skipdates = HolidayList(req)
    # reqDate = calvindate().nextWorkdayAfter(extraNonWorkdayList=skipdates)

    # the string 'None' is not the same as the value None
    if MatlNum=='None' or not MatlNumPassed: MatlNum=0
    if gotoCommand=='None': gotoCommand=None

    FormMain = CountScheduleRecordForm
    FormSubs = {'matl': RelatedMaterialInfo}

    modelMain = FormMain.Meta.model
    modelSubs = {key:S.Meta.model for key, S in FormSubs.items()}

    prefixvals = {
        'main': 'counts',
        'matl': 'matl',
    }
    initialvals = {
        'main': {'CountDate': reqDate, 'RequestFilled': None},
        'matl': {},
    }
    initialvals['main']['Requestor'] = current_user.get_short_name() if variation == 'REQ' else None
    
    initialobj = {
        'main': modelMain(**initialvals['main']),
        'matl': modelSubs['matl'](**initialvals['matl']),
    }

    # process forms
    mainFm = FormMain(prefix=prefixvals['main'], obj=initialobj['main'])   # Note that you don't have to pass request.form to Flask-WTF; it will load automatically. And the convenient validate_on_submit will check if it is a POST request and if it is valid.
    matlSubFm = FormSubs['matl'](prefix=prefixvals['matl'], obj=initialobj['matl'])

    chgd_dat = {
        'main': [], 
        'matl': [], 
        }

    msgDupSched = ''

    # if req.method == 'POST':
    if mainFm.validate_on_submit() and matlSubFm.validate_on_submit():
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
            flash('Select a valid Material.', 'error')
            cntext = {
                    'variation': variation,
                    'frmMain': mainFm,
                    'newRecord_flag': postedRecNum == 0,
                    'frmMatlInfo': matlSubFm,
                    'matlchoiceForm': {'gotoItem': '', 'choicelist': []},
                    'noSchedInfo':True,
                    'changed_data': chgd_dat,
                    }
            templt = 'CountSchedule/CountScheduleRec.html'

            return checkTemplate_and_render(
                templt, **cntext
            )

        before_main = {
            field.short_name: getattr(currRec, field.short_name)
            for field in mainFm
            if field.short_name != 'csrf_token' and hasattr(currRec, field.short_name)
        }

        mainFm.populate_obj(currRec)
        if postedRecNum and postedRecNum != currRec.id:
            currRec.id = postedRecNum
        currRec.Material_id = matlRecNum
        if variation=='REQ' or 'Requestor' in mainFm.data:
            currRec.Requestor = currRec.Requestor or current_user.get_short_name()
            currRec.Requestor_userid_id = current_user.id

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

        # Description is display-only in this subform; keep persisted value on POST.
        if hasattr(matlSubFm, 'Description'):
            matlSubFm.Description.data = getattr(matlRec, 'Description', None)

        # now changes to material record
        chgd_dat['matl'] = ["changes to material record not supported at this time"]

        # we build the new record to present. We don't want to carry any POST state forward, but we do want to show the user the record they just saved.
        # We use the post-if POST/GET logic here so that chgd_dat will be passed into context.
        currRec = initialobj['main']
        matlRec = initialobj['matl']

    else:   # rec.method != 'POST'

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
        elif ((reqDatePassed and reqDate != savedRec.CountDate)
                or (MatlNumPassed and MatlNum != savedRec.Material_id)):
            # review this logic
            currRec = modelMain(
                **{column.name: getattr(savedRec, column.name) for column in savedRec.__table__.columns}
            )
            currRec.CountDate = reqDate or savedRec.CountDate
        else:
            currRec = savedRec

        if MatlNumPassed and MatlNum != currRec.Material_id:
            currRec.Material_id = MatlNum
        model_class = modelSubs['matl']
        matlRecNum = int(getattr(currRec, 'Material_id', 0) or 0)
        matlRec = app_db.session.get(model_class, matlRecNum) or initialobj['matl']

    #endif rec.method = 'POST'

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

#// wics3 code
    # display the form
    cntext = {
            'variation': variation,
            'frmMain': mainFm,
            'newRecord_flag': currRec is None or currRec.id == 0,
            'frmMatlInfo': matlSubFm,
            'matlchoiceForm':matlchoiceForm,
            'changed_data': chgd_dat,
            }
    templt = 'CountSchedule/CountScheduleRec.html'

    return checkTemplate_and_render(
        templt, **cntext
    )

@login_required
def fnRequestCountScheduleRecView(
            recNum = 0, MatlNum = 0, reqDate = None,
            gotoCommand = None
            ):
    return _fnCountSchedRecViewCommon('REQ',
            recNum, MatlNum, reqDate,
            gotoCommand
            )

@login_required
def fnCountScheduleRecView(
            recNum = 0, MatlNum = 0, reqDate = None,
            gotoCommand = None
            ):

    return _fnCountSchedRecViewCommon(None,
            recNum, MatlNum, reqDate,
            gotoCommand
            )

