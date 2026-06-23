from datetime import datetime

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

@login_required
def fnCountEntryView( 
            recNum = None, MatlNum = None, reqDate = None,
            gotoCommand = None
            ):

    req = request
    
    # defauls parms
    if recNum is None: recNum = 0
    if reqDate is None: reqDate = datetime.today()

    # the string 'None' is not the same as the value None
    if MatlNum=='None' or MatlNum is None: MatlNum=0
    if gotoCommand=='None': gotoCommand=None

    FormMain = CountEntryForm
    FormSubs = [S for S in [RelatedMaterialInfo, RelatedScheduleInfo]]

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
        'matl': modelSubs[0](**initialvals['matl']),
        'schedule': modelSubs[1](**initialvals['schedule']),
    }

    # process main form
    mainFm = FormMain(prefix=prefixvals['main'], obj=initialobj['main'])   # Note that you don’t have to pass request.form to Flask-WTF; it will load automatically. And the convenient validate_on_submit will check if it is a POST request and if it is valid.
    matlSubFm = FormSubs[0](prefix=prefixvals['matl'], obj=initialobj['matl'])
    schedSet = FormSubs[1](prefix=prefixvals['schedule'], obj=initialobj['schedule'])

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

    if req.method == 'POST' and mainFm.validate_on_submit() and matlSubFm.validate_on_submit(): # and schedSet.validate_on_submit():
        formRec = modelMain()
        mainFm.populate_obj(formRec)
        recNum = int(getattr(formRec, 'id', 0))
        try:
            currRec = modelMain.query.get(recNum)
        except:
            currRec = modelMain()
        matlformRec = modelSubs[0]()
        matlSubFm.populate_obj(matlformRec)
        matlRecNum = int(getattr(matlformRec, 'id', 0))
        try:
            matlRec = modelSubs[0].query.get(matlRecNum)
        except:
            matlRec = modelSubs[0]()
        #schedRecs = modelSubs[1].objects.filter(org=_userorg, CountDate=req.POST[prefixvals['main']+'-CountDate'], Material=matlRec)

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
            mainFm = FormMain(formdata=None, obj=initialobj["main"], prefix=prefixvals["main"])
            matlSubFm = FormSubs[0](formdata=None, obj=initialobj["matl"], prefix=prefixvals["matl"])
            schedFm = FormSubs[1](formdata=None, obj=initialobj["schedule"], prefix=prefixvals["schedule"])

            # if currRec: 
            #     mainFm = FormMain(instance=currRec, prefix=prefixvals['main'])
            # else:       
            #     mainFm = FormMain(initial=initialvals['main'],  prefix=prefixvals['main'])
            # if matlRec:
            #     matlSubFm = FormSubs[0](matlRec.pk, instance=matlRec, prefix=prefixvals['matl'])
            # else:
            #     matlSubFm = FormSubs[0](None, initial=initialvals['matl'], prefix=prefixvals['matl'])
    else:   ## rec.method != 'POST'
        currRec = modelMain(**initialvals['main'])
        matlRec = modelSubs[0]()

        # TODO: add protection against no records
        recFirstPK = getattr(modelMain.query.order_by(modelMain.id).first(), 'id', 0)
        recLastPK = getattr(modelMain.query.order_by(modelMain.id.desc()).first(), 'id', 0)
        
        if gotoCommand == 'New':
            recNum = 0
        if gotoCommand == 'First':
            try:
                recNum = recFirstPK
            except:
                recNum = 0
        elif gotoCommand == 'Last':
            try:
                recNum = recLastPK
            except:
                recNum = 0
        elif gotoCommand == 'Prev':
            try:
                if recNum <= 0:
                    recNum = recLastPK
                elif recNum <= recFirstPK:
                    recNum = recFirstPK
                else:
                    recNum = getattr(modelMain.query.filter(modelMain.id < recNum).order_by(modelMain.id.desc()).first(), 'id', 0)
            except:
                recNum = 0
        elif gotoCommand == 'Next':
            try:
                if recNum <= 0:
                    recNum = recFirstPK
                elif recNum >= recLastPK:
                    recNum = recLastPK
                else:
                    recNum = getattr(modelMain.query.filter(modelMain.id > recNum).order_by(modelMain.id).first(), 'id', 0)
            except:
                recNum = 0
        else:
            pass

        if recNum:
            currRec = modelMain.query.get(recNum)
            matlRec = getattr(currRec, 'Material', None)  # subject to change
        else:
            currRec = modelMain(**initialvals['main'])
            matlRec = modelSubs[0](**initialvals['matl'])
        #endif recNum

        # if gotoCommand == 'ChgKey':
        #     currRec.CountDate = reqDate
        #     matlRec = modelSubs[0].objects.using(dbUsing).get(pk=MatlNum)
        #     currRec.Material = matlRec
        #     currRec.Material_id = MatlNum

        # at this point, currRec and matlRec s/b correct

        if currRec: 
            mainFm = FormMain(formdata=None, obj=currRec, prefix=prefixvals['main'])
        else:       
            mainFm = FormMain(formdata=None, obj=initialvals['main'],  prefix=prefixvals['main'])
        # I know this is broken now. I'll get around to it. I need to rethink the flow of how the subforms are built and populated. I want to be able to build the subforms with the main form, so that they can be displayed together, and then have them populate and save separately. I also need to think about how to handle the case where there is no material record, or no schedule record, and how to handle the case where there are multiple schedule records for a given date and material.
        if matlRec:
            matlSubFm = FormSubs[0](formata=None, obj=matlRec, prefix=prefixvals['matl'])
            matlRecNum = matlRec.id
        else:
            matlSubFm = FormSubs[0](formdata=None, obj=initialvals['matl'], prefix=prefixvals['matl'])
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
    #     if matlRec and modelSubs[1].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec).exists():
    #         schedinfo = modelSubs[1].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
    #     else:
    #         schedinfo = modelSubs[1].objects.using(dbUsing).none()
    # elif (MatlNum!=0) and (gotoCommand==None):
    #     # review and clean up this block!
    #     if MatlNum != 0:
    #         # fill in MatlInfo and CountSchedInfo
    #         if recNum > 0: getDate = currRec.CountDate 
    #         else: getDate = reqDate
    #         if modelSubs[1].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec).exists():
    #             schedinfo = modelSubs[1].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
    #         else:
    #             schedinfo = modelSubs[1].objects.using(dbUsing).none()
    #     elif recNum > 0:
    #         # ??????????? shouldn't this already be handled?  Think about it...
    #         # fill in MatlInfo and CountSchedInfo
    #         getDate = currRec.CountDate
    #         if modelSubs[1].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec).exists():
    #             schedinfo = modelSubs[1].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
    #         else:
    #             schedinfo = modelSubs[1].objects.using(dbUsing).none()
    # else: 
    #     schedinfo = modelSubs[1].objects.using(dbUsing).none()
    # #endif currRec

    # schedule info for this material and date
    schedinfo = None
    if currRec and matlRec:
        getDate = currRec.CountDate
        schedinfo = modelSubs[1].query.filter(modelSubs[1].CountDate==getDate, modelSubs[1].Material_id==matlRec.id).first()
    else:
        schedinfo = None    
    # endif currRec and matlRec
    if not schedinfo: 
        schedFm = FormSubs[1](formdata=None, obj=initialvals['schedule'], prefix=prefixvals['schedule'])
    else: 
        schedFm = FormSubs[1](formdata=None, obj=schedinfo, prefix=prefixvals['schedule'])
    # endif schedinfo

    # CountEntryForm MaterialList dropdown
    matlchoiceForm = {}
    if matlRec:
        matlchoiceForm['gotoItem'] = matlRec        # the template pulls Material from this record
    else:
        if MatlNum==None: MatlNum = 0
        ## matlchoiceForm['gotoItem'] = {'Material':MatlNum}
        matlchoiceForm['gotoItem'] = ''
    matlchoiceForm['choicelist'] = [{'id': rec.id, 'Material_org': f'{rec.Material}:{rec.org.orgname}'} for rec in  MaterialList.query.all()]

    # display the form
    cntext = {'frmMain': mainFm,
            'frmMatlInfo': matlSubFm,
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

