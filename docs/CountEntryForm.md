## <u>Components</u>

### <u>frmCountEntryView.py</u>
    def fnCountEntryView( 
            recNum = None, MatlNum = None, reqDate = None,
            gotoCommand = None
            ):

### <u>CountEntryForm.py</u>
(WTF-Flask forms)   <br>

    class CountEntryForm
    class RelatedMaterialInfo
    class RelatedScheduleInfo

### <u>frm_CountEntry.html</u>

<hr style="height:15px;">

## <u>Routes</u>
(_CountEntryForm_ is GET and POST, all others are GET only) <br>
__CountEntryForm:__ /CountEntryForm <br>
__CountEntryFormGo:__ /CountEntryForm/Go/\<int:recNum>   <br>
__CountEntryFormGo_Command:__ /CountEntryForm/Go/\<int:recNum>/\<string:gotoCommand>   <br>
__CountEntryForm_ChgKey:__ /CountEntryForm/\<int:recNum>/\<string:reqDate>/\<string:MatlNum> <br>

<div style="page-break-after: always;"></div>

## <u>Behavior of _fnCountEntryView_</u>
    if request.method == 'POST':
        extract reqDate, recNum, MatlNum from POST
        currRec = get(recNum)
        compare POST with currRec, document changes
            # NOTE: reqDate, MatlNum MAY BE DIFFERENT!!
        write POST record
        present new record (like GET, gotoCommand=NEW)
    else: (req.method == GET)
        if recNum == None:
            currRec = get(recNum)
        else:
            currRec = empty record
        endif recNum == None
        if reqDate == None:
            reqDate = today
        endif reqDate == None
        currRec.CountDate = reqDate
        if MatlNum is not Null and MatlNum != currRec.Material_id:
            currRec.Material_id = MatlNum
            currRec.Material = get(MatlNum)
        endif MatlNum different
        # NOTE: DO NOT save currRec, even if changed, save that for the POST
        if gotoCommand is None:
            noop, but s/b be present because None is valid
        elif gotoCommand == 'ChgKey':
            reqDate / MatlNum already changed above
        elif gotoCommand == 'New':
            currRec = empty record
        elif gotoCommand == 'First':
            ...
        elif gotoCommand == 'Last':
            ...
        elif gotoCommand == 'Prev':
            ...
        elif gotoCommand == 'Next':
            ...
        else:
            Invalid gotoCommand value
        endif gotoCommand
    endif req.method == POST

    prepare scheduled count records, scheduled today flag
    prepare other context variables

    handoff to html
