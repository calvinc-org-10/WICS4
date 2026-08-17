import os
from typing import cast, Any

from flask import current_app
from flask_login import login_required

from sqlalchemy import select, text

from calvincTools.mathexpr_parser import evaluate
from calvincTools.utils import (
    coerce_date, IsDateString, 
    WrapInQuotes, 
    Excelfile_fromqs, ExcelWorkbook_fileext,
    checkTemplate_and_render,    
    )

from database import app_db
from models import Organizations, ActualCounts, CountSchedule

from views.SAP import fnSAPList


#####################################################################
#####################################################################
#####################################################################

# add this to cMenu.utils later
def coerce_float(x) -> float:
    if isinstance(x,(float, int)):
        return float(x)
    if isinstance(x,str) and x.isnumeric():
        return float(x)

    return 0.0

@login_required
def fnCountSummaryReqRpt(passedCountDate='CURRENT_DATE'):
    return fnCountSummaryRpt(passedCountDate, Rptvariation='REQ')
@login_required
def fnCountSummaryRpt (passedCountDate='CURRENT_DATE', Rptvariation=None):

    # get the SAP data
    dtobj_pDate = coerce_date(passedCountDate)
    SAP_SOH = fnSAPList(dtobj_pDate)

    ## construct list of dates counts actually occurred, for use in the dropdown on the report page, and to find the most recent date if passedCountDate is 'CURRENT_DATE'
    stmt = select(ActualCounts.CountDate).distinct().order_by(ActualCounts.CountDate.desc())
    countDatesRaw = app_db.session.execute(stmt).scalars().all()
    _myDtFmt = current_app.config.get('DEFAULT_DATEFORMAT', '%Y-%m-%d')
    countDates = [D.strftime(_myDtFmt) for D in countDatesRaw]
    # correct dtobj_pDate to the most recent date in countDatesRaw <= passedCountDate
    dtobj_pDate = [D for D in countDatesRaw if D <= dtobj_pDate][0] if countDatesRaw else dtobj_pDate

    # prep Excel_qdict.  It's up here so that the functions below have access to it
    Excel_qdict = []

    def CreateOutputRows(raw_qs, Eval_CTDQTY=True):
        def SummaryLine(lastrow):
            # summarize last Matl
            # total SAP Numbers
            SAPTot = 0
            outputline = dict()
            outputline['type'] = 'Summary'
            outputline['SAPNum'] = []
            for SAProw in [saprow for saprow in SAP_SOH['SAPTable'] if saprow.Material_id==lastrow['Material_id']]:
                outputline['SAPNum'].append((SAProw.StorageLocation, format(SAProw.Amount,".2f"), SAProw.BaseUnitofMeasure))
                SAPTot += SAProw.Amount*SAProw.mult
            outputline['TypicalContainerQty'] = lastrow['TypicalContainerQty']
            outputline['TypicalPalletQty'] = lastrow['TypicalPalletQty']
            outputline['OrgName'] = lastrow['OrgName']
            outputline['Material'] = lastrow['Material']
            outputline['Material_id'] = lastrow['Material_id']
            outputline['Description'] = lastrow['Description']
            outputline['SchedCounter'] = lastrow['SchedCounter']
            outputline['Counters'] = lastrow['Counters']
            outputline['Requestor'] = lastrow['Requestor']
            outputline['RequestFilled'] = lastrow['RequestFilled']
            outputline['PartType'] = lastrow['PartType']
            outputline['CountTotal'] = lastrow['TotalCounted']
            outputline['SAPTotal'] = int(SAPTot)
            outputline['Diff'] = int(lastrow['TotalCounted'] - SAPTot)
            divsr = 1
            if lastrow['TotalCounted']!=0 or SAPTot!=0: divsr = max(lastrow['TotalCounted'], SAPTot)
            outputline['Accuracy'] = min(lastrow['TotalCounted'], SAPTot) / divsr * 100
            outputline['ReasonScheduled'] = lastrow['ReasonScheduled']
            outputline['SchedNotes'] = lastrow['SchedNotes']
            outputline['MatlNotes'] = lastrow['MatlNotes']
            #outputrows.append(outputline)

            return outputline
        # end def SummaryLine

        def CreateLastrow(rawrow):
            lastrow = dict()
            lastrow['OrgName'] = rawrow.OrgName
            lastrow['Material'] = rawrow.Matl_PartNum
            lastrow['Material_id'] = rawrow.matl_id
            lastrow['Description'] = rawrow.Description
            lastrow['SchedCounter'] = rawrow.cs_Counter
            lastrow['Counters'] = rawrow.ac_Counter if rawrow.ac_Counter is not None else ''
            lastrow['Requestor'] = rawrow.Requestor
            lastrow['RequestFilled'] = rawrow.RequestFilled
            lastrow['PartType'] = rawrow.PartType
            lastrow['TotalCounted'] = 0
            lastrow['SchedNotes'] = rawrow.cs_Notes
            lastrow['TypicalContainerQty'] = rawrow.TypicalContainerQty
            lastrow['TypicalPalletQty'] = rawrow.TypicalPalletQty
            lastrow['MatlNotes'] = rawrow.mtl_Notes
            lastrow['ReasonScheduled'] = rawrow.cs_ReasonScheduled

            return lastrow
        # end def CreateLastRow

        def DetailLine(rawrow, Eval_CTDQTY=True):
            outputline = dict()
            outputline['type'] = 'Detail'
            outputline['CycCtID'] = rawrow.ac_CycCtID
            outputline['Material'] = rawrow.Matl_PartNum
            outputline['Material_id'] = rawrow.matl_id
            outputline['org_id'] = rawrow.org_id
            outputline['orgName'] = rawrow.OrgName
            outputline['ActCounter'] = rawrow.ac_Counter
            if rawrow.ac_Counter is not None and rawrow.ac_Counter not in lastrow['Counters']:
                lastrow['Counters'] += ', ' + rawrow.ac_Counter
            outputline['LOCATION'] = rawrow.ac_LOCATION
            outputline['PKGID'] = rawrow.ac_PKGID_Desc
            outputline['TAGQTY'] = rawrow.ac_TAGQTY
            outputline['PossNotRec'] = rawrow.FLAG_PossiblyNotRecieved
            outputline['MovDurCt'] = rawrow.FLAG_MovementDuringCount
            outputline['CTD_QTY_Expr'] = rawrow.ac_CTD_QTY_Expr
            if Eval_CTDQTY:
                try:
                    outputline['CTD_QTY_Eval'] = evaluate(rawrow.ac_CTD_QTY_Expr)
                    # do next line at caller
                    # lastrow['TotalCounted'] += outputline['CTD_QTY_Eval']
                except:
                    # Exception('bad expression:'+rawrow.ac_CTD_QTY_Expr)
                    outputline['CTD_QTY_Eval'] = "????"
            else:
                outputline['CTD_QTY_Eval'] = "----"
            outputline['ActCountNotes'] = rawrow.ac_Notes
            # outputrows.append(outputline)

            return outputline
        #end def DetailLine

        outputrows = []
        lastrow:dict[str, Any] = {'Material_id': None}
        for rawrow in raw_qs:
            if rawrow.matl_id != lastrow['Material_id']:     # new Matl
                if outputrows:
                    SmLine = SummaryLine(lastrow)
                    outputrows.append(SmLine)
                    Excel_qdict.append(
                        {key:SmLine[key]
                          for key in ['OrgName','Material','PartType','Description','CountTotal','SAPTotal','Diff','Accuracy','Counters']
                        })
                # no else -  if outputrows is empty, this is the first row, so keep going

                # this new material is now the "old" one; save values for when it switches, and we do the above block
                # this whole block becomes
                lastrow = CreateLastrow(rawrow)
            #endif

            # process this row
            outputline = DetailLine(rawrow, Eval_CTDQTY)
            outputrows.append(outputline)
            if isinstance(outputline['CTD_QTY_Eval'],(int,float)): 
                lastrow['TotalCounted'] += outputline['CTD_QTY_Eval']
        # endfor
        # need to do the summary on the last row
        if outputrows:
            # summarize last Matl
            SmLine = SummaryLine(lastrow)
            outputrows.append(SmLine)
            Excel_qdict.append(
                {key:SmLine[key]
                    for key in ['OrgName','Material','PartType','Description','CountTotal','SAPTotal','Diff','Accuracy','Counters']
                })

        return outputrows
    #end def CreateOutputRows

    ### main body of fnCountSummaryRpt

    SummaryReport = []

    fldlist = "0 as id, cs.id as cs_id, cs.CountDate as cs_CountDate , cs.Counter as cs_Counter" \
        ", cs.Priority as cs_Priority, cs.ReasonScheduled as cs_ReasonScheduled" \
        ", cs.Requestor, cs.RequestFilled" \
        ", cs.Notes as cs_Notes" \
        ", ac.id as ac_id, ac.CountDate as ac_CountDate, ac.CycCtID as ac_CycCtID, ac.Counter as ac_Counter" \
        ", ac.LocationOnly as ac_LocationOnly, ac.CTD_QTY_Expr as ac_CTD_QTY_Expr" \
        ", ac.LOCATION as ac_LOCATION, ac.PKGID_Desc as ac_PKGID_Desc, ac.TAGQTY as ac_TAGQTY" \
        ", ac.FLAG_PossiblyNotRecieved, ac.FLAG_MovementDuringCount, ac.Notes as ac_Notes" \
        ", mtl.id as matl_id, mtl.org_id, mtl.OrgName" \
        ", mtl.Material_org as Matl_PartNum, mtl.PartType as PartType" \
        ", mtl.Description, mtl.TypicalContainerQty, mtl.TypicalPalletQty, mtl.Notes as mtl_Notes"
    datestr = WrapInQuotes(str(dtobj_pDate),"'","'")
    date_condition = '(ac.CountDate = ' + datestr + ' OR cs.CountDate = ' + datestr + ') '
    order_by = 'Matl_PartNum'

    VIEW_Material_sql = "VIEW_materials mtl "

    stmt = select(Organizations).order_by(Organizations.orgname)
    all_orgs = app_db.session.execute(stmt).scalars().all()
    for org in all_orgs:
        # group by org_id
        org_condition = '(mtl.org_id = ' + str(org.id) + ')'

        A_Sched_Ctd_from = 'WICS_countschedule cs INNER JOIN ' + VIEW_Material_sql
        A_Sched_Ctd_from += ' INNER JOIN (SELECT * FROM WICS_actualcounts WHERE not LocationOnly) ac '
        A_Sched_Ctd_joinon = ' cs.CountDate=ac.CountDate AND cs.Material_id=ac.Material_id AND ac.Material_id=mtl.id'
        A_Sched_Ctd_where = ''
        if Rptvariation == 'REQ':
            if A_Sched_Ctd_where:  A_Sched_Ctd_where += ' AND '
            A_Sched_Ctd_where += 'Requestor IS NOT NULL'
        A_Sched_Ctd_sql = 'SELECT ' + fldlist + \
            ' FROM ' + A_Sched_Ctd_from + \
            ' ON ' + A_Sched_Ctd_joinon + \
            ' WHERE NOT ac.LocationOnly AND ' + date_condition + ' AND ' + org_condition
        if A_Sched_Ctd_where:
            A_Sched_Ctd_sql += ' AND ' + A_Sched_Ctd_where
        A_Sched_Ctd_sql += ' ORDER BY ' + order_by
        A_Sched_Ctd_qs = app_db.session.execute(text(A_Sched_Ctd_sql)).all()
        # build display lines
        ttl = 'Scheduled and Counted'
        if Rptvariation == 'REQ':
            ttl = 'Requested and Counted'
        SummaryReport.append({
                    'org':org,
                    'Title':ttl,
                    'outputrows': CreateOutputRows(A_Sched_Ctd_qs)
                    })

        if Rptvariation is None:
            B_UnSched_Ctd_from = 'WICS_countschedule cs RIGHT JOIN' \
                ' ((SELECT * FROM WICS_actualcounts WHERE not LocationOnly) ac INNER JOIN ' + VIEW_Material_sql + ' ON ac.Material_id=mtl.id)'
            B_UnSched_Ctd_joinon = 'cs.CountDate=ac.CountDate AND cs.Material_id=ac.Material_id'
            B_UnSched_Ctd_where = '(cs.id IS NULL)'
            B_UnSched_Ctd_sql = 'SELECT ' + fldlist + ' ' + \
                ' FROM ' + B_UnSched_Ctd_from + \
                ' ON ' + B_UnSched_Ctd_joinon + \
                ' WHERE NOT ac.LocationOnly AND ' + date_condition + ' AND ' + org_condition + \
                ' AND ' + B_UnSched_Ctd_where + \
                ' ORDER BY ' + order_by
            B_UnSched_Ctd_qs = app_db.session.execute(text(B_UnSched_Ctd_sql)).all()
            SummaryReport.append({
                        'org':org,
                        'Title':'UnScheduled',
                        'outputrows': CreateOutputRows(B_UnSched_Ctd_qs)
                        })

        C_Sched_NotCtd_Ctd_from = '(WICS_countschedule cs INNER JOIN ' + VIEW_Material_sql + ' ON cs.Material_id=mtl.id)'
        C_Sched_NotCtd_Ctd_from += ' LEFT JOIN (SELECT * FROM WICS_actualcounts WHERE not LocationOnly) ac '
        C_Sched_NotCtd_Ctd_joinon = 'cs.CountDate=ac.CountDate AND cs.Material_id=ac.Material_id'
        C_Sched_NotCtd_Ctd_where = '(ac.id IS NULL)'
        if Rptvariation == 'REQ':
            if C_Sched_NotCtd_Ctd_where:  C_Sched_NotCtd_Ctd_where += ' AND '
            C_Sched_NotCtd_Ctd_where += '(Requestor IS NOT NULL)'
        C_Sched_NotCtd_Ctd_sql = 'SELECT ' + fldlist + ' ' + \
            ' FROM ' + C_Sched_NotCtd_Ctd_from + \
            ' ON ' + C_Sched_NotCtd_Ctd_joinon + \
            ' WHERE ' + date_condition + ' AND ' + org_condition
        if C_Sched_NotCtd_Ctd_where:
            C_Sched_NotCtd_Ctd_sql += ' AND ' + C_Sched_NotCtd_Ctd_where
        C_Sched_NotCtd_Ctd_sql += ' ORDER BY ' + order_by
        C_Sched_NotCtd_Ctd_qs = app_db.session.execute(text(C_Sched_NotCtd_Ctd_sql)).all()
        ttl = 'Scheduled but Not Counted'
        if Rptvariation == 'REQ':
            ttl = 'Requested but Not Counted'
        SummaryReport.append({
                    'org':org,
                    'Title':ttl,
                    'outputrows': CreateOutputRows(C_Sched_NotCtd_Ctd_qs, Eval_CTDQTY=False)
                    })

    AccuracyCutoff = {
                'DANGER': coerce_float(current_app.config.get('ACCURACY-DANGER', 90)),
                'SUCCESS': coerce_float(current_app.config.get('ACCURACY-SUCCESS',97)),
                'WARNING': coerce_float(current_app.config.get('ACCURACY-WARNING',95)),
                }

    ExcelFileNamePrefix = "CountSummary "
    svdir = current_app.config.get('SAP_FILELOC', os.getcwd())
    os.makedirs(svdir+'tmpdl', exist_ok=True)
    fName_base = 'tmpdl/'+ExcelFileNamePrefix + f'{dtobj_pDate:%Y-%m-%d}'
    fName = svdir + fName_base
    ExcelFileName = Excelfile_fromqs(Excel_qdict, fName)

    # display the form
    cntext = {
            'variation': Rptvariation,
            'CountDateList': countDates,
            'CountDate': dtobj_pDate,
            'SAPDate': SAP_SOH['SAPDate'],
            'AccuracyCutoff': AccuracyCutoff,
            'SummaryReport': SummaryReport,
            'FilSavLoc': ExcelFileName,
            'ExcelFileName': fName_base+ExcelWorkbook_fileext,
            }
    templt = 'ActualCounts/rpt_CountSummary.html'
    return checkTemplate_and_render(templt, **cntext)

