# WICS4 reusable code review and calvincTools extraction plan

Date: 2026-08-30

## Summary

This review looked through the app’s Python modules and templates to separate:

- app-specific WICS business logic
- generic reusable utilities
- code that is already clearly marked as needing to move into a shared library

The strongest candidates for moving into a shared `calvincTools` package are the spreadsheet import/coercion helpers and the generic async progress/status patterns.

---

## Best candidates to move into calvincTools

### 1) Spreadsheet coercion helpers

File: [views/ActualCounts/upldActCounts.py](views/ActualCounts/upldActCounts.py)

- `coerce_bool(val)`
- `cleanupfld(fld, val, CountSprshtDateEpoch=WINDOWS_EPOCH)`

Why these belong in a shared package:
- They are generic and not tied to WICS schema details.
- They normalize raw spreadsheet values for database inserts.
- They are already flagged as move candidates in the code comments.

Suggested home:
- `calvincTools.utils`
- or a dedicated `calvincTools.excel_imports` module if you want to separate import helpers from general utility functions.

---

### 2) Generic spreadsheet upload / workbook import workflow

Files:
- [views/ActualCounts/upldActCounts.py](views/ActualCounts/upldActCounts.py)
- [views/Material/updtMatlList.py](views/Material/updtMatlList.py)

Candidates:
- `proc_UpActCountSprsheet_00InitUpld`
- `proc_UpActCountSprsheet_00CopySpreadsheet`
- `proc_UpActCountSprsheet_01ReadSheet`
- `proc_UpActCountSprsheet_99_FinalProc`
- `proc_UpActCountSprsheet_99_Cleanup`
- `proc_MatlListSAPSprsheet_00InitUMLasync_comm`
- `proc_MatlListSAPSprsheet_00CopyUMLSpreadsheet`
- `proc_MatlListSAPSprsheet_00ResolveLocalSpreadsheetPath`
- `proc_MatlListSAPSprsheet_01ReadSpreadsheet`
- `proc_MatlListSAPSprsheet_99_FinalProc`
- `proc_MatlListSAPSprsheet_99_Cleanup`

Why these are reusable:
- They follow a common pattern: upload file, validate workbook, map columns, convert values, finalize, clean up.
- The WICS-specific piece is mostly the field map and the data model conversion; the surrounding mechanics are generic.

Suggested shared abstraction:
- `save_uploaded_workbook`
- `load_workbook_from_path`
- `validate_required_columns`
- `map_spreadsheet_columns`
- `read_uploaded_rows`
- `finalize_import`

---

### 3) Async job tracking/status helpers

File: [models.py](models.py)

- `HueySession`
- `async_comm`
- `get_async_comm_state`
- `set_async_comm_state`
- `delete_async_comm`

Why these are strong candidates:
- This is generic background-task progress tracking infrastructure.
- It is not tied to WICS business rules.
- It is exactly the type of shared facility a common package should own.

Suggested home:
- a shared async/job-status helper or model mixin in `calvincTools`

---

### 4) Generic dropdown/choice-list helpers

File: [models.py](models.py)

- `choices_for_organizations`
- `choices_for_materials`
- `choices_for_whseparttypes`

Why these are reusable:
- They all build `(id, label)` pairs from a model.
- The pattern is common across applications.

Suggested generalized helper:
- `model_choice_list(...)`

---

### 5) Template-side JS utility functions

File: [templates/ActualCounts/frm_CountEntry.html](templates/ActualCounts/frm_CountEntry.html)

- `serialize(elmnts)`
- `dtstr(dt = Date(), fmt = "YYYY-MM-DD HH:NN:SS")`
- `showCountExpr(expr_fld, rslt)`

Why these are reusable:
- These are generic browser utilities.
- They are not tied to WICS domain logic.
- There are explicit comments saying “move to common”.

Suggested home:
- shared JavaScript helper file / common static bundle

---

## Lower-priority but possible future moves

### `Base.save` in models.py

File: [models.py](models.py)

- `Base.save(self)`

This is a general pattern, but less compelling than the shared import and async helpers.
It’s still generally useful, but it is not as obviously reusable as the spreadsheet and async infrastructure.

---

## Should stay in this app

These are clearly WICS application logic and should not be moved into `calvincTools` as-is:

- `fnCountEntryView` in [views/ActualCounts/frmCountEntryView.py](views/ActualCounts/frmCountEntryView.py)
- `fnMaterialForm` in [views/Material/frmMaterial.py](views/Material/frmMaterial.py)
- `fnCountSummaryRpt` in [views/ActualCounts/rptCountSummary.py](views/ActualCounts/rptCountSummary.py)
- `fnSAPList` and SAP logic in [views/SAP/procs_SAP.py](views/SAP/procs_SAP.py)
- Domain models including `ActualCounts`, `MaterialList`, `CountSchedule`, `SAP_SOHRecs`, `Organizations`
- App bootstrap/config/routing in [app.py](app.py), [config.py](config.py), and [define_routes.py](define_routes.py)

These are tied to this app’s schema and business rules.

---

## Recommended implementation order

### Phase 1: move now
1. `coerce_bool`
2. `cleanupfld`
3. generic spreadsheet upload import helpers
4. async job status helper

### Phase 2: move next
5. model choice-list helper
6. common JS helpers in the template

### Phase 3: leave unless a broader refactor is needed
7. broader model or form abstraction work

---

## Final recommendation

If you want the highest-value extraction with the lowest risk, start with the spreadsheet coercion + import helpers and the async job state model.
Those are the clearest examples of reusable infrastructure and are already in the right shape for a shared library.

The WICS-specific route handlers, summary logic, and domain models should stay local.

---

## Concrete extraction checklist for the first move batch

### A. Move these first

1. `coerce_bool`
   - Best location: `calvincTools.utils`
   - Reason: generic value normalization for imported spreadsheet data

2. `cleanupfld`
   - Best location: `calvincTools.utils` or `calvincTools.excel_imports`
   - Reason: converts raw spreadsheet field values into the correct DB-friendly types

3. `Async progress/status job helper`
   - Best location: `calvincTools.asyncjobs` or a shared job-status utility module
   - Reason: generic progress tracking for long-running background operations

4. Spreadsheet workflow helpers
   - Best location: `calvincTools.excel_imports`
   - Reason: reusable upload/check/column-map/cleanup flow across multiple apps

### B. Suggested shared function names

```python
# calvincTools.utils
coerce_bool(val)
cleanup_field_value(field_name, value, default_epoch=WINDOWS_EPOCH)

# calvincTools.excel_imports
save_uploaded_workbook(request, file_key, target_dir=None)
load_workbook_from_path(path)
validate_required_columns(ws, required_fields)
map_spreadsheet_columns(ws, field_map)
read_uploaded_rows(ws, column_map, row_callback=None)
finalize_import(reqid, async_comm_model, statecode='done', statetext='Finished')

# calvincTools.asyncjobs
get_async_comm_state(reqid)
set_async_comm_state(reqid, statecode, statetext, processname=None, result=None, extra1=None)
delete_async_comm(reqid)

# calvincTools.models or utils
model_choice_list(model, order_by=None, value_attr='id', label_fields=None)
```

### C. Keep these local in WICS4

- Count entry and material form logic
- Count summary reporting
- SAP lookup/reporting logic
- WICS-specific domain classes and table definitions

These are the parts that encode the behavior of this system, not generic utility infrastructure.

### D. Recommended move pattern

- Extract utility functions first
- Move the generic workbook processing next
- Keep the WICS-specific field maps and data model conversion in the app
- Leave business rules and view logic in the app layer

This keeps the shared package small, reusable, and stable while avoiding a premature abstraction of WICS-only logic.
