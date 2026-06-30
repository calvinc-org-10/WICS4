from datetime import datetime, date

from flask_login import login_required, current_user
from flask import (
    redirect, url_for, abort,
    flash, 
    request, session, 
    current_app,
    )

from calvincTools.utils import checkTemplate_and_render

from .CountEntryForm import CountEntryForm, RelatedMaterialInfo, RelatedScheduleInfo
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

    changes_saved = {
        'main': False,
        'matl': False,
        'schedule': False
        }
    chgd_dat = {
        'main': [], 
        'matl': [], 
        'schedule': []
        }

    if request.method == 'POST' and mainFm.validate_on_submit() and matlSubFm.validate_on_submit(): # and schedSet.validate_on_submit():
        formRec = modelMain()
        mainFm.populate_obj(formRec)
        recNum = int(getattr(formRec, 'id', 0))
        currRec = app_db.session.get(modelMain, recNum) or modelMain()

        matlformRec = modelSubs[matlSubIndx]()
        matlSubFm.populate_obj(matlformRec)
        matlRecNum = int(getattr(matlformRec, 'id', 0))
        model_class = modelSubs[matlSubIndx]
        matlRec = app_db.session.get(model_class, matlRecNum) or model_class()

        #schedRecs = modelSubs[schdSubIndx].objects.filter(org=_userorg, CountDate=req.POST[prefixvals['main']+'-CountDate'], Material=matlRec)

        # what's changed in main form?
        chgd_dat['main'] = [
            f'{field.name}={field.data}' 
            for field in mainFm if hasattr(currRec, field.name) and getattr(currRec, field.name) != field.data
        ]
        if len(chgd_dat['main']) > 0:
            formRec.save()
        
        # now changes to material record
        chgd_dat['matl'] = [
            f'{field.name}={field.data}'
            for field in matlSubFm if hasattr(matlRec, field.name) and getattr(matlRec, field.name) != field.data
        ]
        if len(chgd_dat['matl']) > 0:
            matlSubFm.save()

            # count schedule subform
            # if schedSet.has_changed():
            #      schedSet.save()
            #      chgd_dat['schedule'] = schedSet.changed_data
            #      changes_saved['schedule'] = True

            # prep new record to present
            # currRec = modelMain(**initialvals['main'])
            # recNum=0
            # MatlNum = 0
            # matlRec = getattr(currRec,'Material', '')
            # # MaterialID = getattr(matlRec, 'pk', None)

            # NOTE: If you want the cleanest flow, do a redirect after POST and rebuild the forms on the following GET. That avoids carrying any POST state forward at all.
            return redirect(url_for('WICS.CountEntryForm'))
            # mainFm = FormMain(formdata=None, obj=initialobj["main"], prefix=prefixvals["main"])
            # matlSubFm = FormSubs[matlSubIndx](formdata=None, obj=initialobj["matl"], prefix=prefixvals["matl"])
            # schedFm = FormSubs[schdSubIndx](formdata=None, obj=initialobj["schedule"], prefix=prefixvals["schedule"])

    else:   ## rec.method != 'POST'
        currRec = modelMain(**initialvals['main'])
        matlRec = modelSubs[matlSubIndx](**initialvals['matl'])

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

        currRec = app_db.session.get(modelMain, recNum) or modelMain()

        if MatlNum != 0 and MatlNum != currRec.Material_id:
            currRec.Material_id = MatlNum
        model_class = modelSubs[matlSubIndx]
        matlRec = app_db.session.get(model_class, MatlNum) or model_class()

        # at this point, currRec and matlRec s/b correct
        if currRec: 
            mainFm = FormMain(formdata=None, obj=currRec, prefix=prefixvals['main'])
        else:       
            mainFm = FormMain(formdata=None, obj=initialvals['main'],  prefix=prefixvals['main'])
        # I know this is broken now. I'll get around to it. I need to rethink the flow of how the subforms are built and populated. I want to be able to build the subforms with the main form, so that they can be displayed together, and then have them populate and save separately. I also need to think about how to handle the case where there is no material record, or no schedule record, and how to handle the case where there are multiple schedule records for a given date and material.
        # I think I fixed it, but I need to test it. I also need to think about how to handle the case where there is no material record, or no schedule record, and how to handle the case where there are multiple schedule records for a given date and material.
        if matlRec:
            matlSubFm = FormSubs[matlSubIndx](formata=None, obj=matlRec, prefix=prefixvals['matl'])
            matlRecNum = matlRec.id
        else:
            matlSubFm = FormSubs[matlSubIndx](formdata=None, obj=initialvals['matl'], prefix=prefixvals['matl'])
            matlRecNum = 0
    #endif rec.method == 'POST'

    # all counts for this Material today
    if matlRec:
        matchDate = reqDate
        if currRec: matchDate = currRec.CountDate
        todayscounts = modelMain.query.filter(modelMain.CountDate==matchDate,modelMain.Material_id==matlRecNum).all()
    else: 
        # todayscounts = modelMain()
        todayscounts = None
    # endif matlRec

    # if currRec:
    #     getDate = currRec.CountDate
    #     if matlRec and modelSubs[schdSubIndx].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec).exists():
    #         schedinfo = modelSubs[schdSubIndx].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
    #     else:
    #         schedinfo = modelSubs[schdSubIndx].objects.using(dbUsing).none()
    # elif (MatlNum!=0) and (gotoCommand==None):
    #     # review and clean up this block!
    #     if MatlNum != 0:
    #         # fill in MatlInfo and CountSchedInfo
    #         if recNum > 0: getDate = currRec.CountDate 
    #         else: getDate = reqDate
    #         if modelSubs[schdSubIndx].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec).exists():
    #             schedinfo = modelSubs[schdSubIndx].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
    #         else:
    #             schedinfo = modelSubs[schdSubIndx].objects.using(dbUsing).none()
    #     elif recNum > 0:
    #         # ??????????? shouldn't this already be handled?  Think about it...
    #         # fill in MatlInfo and CountSchedInfo
    #         getDate = currRec.CountDate
    #         if modelSubs[schdSubIndx].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec).exists():
    #             schedinfo = modelSubs[schdSubIndx].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
    #         else:
    #             schedinfo = modelSubs[schdSubIndx].objects.using(dbUsing).none()
    # else: 
    #     schedinfo = modelSubs[schdSubIndx].objects.using(dbUsing).none()
    # #endif currRec

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
    if MatlNum==None: MatlNum = 0
    if MatlNum:     # this implies matlRec exists and is a real record, so we can use it to populate the dropdown
        assert matlRec is not None, "matlRec should not be None when MatlNum is provided"
        # matlchoiceForm['gotoItem'] = matlRec        # the template pulls Material from this record
        matlchoiceForm['gotoItem'] = f'{matlRec.Material}:{matlRec.org.orgname}'
    else:
        ## matlchoiceForm['gotoItem'] = {'Material':MatlNum}
        matlchoiceForm['gotoItem'] = ''
    matlchoiceForm['choicelist'] = [{'id': rec.id, 'Material_org': f'{rec.Material}:{rec.org.orgname}'} for rec in  MaterialList.query.all()]

    # display the form
    cntext = {'frmMain': mainFm,
            'frmMatlInfo': matlSubFm,
            'MatlNum': MatlNum,
            'todayscounts': todayscounts,
            'matlchoiceForm':matlchoiceForm,
            'noSchedInfo':(not schedinfo),
            'frmSchedInfo': schedFm,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            'recNum': recNum,
            }
    templt = '_newcode/frm_CountEntry.html'
    return checkTemplate_and_render(templt, **cntext)

