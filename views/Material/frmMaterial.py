import os
from types import SimpleNamespace
from typing import Dict, Any, List
from datetime import datetime, date

from flask import (
    redirect, url_for, abort,
    flash, 
    request, session, 
    current_app,
    )
from flask_login import login_required, current_user

from sqlalchemy import select, func, Integer, literal
from sqlalchemy.orm import selectinload, aliased

from calvincTools.utils import (
    checkTemplate_and_render,
    coerce_date,
    )
from calvincTools.mathexpr_parser import eval_arith

from forms.Material.MaterialForm import (
    MaterialForm, 
    CountsSubForm, ScheduleSubForm, MfrPNSubForm,
    MaterialCountSummaryLine,
    )
from models import (
    MaterialList, MaterialPhotos, 
    WhsePartTypes, 
    ActualCounts, CountSchedule, 
    MfrPNtoMaterial, 
    SAP_SOHRecs, UnitsOfMeasure,
    _defaultOrg,
    )

from database import app_db

# dummy until fnSAPList is defined
def fnSAPList(matl:Any=None):
    return []


@login_required
def fnMaterialForm(recNum = -1, gotoRec=False, newRec=False, HistoryCutoffDate=None):

    formlist = ['main', 'counts', 'schedule', 'MfrPN']

    FormWTF = {
        'main': MaterialForm,
        'counts': CountsSubForm,
        'schedule': ScheduleSubForm,
        'MfrPN': MfrPNSubForm,
    }

    modelSubs = {
        'main': FormWTF['main'].Meta.model,
        'counts': ActualCounts,
        'schedule': CountSchedule,
        'MfrPN': MfrPNtoMaterial,
        }

    FormFieldsSubs = {
        'main': [],
        'counts':
          ['id', 'CountDate', 'Counter', 'LocationOnly', 'CTD_QTY_Expr', 'LOCATION', 'FLAG_PossiblyNotRecieved', 'FLAG_MovementDuringCount', 'Notes',],
        'schedule':
          ['id','CountDate','Counter', 'Priority', 'ReasonScheduled', 'Notes',],
        'MfrPN':
          ['id', 'MfrPN', 'Manufacturer', 'Notes',],
    }

    prefixvals = {
        'main': 'material',
        'counts': 'countset',
        'schedule': 'schedset',
        'MfrPN': 'MPN',
        }
    initialvals = {
        # 'main': {'gotoItem': thisPK, 'showPK': thisPK, 'org':_defaultOrg},
        'main': {'org_id':_defaultOrg},
        'counts': {},
        'schedule': {},
        'MfrPN': {},
        }
    initialrec = {
        'main': modelSubs['main'](**initialvals['main']),
        'counts': modelSubs['counts'](**initialvals['counts']),
        'schedule': modelSubs['schedule'](**initialvals['schedule']),
        'MfrPN': modelSubs['MfrPN'](**initialvals['MfrPN']),
    }

    changes_saved = {
        'main': False,
        'counts': False,
        'schedule': False,
        'MfrPN': False,
        }
    chgd_dat = {
        'main':[], 
        'counts': [], 
        'schedule': [],
        'MfrPN': [],
        }

    class _SubFormSet(list):
        def __init__(self, forms_list, prefix):
            super().__init__(forms_list)
            self.prefix = prefix
            self.management_form = ''
            self.non_form_errors = []

        @property
        def errors(self):
            return [fm.errors for fm in self]

    def _build_subform_set(sub_key, recs):
        entries = [
            FormWTF[sub_key](prefix=f"{prefixvals[sub_key]}-{i}", obj=rec)
            for i, rec in enumerate(recs)
        ]
        if not entries:
            entries = [FormWTF[sub_key](prefix=f"{prefixvals[sub_key]}-0", obj=initialrec[sub_key])]
        return _SubFormSet(entries, prefixvals[sub_key])

    related_loads = (
        selectinload(MaterialList.actualcounts),
        selectinload(MaterialList.countschedule),
        selectinload(MaterialList.mfrpntomaterial),
        selectinload(MaterialList.materialphotos),
        selectinload(MaterialList.org),
    )

    if newRec:
        currRec = initialrec['main']
    elif recNum <= 0:
        currRec = app_db.session.execute(
            select(modelSubs['main']).options(*related_loads).order_by(modelSubs['main'].id)
        ).scalars().first() or initialrec['main']
    else:
        currRec = app_db.session.execute(
            select(modelSubs['main']).options(*related_loads).where(modelSubs['main'].id == recNum)
        ).scalars().first() or initialrec['main']

    # get current form
    mainFm = FormWTF['main'](prefix=prefixvals['main'], obj=currRec)
    mainFm.subforms = {
        'counts': _build_subform_set('counts', getattr(currRec, 'actualcounts', []) or []),
        'schedule': _build_subform_set('schedule', getattr(currRec, 'countschedule', []) or []),
        'MfrPN': _build_subform_set('MfrPN', getattr(currRec, 'mfrpntomaterial', []) or []),
    }

    if mainFm.validate_on_submit():         # includes test if request.method = 'POST' and if the form is valid
        # is a Photo being attached?
        PhotoOp_cmd = request.form.get('PhotoOp', '')
        if PhotoOp_cmd == "ADD":
            mPhotoPic = request.files["newPhoto"]
            if mPhotoPic.filename is not None:
                mPhotoPic.save(os.path.join(current_app.config.get('MTLPHOTO_FOLDER', 'mtl_photos'), mPhotoPic.filename))
            mPhotoRec = MaterialPhotos(
                Material_id = recNum,
                Photo = mPhotoPic.filename,
            )
            app_db.session.add(mPhotoRec)
            app_db.session.commit()
        #endif PhotoOp_cmd == "ADD"
            
        # is a photo being removed?
        if PhotoOp_cmd[:3] == "DEL":
            photoID = PhotoOp_cmd[4:]
            mPhotoRec = app_db.session.get(MaterialPhotos, photoID)
            assert mPhotoRec is not None, "Photo record not found"
            mPhotoPic = mPhotoRec.Photo
            if mPhotoPic is not None:
                os.remove(os.path.join(current_app.config.get('MTLPHOTO_FOLDER', 'mtl_photos'), mPhotoPic))
            app_db.session.delete(mPhotoRec)
        # end if PhotoOp_cmd[:3] == "DEL"
            
        # is there a request to copy a count?
        copyCountFromid = request.form.get('copyCountFromid', None)
        copyCountToDate = coerce_date(request.form.get('copyCountToDate', date.today()))
        if copyCountFromid is not None:
            try:
                copyCountFromid_int = int(copyCountFromid)
            except (TypeError, ValueError):
                copyCountFromid_int = -1
            copyCountRec = app_db.session.get(ActualCounts, copyCountFromid_int)
            assert copyCountRec is not None, "Count record not found"
            copiedCountRec = ActualCounts(
                CountDate=copyCountToDate,
                Counter=copyCountRec.Counter,
                LOCATION=copyCountRec.LOCATION,
                FLAG_PossiblyNotRecieved=copyCountRec.FLAG_PossiblyNotRecieved,
                FLAG_MovementDuringCount=copyCountRec.FLAG_MovementDuringCount,
                Material_id=copyCountRec.Material_id,
                LocationOnly=copyCountRec.LocationOnly,
                CycCtID=copyCountRec.CycCtID,
                CTD_QTY_Expr=copyCountRec.CTD_QTY_Expr,
                PKGID_Desc=copyCountRec.PKGID_Desc,
                TAGQTY=copyCountRec.TAGQTY,
                Notes=copyCountRec.Notes,
            )
            app_db.session.add(copiedCountRec)
            app_db.session.commit()
            flash(f'Count copied successfully from ID {copyCountFromid_int} to record {copiedCountRec.id}, date {copyCountToDate}', 'success')
        # endif copyCountFromid is not None

        # # process the forms
        # formRec = modelSubs['main']()
        # mainFm.populate_obj(formRec)
        # recNum = int(getattr(formRec, 'id', 0) or 0)
        # currRec = app_db.session.get(modelMain, recNum) or initialobj['main']

        for subform in mainFm.subforms:
            model_class = modelSubs[subform]
            formRec = model_class()
            FormWTF[subform].populate_obj(formRec)
            formRecID = int(getattr(formRec, 'id', 0))
            dbRec = app_db.session.get(model_class, formRecID) or initialrec[subform]
            
            chgd_dat[subform] = [
                f'{field.short_name}={field.data}'
                for field in FormWTF[subform]
                if hasattr(dbRec, field.short_name)
                and getattr(dbRec, field.short_name) != field.data
            ]
            if len(chgd_dat[subform]) > 0:
                formRec.save()
            
            if subform == 'main':
                currRec = formRec
        # end for subform in mainFm.subforms
        
    else:
        # handle GET request or when form is not valid
        pass
    # end if request.method 

    if newRec:
        SAP_SOH = fnSAPList(matl='-')
    else:
        SAP_SOH = fnSAPList(matl=currRec)
    # SAP_SOH = fnSAPList(matl=currRec)

    gotoForm = {
        'choicelist': [
            SimpleNamespace(id=rec.id, Material_org=f'{rec.Material}:{rec.org.orgname}') 
                for rec in app_db.session.query(MaterialList).all()
            ],
        'gotoItem': f'{currRec.Material}:{currRec.org.orgname}' if currRec else '',
    }

    # count summary subform
    SAP = aliased(SAP_SOHRecs)

    mult_subq = (
        select(UnitsOfMeasure.Multiplier1)
        .where(UnitsOfMeasure.UOM == SAP.BaseUnitofMeasure)
        .correlate(SAP)
        .scalar_subquery()
    )

    SAPTotals = app_db.session.execute(
        select(
            SAP.uploaded_at,
            SAP.MaterialPartNum,
            func.sum(SAP.Amount).label("SAPQty"),
            mult_subq.label("mult"),
        )
        .where(SAP.Material_id == currRec.id)
        .group_by(
            SAP.uploaded_at,
            SAP.MaterialPartNum,
            SAP.BaseUnitofMeasure,  # keeps grouped result deterministic for the correlated subquery
        )
        .order_by(SAP.uploaded_at, SAP.MaterialPartNum)
    ).mappings().all()
    raw_countdata = app_db.session.execute(
        select(
            ActualCounts
        )
        .where(ActualCounts.Material_id == currRec.id)
        .order_by(ActualCounts.CountDate, ActualCounts.id)
    )
    raw_countdata = [
        SimpleNamespace(
            ActualCounts=r.ActualCounts,
            Material=r.ActualCounts.Material,
            CountDate=r.ActualCounts.CountDate,
            QtyEval=0,
        )
        for r in raw_countdata
    ]
    for r in raw_countdata:
        if r.ActualCounts.CTD_QTY_Expr:
            try:
                r.QtyEval = eval_arith(r.ActualCounts.CTD_QTY_Expr)
            except Exception as e:
                r.QtyEval = 0
                # flash(f"Error evaluating CTD_QTY_Expr for count ID {r.ActualCounts.id}: {e}", "danger")
        else:
            r.QtyEval = 0
    LastMaterial = None ; LastCountDate = None
    summarydata = []
    summrecdict = {}
    SAPQty = 0 ; SAPDate = ''
    for r in raw_countdata:
        if (r.Material != LastMaterial or r.CountDate != LastCountDate):
            LastMaterial = r.Material ; LastCountDate = r.CountDate
            SAPTot_dateset = [s for s in SAPTotals if s.MaterialPartNum == r.Material and s.uploaded_at <= r.CountDate]
            if SAPTot_dateset:
                SAPDate = max(s.uploaded_at for s in SAPTot_dateset)
                SQ = next(s for s in SAPTot_dateset if s.uploaded_at == SAPDate)
                SAPQty = SQ.SAPQty * SQ.mult
            else:
                if len(SAPTotals) > 0:
                    SAPDate = SAPTotals[0]['uploaded_at']
                    SQ = SAPTotals[0]
                    SAPQty = SQ['SAPQty'] * SQ['mult']
                else:
                    SAPDate = ''
                    SAPQty = 0
            # endif SAPTot_dateset

            summrecdict = {
                'Material': r.Material,
                'CountDate': r.CountDate,
                'CountQTY_Eval': 0,
                'SAPDate': SAPDate,
                'SAPQty': SAPQty,
            }
        #endif (r.material or r.CountDate change)
        
        PIQty = summrecdict['CountQTY_Eval'] + r.QtyEval
        summrecdict['CountQTY_Eval'] = PIQty
        summrecdict['Diff'] = PIQty - SAPQty
        divsr = 1
        if PIQty!=0 or SAPQty!=0: divsr = max(PIQty, SAPQty)
        summrecdict['Accuracy'] = f"{min(PIQty, SAPQty) / divsr * 100:.2f}%"
        
        summarydata.append(SimpleNamespace(**summrecdict))
    # endfor r in raw_countdata
    # move this to method and tie with build_subform_set() to create a subform for the summary data ??
    prefixSummary = 'summaryset'
    entries = [
        MaterialCountSummaryLine(prefix=f"{prefixSummary}-{i}", obj=rec)
        for i, rec in enumerate(summarydata)
    ]
    if not entries:
        entries = [MaterialCountSummaryLine(prefix=f"{prefixSummary}-0")]   # , obj=initialrec[sub_key])]
    summaryFormSet = _SubFormSet(entries, prefixSummary)

    # Material photos
    PhotoSet = app_db.session.query(MaterialPhotos).filter_by(Material_id=currRec.id).all() if currRec else []

    # display the form
    if current_user.has_permission('WICS.Material_onlyview') and not current_user.has_permission('WICS.SuperUser'):
        templt = 'Material/frm_Material_RO.html'
    else: templt = 'Material/frm_Material.html'
    
    # LastFA = None if not currRec else VIEW_materials.objects.using(user_db(req)).filter(pk=currRec.pk).values('LastCountDate','LastFoundAt')[0]
    LastFA = SimpleNamespace(LastFoundAt="-- currently not implemented --", LastCountDate="---")

    FoundAt = [
        SimpleNamespace(CountDate=rec.CountDate, FoundAt=rec.LOCATION)
        for rec in currRec.actualcounts
    ]

    cntext = {
            'frmMain': mainFm,
            'PhotoSet': PhotoSet, 
            'userReadOnly': current_user.has_permission('WICS.Material_onlyview') and not current_user.has_permission('WICS.SuperUser'),
            'lastFoundAt': LastFA,
            'FoundAt': FoundAt,
            'gotoForm': gotoForm,
            'countset': mainFm.subforms['counts'],
            'scheduleset': mainFm.subforms['schedule'],
            'countsummset': summaryFormSet,
            'MPNset': mainFm.subforms['MfrPN'],
            'SAPSet': SAP_SOH,
            'changes_saved': changes_saved,
            'changed_data': chgd_dat,
            }
    
    return checkTemplate_and_render(templt, **cntext)

