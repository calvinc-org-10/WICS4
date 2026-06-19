from datetime import datetime

from flask_login import login_required, current_user

from .CountEntryForm import CountEntryForm, RelatedMaterialInfo, RelatedScheduleInfo
from ..models import ActualCounts, MaterialList, WhsePartTypes

@login_required
def fnCountEntryView(req, 
            recNum = None, MatlNum = None, reqDate = None,
            gotoCommand = None
            ):

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
        'main': {'CountDate': reqDate,'Counter':current_user().username},
        'matl': {},
        'schedule': {'CountDate': reqDate},
    }

    changes_saved = {
        'main': False,
        'matl': False,
        'schedule': False
        }
    chgd_dat = {
        'main':None, 
        'matl': None, 
        'schedule': None
        }

    if req.method == 'POST':
        R = req.POST[prefixvals['main']+'-id']
        recNum = int(R) if R.isnumeric() else 0
        try:
            currRec = modelMain.objects.using(dbUsing).get(pk=recNum)
        except:
            currRec = modelMain()
        matlRec = modelSubs[0].objects.using(dbUsing).get(id=req.POST['MatlPK'])
        #schedRecs = modelSubs[1].objects.filter(org=_userorg, CountDate=req.POST[prefixvals['main']+'-CountDate'], Material=matlRec)

        # process main form
        if currRec: mainFm = FormMain(req.POST, instance=currRec,  prefix=prefixvals['main'])   # do I need to pass in intial?
        else: mainFm = FormMain(req.POST, initial=initialvals['main'],  prefix=prefixvals['main']) 
        matlSubFm = FormSubs[0](matlRec.pk, req.POST, instance=matlRec, prefix=prefixvals['matl'])
        #schedSet = RelatedScheduleInfo(_userorg, SchedID, req.POST, prefix=prefixvals['schedule'], initial=initialvals['schedule'])

        s = modelMain.objects.using(dbUsing).none()

        # if mainFm.is_valid() and matlSubFm.is_valid() and schedFm.is_valid():
        if mainFm.is_valid() and matlSubFm.is_valid():
            if mainFm.has_changed():
                s = mainFm.save(req=req)
                chgd_dat['main'] = []
                for chgdfld in mainFm.changed_data:
                    chgd_dat['main'].append(chgdfld+'='+str(mainFm.cleaned_data[chgdfld]))
                changes_saved['main'] = s.id
            # material info subform
            if matlSubFm.has_changed():
                matlSubFm.save(req=req)
                chgd_dat['matl'] = []
                for chgdfld in matlSubFm.changed_data:
                    chgd_dat['matl'].append(chgdfld+'='+str(matlSubFm.cleaned_data[chgdfld]))
                changes_saved['matl'] = True
            # count schedule subform
            # if schedSet.has_changed():
            #      schedSet.save()
            #      chgd_dat['schedule'] = schedSet.changed_data
            #      changes_saved['schedule'] = True

            # prep new record to present
            currRec = modelMain(CountDate=reqDate,Counter=req.user.get_short_name())
            recNum=0
            MatlNum = 0
            matlRec = getattr(currRec,'Material', '')
            # MaterialID = getattr(matlRec, 'pk', None)

            if currRec: 
                mainFm = FormMain(instance=currRec, prefix=prefixvals['main'])
            else:       
                mainFm = FormMain(initial=initialvals['main'],  prefix=prefixvals['main'])
            if matlRec:
                matlSubFm = FormSubs[0](matlRec.pk, instance=matlRec, prefix=prefixvals['matl'])
            else:
                matlSubFm = FormSubs[0](None, initial=initialvals['matl'], prefix=prefixvals['matl'])
    else:   ## rec.method != 'POST'
        currRec = modelMain(CountDate=reqDate,Counter=req.user.get_short_name())
        matlRec = modelSubs[0].objects.using(dbUsing).none()

        # TODO: add protection against no records
        recFirstPK = modelMain.objects.using(dbUsing).order_by('id').first().pk
        recLastPK = modelMain.objects.using(dbUsing).order_by('id').last().pk
        
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
                    recNum = modelMain.objects.using(dbUsing).filter(pk__lt=recNum).order_by('id').last().pk
            except:
                recNum = 0
        elif gotoCommand == 'Next':
            try:
                if recNum <= 0:
                    recNum = recFirstPK
                elif recNum >= recLastPK:
                    recNum = recLastPK
                else:
                    recNum = modelMain.objects.using(dbUsing).filter(pk__gt=recNum).order_by('id').first().pk
            except:
                recNum = 0
        else:
            pass

        if recNum:
            currRec = modelMain.objects.using(dbUsing).get(pk=recNum)
            matlRec = currRec.Material  # subject to change

        if gotoCommand == 'ChgKey':
            currRec.CountDate = reqDate
            matlRec = modelSubs[0].objects.using(dbUsing).get(pk=MatlNum)
            currRec.Material = matlRec
            currRec.Material_id = MatlNum

        # at this point, currRec and matlRec s/b correct

        if currRec: 
            mainFm = FormMain(instance=currRec, prefix=prefixvals['main'])
        else:       
            mainFm = FormMain(initial=initialvals['main'],  prefix=prefixvals['main'])
        if matlRec:
            matlSubFm = FormSubs[0](matlRec.pk, instance=matlRec, prefix=prefixvals['matl'])
        else:
            matlSubFm = FormSubs[0](None, initial=initialvals['matl'], prefix=prefixvals['matl'])
    #endif rec.method == 'POST'

    # all counts for this Material today
    if matlRec:
        matchDate = reqDate
        if currRec: matchDate = currRec.CountDate
        todayscounts = modelMain.objects.using(dbUsing).filter(CountDate=matchDate,Material=matlRec)
    else: 
        todayscounts = modelMain.objects.using(dbUsing).none()

    if currRec:
        getDate = currRec.CountDate
        if matlRec and modelSubs[1].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec).exists():
            schedinfo = modelSubs[1].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
        else:
            schedinfo = modelSubs[1].objects.using(dbUsing).none()
    elif (MatlNum!=0) and (gotoCommand==None):
        # review and clean up this block!
        if MatlNum != 0:
            # fill in MatlInfo and CountSchedInfo
            if recNum > 0: getDate = currRec.CountDate 
            else: getDate = reqDate
            if modelSubs[1].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec).exists():
                schedinfo = modelSubs[1].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
            else:
                schedinfo = modelSubs[1].objects.using(dbUsing).none()
        elif recNum > 0:
            # ??????????? shouldn't this already be handled?  Think about it...
            # fill in MatlInfo and CountSchedInfo
            getDate = currRec.CountDate
            if modelSubs[1].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec).exists():
                schedinfo = modelSubs[1].objects.using(dbUsing).filter(CountDate=getDate, Material=matlRec)[0]  # filter rather than get, since a scheduled count may not exist, or multiple may exist (shouldn't but ...)
            else:
                schedinfo = modelSubs[1].objects.using(dbUsing).none()
    else: 
        schedinfo = modelSubs[1].objects.using(dbUsing).none()
    #endif currRec
    if not schedinfo: schedFm = FormSubs[1](None, initial=initialvals['schedule'], prefix=prefixvals['schedule'])
    else: schedFm = FormSubs[1](schedinfo.pk, instance=schedinfo, prefix=prefixvals['schedule'])

    # CountEntryForm MaterialList dropdown
    matlchoiceForm = {}
    if matlRec:
        matlchoiceForm['gotoItem'] = matlRec        # the template pulls Material from this record
    else:
        if MatlNum==None: MatlNum = 0
        ## matlchoiceForm['gotoItem'] = {'Material':MatlNum}
        matlchoiceForm['gotoItem'] = ''
    matlchoiceForm['choicelist'] = VIEW_materials.objects.using(dbUsing).all().values('id','Material_org')

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
    templt = 'frm_CountEntry.html'
    return render(req, templt, cntext)

