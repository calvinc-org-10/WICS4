import os
import re
from types import SimpleNamespace
from typing import Dict, Any, List
from datetime import datetime, date
from enum import Enum

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
    WhsePartTypes, Organizations,
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

    #TODO: deprecate this
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

    def _to_int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _is_empty_value(value):
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ''
        return False

    def _has_meaningful_input(form_obj, field_names):
        for field_name in field_names:
            if field_name == 'id':
                continue
            if not hasattr(form_obj, field_name):
                continue
            data = getattr(form_obj, field_name).data
            if isinstance(data, bool):
                if data:
                    return True
            elif not _is_empty_value(data):
                return True
        return False

    def _build_subform_set(sub_key, recs):
        entries = []
        prefix = prefixvals[sub_key]
        posted_indices = set()

        # On POST, build forms from posted indexes so dynamic rows are processed.
        if request.method == 'POST':
            rgx = re.compile(rf"^{re.escape(prefix)}-(\d+)-")
            for key in request.form.keys():
                m = rgx.match(key)
                if m:
                    posted_indices.add(int(m.group(1)))

        if posted_indices:
            for i in sorted(posted_indices):
                rec = recs[i] if i < len(recs) else initialrec[sub_key]
                entries.append(FormWTF[sub_key](prefix=f"{prefix}-{i}", obj=rec))
        else:
            entries = [
                FormWTF[sub_key](prefix=f"{prefix}-{i}", obj=rec)
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
    elif request.method == 'POST':
        # On POST, retrieve the record based on the submitted form's ID.
        form_rec_id = _to_int(request.form.get(f"{prefixvals['main']}-id", 0), default=0)
        currRec = app_db.session.execute(
            select(modelSubs['main']).options(*related_loads).where(modelSubs['main'].id == form_rec_id)
        ).scalars().first() or initialrec['main']
    elif recNum <= 0:
        currRec = app_db.session.execute(
            select(modelSubs['main']).options(*related_loads).order_by(modelSubs['main'].id)
        ).scalars().first() or initialrec['main']
    else:
        currRec = app_db.session.execute(
            select(modelSubs['main']).options(*related_loads).where(modelSubs['main'].id == recNum)
        ).scalars().first() or initialrec['main']

    assert currRec is not None, "Material record context not available"

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

        all_subforms_valid = True
        for subform_key in ['counts', 'schedule', 'MfrPN']:
            for sbfm in mainFm.subforms[subform_key]:
                if not sbfm.validate():
                    all_subforms_valid = False

        if all_subforms_valid:
            # Save main record first so child rows can reference Material_id.
            main_form_rec_id = _to_int(getattr(mainFm.id, 'data', 0), default=0)
            db_main = app_db.session.get(modelSubs['main'], main_form_rec_id) if main_form_rec_id > 0 else None
            if db_main is None:
                db_main = modelSubs['main']()

            before_main = {
                field.short_name: getattr(db_main, field.short_name)
                for field in mainFm
                if field.short_name != 'csrf_token' and hasattr(db_main, field.short_name)
            }

            mainFm.populate_obj(db_main)

            chgd_dat['main'] = [
                f"{fld}={getattr(db_main, fld)}"
                for fld, old_val in before_main.items()
                if getattr(db_main, fld) != old_val
            ]

            if chgd_dat['main']:
                app_db.session.add(db_main)
                changes_saved['main'] = True

            if getattr(db_main, 'id', None) in (None, 0):
                app_db.session.add(db_main)

            app_db.session.flush()
            currRec = db_main
            assert currRec is not None, "Main material save failed"

            # Save child rows for each subform collection.
            for subform_key in ['counts', 'schedule', 'MfrPN']:
                model_class = modelSubs[subform_key]
                tracked_fields = [f for f in FormFieldsSubs[subform_key] if f != 'id']

                for sbfm in mainFm.subforms[subform_key]:
                    row_id = _to_int(getattr(getattr(sbfm, 'id', None), 'data', 0), default=0)
                    is_new = row_id <= 0

                    if is_new and not _has_meaningful_input(sbfm, tracked_fields):
                        continue

                    db_row = app_db.session.get(model_class, row_id) if row_id > 0 else None
                    if db_row is None:
                        db_row = model_class()
                    before_row = {
                        fld: getattr(db_row, fld)
                        for fld in tracked_fields
                        if hasattr(db_row, fld)
                    }

                    sbfm.populate_obj(db_row)

                    if hasattr(db_row, 'Material_id') and currRec is not None and getattr(currRec, 'id', None):
                        db_row.Material_id = currRec.id

                    row_changes = [
                        f"{fld}={getattr(db_row, fld)}"
                        for fld, old_val in before_row.items()
                        if getattr(db_row, fld) != old_val
                    ]

                    if row_changes or is_new:
                        app_db.session.add(db_row)
                        chgd_dat[subform_key].append(row_changes or ['new row'])
                        changes_saved[subform_key] = True

            app_db.session.commit()
        # endif all_subforms_valid
        # end save main/subforms
        
    else:
        # handle GET request or when form is not valid
        pass
    # end if request.method 

    if newRec:
        SAP_SOH = fnSAPList(matl='-')
    else:
        SAP_SOH = fnSAPList(matl=currRec)
    # SAP_SOH = fnSAPList(matl=currRec)

    assert currRec is not None, "Material record context not available"

    # Avoid assigning relationship on a transient record (e.g., newRec) because
    # later queries can trigger autoflush warnings for back-populated collections.
    currRec_org = currRec.org or app_db.session.get(Organizations, _defaultOrg)
    gotoForm = {
        'choicelist': [
            SimpleNamespace(id=rec.id, Material_org=f'{rec.Material}:{rec.org.orgname}') 
                for rec in app_db.session.query(MaterialList).all()
            ],
        'gotoItem': f'{currRec.Material}:{currRec_org.orgname}' if currRec_org and currRec.id and currRec.Material else '',
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


@login_required
def fnMaterialForm_NEW(recNum=-1, gotoRec=False, newRec=False, HistoryCutoffDate=None):
    """Material form flow refactor with explicit request cases.

    Cases:
    1) Initial form load (defaults)
    2) New record mode (gotoRec=False, newRec=True)
    3) GoTo record mode (recNum given, gotoRec=True)
    4) Change record (POST)
    """

    # Not used yet in this refactor.
    _ = HistoryCutoffDate
    
    class FlowCase(Enum):
        INITIAL_LOAD = 1
        NEW_RECORD = 2
        GOTO_RECORD = 3
        CHANGE_RECORD = 4
    
    formlist = ['main', 'counts', 'schedule', 'MfrPN']
    subformlist = [fm for fm in formlist if fm != 'main']

    FormWTF = {
        'main': MaterialForm,
        'counts': CountsSubForm,
        'schedule': ScheduleSubForm,
        'MfrPN': MfrPNSubForm,
    }

    modelSubs = { fm: FormWTF[fm].Meta.model for fm in formlist }

    FormFieldsSubs = {
        'main': [],
        'counts': ['id', 'CountDate', 'Counter', 'LocationOnly', 'CTD_QTY_Expr', 'LOCATION', 'FLAG_PossiblyNotRecieved', 'FLAG_MovementDuringCount', 'Notes'],
        'schedule': ['id', 'CountDate', 'Counter', 'Priority', 'ReasonScheduled', 'Notes'],
        'MfrPN': ['id', 'MfrPN', 'Manufacturer', 'Notes'],
    }

    prefixvals = {
        'main': 'material',
        'counts': 'countset',
        'schedule': 'schedset',
        'MfrPN': 'MPN',
    }

    initialvals = {
        'main': {'org_id': _defaultOrg},
        'counts': {},
        'schedule': {},
        'MfrPN': {},
    }

    initialrec = { fm: modelSubs[fm](**initialvals[fm]) for fm in formlist }

    #TODO: deprecate this, but keep for now to avoid breaking existing code
    changes_saved = {
        'main': False,
        'counts': False,
        'schedule': False,
        'MfrPN': False,
    }
    chgd_dat = {
        'main': [],
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

    def _coerce_int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _is_empty_value(value):
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ''
        return False

    def _has_meaningful_input(form_obj, field_names):
        for field_name in field_names:
            if field_name == 'id':
                continue
            if not hasattr(form_obj, field_name):
                continue
            data = getattr(form_obj, field_name).data
            if isinstance(data, bool):
                if data:
                    return True
            elif not _is_empty_value(data):
                return True
        return False

    def _build_subform_set(sub_key, recs):
        entries = []
        prefix = prefixvals[sub_key]
        posted_indices = set()

        if request.method == 'POST':
            rgx = re.compile(rf"^{re.escape(prefix)}-(\d+)-")
            for key in request.form.keys():
                m = rgx.match(key)
                if m:
                    posted_indices.add(int(m.group(1)))

        if posted_indices:
            for i in sorted(posted_indices):
                rec = recs[i] if i < len(recs) else initialrec[sub_key]
                entries.append(FormWTF[sub_key](prefix=f"{prefix}-{i}", obj=rec))
        else:
            entries = [
                FormWTF[sub_key](prefix=f"{prefix}-{i}", obj=rec)
                for i, rec in enumerate(recs)
            ]

        if not entries:
            # entries = [FormWTF[sub_key](prefix=f"{prefixvals[sub_key]}-0", obj=initialrec[sub_key])]
            entries = []
        return _SubFormSet(entries, prefixvals[sub_key])
    # _build_subform_set

    related_loads = (
        selectinload(MaterialList.actualcounts),
        selectinload(MaterialList.countschedule),
        selectinload(MaterialList.mfrpntomaterial),
        selectinload(MaterialList.materialphotos),
        selectinload(MaterialList.org),
    )

    # Case routing
    if request.method == 'POST':
        flow_case = FlowCase.CHANGE_RECORD
    elif gotoRec and recNum > 0:
        flow_case = FlowCase.GOTO_RECORD
    elif newRec and not gotoRec:
        flow_case = FlowCase.NEW_RECORD
    else:
        flow_case = FlowCase.INITIAL_LOAD
    # endif determine flow

    mainFm = None  # Initialize mainFm to None; will be set later based on flow_case
        
    # determine currRec based on the case. 
        # For CHANGE_RECORD, use the form's submitted ID to retrieve the original record.
        # after saving record, reload currRec from the database to ensure it reflects the latest state.
    if flow_case == FlowCase.NEW_RECORD:
        currRec = initialrec['main']
        
    elif flow_case == FlowCase.GOTO_RECORD:
        currRec = app_db.session.execute(
            select(modelSubs['main']).options(*related_loads).where(modelSubs['main'].id == recNum)
        ).scalars().first()
        if currRec is None:
            currRec = app_db.session.execute(
                select(modelSubs['main']).options(*related_loads).order_by(modelSubs['main'].id)
            ).scalars().first() or initialrec['main']
    
    elif flow_case == FlowCase.CHANGE_RECORD:
        form_rec_id = _coerce_int(request.form.get(f"{prefixvals['main']}-id", 0), default=0)
        # initial load of currRec based on the form's submitted ID
        if form_rec_id > 0:
            currRec = app_db.session.execute(
                select(modelSubs['main']).options(*related_loads).where(modelSubs['main'].id == form_rec_id)
            ).scalars().first() or initialrec['main']
        else:
            currRec = initialrec['main']

        mainFm = FormWTF['main'](prefix=prefixvals['main'], obj=currRec)
        mainFm.subforms = {
            'counts': _build_subform_set('counts', getattr(currRec, 'actualcounts', []) or []),
            'schedule': _build_subform_set('schedule', getattr(currRec, 'countschedule', []) or []),
            'MfrPN': _build_subform_set('MfrPN', getattr(currRec, 'mfrpntomaterial', []) or []),
        }

        if mainFm.validate_on_submit():
            all_subforms_valid = True
            for subform_key in subformlist:
                for sbfm in mainFm.subforms[subform_key]:
                    if not sbfm.validate():
                        all_subforms_valid = False

            if all_subforms_valid:
                # process main form first
                main_form_rec_id = _coerce_int(getattr(mainFm.id, 'data', 0), default=0)
                dbRec_main = app_db.session.get(modelSubs['main'], main_form_rec_id) if main_form_rec_id > 0 else None
                if dbRec_main is None:
                    dbRec_main = modelSubs['main']()

                before_main = {
                    field.short_name: getattr(dbRec_main, field.short_name)
                    for field in mainFm
                    if field.short_name != 'csrf_token' and hasattr(dbRec_main, field.short_name)
                }

                mainFm.populate_obj(dbRec_main)

                chgd_dat['main'] = [
                    f"{fld}={getattr(dbRec_main, fld)}"
                    for fld, old_val in before_main.items()
                    if getattr(dbRec_main, fld) != old_val
                ]

                if chgd_dat['main']:
                    app_db.session.add(dbRec_main)
                    changes_saved['main'] = True    # don't need to do this, but keep for now to avoid breaking existing code

                if getattr(dbRec_main, 'id', None) in (None, 0):
                    app_db.session.add(dbRec_main)

                app_db.session.flush()
                currRec = app_db.session.execute(
                    select(modelSubs['main']).options(*related_loads).where(modelSubs['main'].id == dbRec_main.id)
                ).scalars().first()
                assert currRec is not None, 'Main material save failed'

                # process subforms
                # No delete support: only insert/update child rows that were posted.
                for subform_key in subformlist:
                    model_class = modelSubs[subform_key]
                    tracked_fields = [f for f in FormFieldsSubs[subform_key] if f != 'id']      #???

                    for sbfm in mainFm.subforms[subform_key]:
                        row_id = _coerce_int(getattr(getattr(sbfm, 'id', None), 'data', 0), default=0)
                        is_new = row_id <= 0

                        if is_new and not _has_meaningful_input(sbfm, tracked_fields):
                            continue

                        db_row = app_db.session.get(model_class, row_id) if row_id > 0 else None
                        if db_row is None:
                            db_row = model_class()
                        before_row = {
                            fld: getattr(db_row, fld)
                            for fld in tracked_fields
                            if hasattr(db_row, fld)
                        }

                        sbfm.populate_obj(db_row)

                        if hasattr(db_row, 'Material_id') and currRec is not None and getattr(currRec, 'id', None):
                            db_row.Material_id = currRec.id

                        row_changes = [
                            f"{fld}={getattr(db_row, fld)}"
                            for fld, old_val in before_row.items()
                            if getattr(db_row, fld) != old_val
                        ]

                        if row_changes or is_new:
                            app_db.session.add(db_row)
                            chgd_dat[subform_key].append(row_changes or ['new record'])
                            changes_saved[subform_key] = True
                        #endif row_changes or is_new
                    # endfor sbfm in mainFm.subforms[subform_key]
                # endfor subform_key in ['counts', 'schedule', 'MfrPN']    

                app_db.session.commit()
            else:
                flash("Form validation failed. Please check the input fields.", "danger")
        # endif mainFm.validate_on_submit()

        # after record save, reload currRec from the database to ensure it reflects the latest state.
        if form_rec_id > 0:
            currRec = app_db.session.execute(
                select(modelSubs['main']).options(*related_loads).where(modelSubs['main'].id == form_rec_id)
            ).scalars().first() or initialrec['main']
        else:
            currRec = initialrec['main']
                
    else:   # flow_case == FlowCase.INITIAL_LOAD:
        currRec = app_db.session.execute(
            select(modelSubs['main']).options(*related_loads).order_by(modelSubs['main'].id)
        ).scalars().first() or initialrec['main']
    # endif flow_case for establishing currRec

    # define the output Form
    if mainFm is None:
        mainFm = FormWTF['main'](prefix=prefixvals['main'], obj=currRec)
        mainFm.subforms = {
            'counts': _build_subform_set('counts', getattr(currRec, 'actualcounts', []) or []),
            'schedule': _build_subform_set('schedule', getattr(currRec, 'countschedule', []) or []),
            'MfrPN': _build_subform_set('MfrPN', getattr(currRec, 'mfrpntomaterial', []) or []),
        }

    if flow_case == FlowCase.NEW_RECORD:
        SAP_SOH = fnSAPList(matl='-')
    else:
        SAP_SOH = fnSAPList(matl=currRec)

    # assert currRec is not None, 'Material record context not available'

    currRec_org = currRec.org or app_db.session.get(Organizations, _defaultOrg)
    gotoForm = {
        'choicelist': [
            SimpleNamespace(id=rec.id, Material_org=f'{rec.Material}:{rec.org.orgname}')
            for rec in app_db.session.query(MaterialList).all()
        ],
        'gotoItem': f'{currRec.Material}:{currRec_org.orgname}' if currRec_org and currRec.id and currRec.Material else '',
    }

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
            func.sum(SAP.Amount).label('SAPQty'),
            mult_subq.label('mult'),
        )
        .where(SAP.Material_id == currRec.id)
        .group_by(
            SAP.uploaded_at,
            SAP.MaterialPartNum,
            SAP.BaseUnitofMeasure,
        )
        .order_by(SAP.uploaded_at, SAP.MaterialPartNum)
    ).mappings().all()

    raw_countdata = app_db.session.execute(
        select(ActualCounts)
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
            except Exception:
                r.QtyEval = 0
        else:
            r.QtyEval = 0

    LastMaterial = None
    LastCountDate = None
    summarydata = []
    summrecdict = {}
    SAPQty = 0
    SAPDate = ''

    for r in raw_countdata:
        if r.Material != LastMaterial or r.CountDate != LastCountDate:
            LastMaterial = r.Material
            LastCountDate = r.CountDate
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

            summrecdict = {
                'Material': r.Material,
                'CountDate': r.CountDate,
                'CountQTY_Eval': 0,
                'SAPDate': SAPDate,
                'SAPQty': SAPQty,
            }

        PIQty = summrecdict['CountQTY_Eval'] + r.QtyEval
        summrecdict['CountQTY_Eval'] = PIQty
        summrecdict['Diff'] = PIQty - SAPQty
        divsr = 1
        if PIQty != 0 or SAPQty != 0:
            divsr = max(PIQty, SAPQty)
        summrecdict['Accuracy'] = f"{min(PIQty, SAPQty) / divsr * 100:.2f}%"

        summarydata.append(SimpleNamespace(**summrecdict))

    prefixSummary = 'summaryset'
    entries = [
        MaterialCountSummaryLine(prefix=f"{prefixSummary}-{i}", obj=rec)
        for i, rec in enumerate(summarydata)
    ]
    if not entries:
        entries = [MaterialCountSummaryLine(prefix=f"{prefixSummary}-0")]
    summaryFormSet = _SubFormSet(entries, prefixSummary)

    PhotoSet = app_db.session.query(MaterialPhotos).filter_by(Material_id=currRec.id).all() if currRec else []

    if current_user.has_permission('WICS.Material_onlyview') and not current_user.has_permission('WICS.SuperUser'):
        templt = 'Material/frm_Material_RO.html'
    else:
        templt = 'Material/frm_Material.html'

    LastFA = SimpleNamespace(LastFoundAt='-- currently not implemented --', LastCountDate='---')

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
        'changed_data': chgd_dat,
    }

    return checkTemplate_and_render(templt, **cntext)

def fnMaterialForm_photos(recNum=0):
    """Handle photo operations for a material record."""
    currRec = app_db.session.get(MaterialList, recNum)
    # TODO: Mov photo handling to a separate function or method as ajax call for clarity and maintainability.
    PhotoOp_cmd = request.form.get('PhotoOp', '')
    if PhotoOp_cmd == 'ADD':
        if currRec is None or getattr(currRec, 'id', None) in (None, 0):
            flash('Save the material record before adding photos.', 'warning')
        else:
            mPhotoPic = request.files["newPhoto"]
            if mPhotoPic.filename is not None:
                mPhotoPic.save(os.path.join(current_app.config.get('MTLPHOTO_FOLDER', 'mtl_photos'), mPhotoPic.filename))
                mPhotoRec = MaterialPhotos(
                    Material_id=currRec.id,
                    Photo=mPhotoPic.filename,
                )
                app_db.session.add(mPhotoRec)
                app_db.session.commit()
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

def fnMaterialForm_copycount(recNum=0):
    copyCountFromid = request.form.get('copyCountFromid', None)
    copyCountToDate = coerce_date(request.form.get('copyCountToDate', date.today()))
    if copyCountFromid is not None:
        copyCountFromid_int = int(copyCountFromid)
        # copyCountFromid_int = _coerce_int(copyCountFromid, default=-1)
        copyCountRec = app_db.session.get(ActualCounts, copyCountFromid_int)
        assert copyCountRec is not None, 'Count record not found'
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

