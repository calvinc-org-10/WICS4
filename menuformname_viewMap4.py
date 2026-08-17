import _newcode
# import views referenced in the FormNameToURL_Map below
import views



# def LoadAdmin(parent):
def LoadAdmin():
    # return redirect('/admin/')
    return

#########################################################################
#########################################################################


FormNameToURL_Map = {}
# FormNameToURL_Map['menu Argument'.lower()] = (url, view)
# FormNameToURL_Map['l10-wics-uadmin'.lower()] = (None, fnWICSuserForm)
# FormNameToURL_Map['l10-wics-uadmin'.lower()] = (None, None)
# FormNameToURL_Map['l6-wics-uadmin'.lower()] = FormNameToURL_Map['l10-wics-uadmin']
# FormNameToURL_Map['django-admin'.lower()] = (None, LoadAdmin)

FormNameToURL_Map['frmcountentry'.lower()] = (None, views.ActualCounts.fnCountEntryView)
##FormNameToURL_Map['frmcountentry'.lower()] = ('CountEntryForm', _newcode.frmCountEntryView.fnCountEntryView)
# FormNameToURL_Map['frmUploadCountEntry'.lower()] = ('WICS.UploadActualCounts', None)
FormNameToURL_Map['frmUploadCountEntry'.lower()] = (None, views.ActualCounts.upldActCounts.fnUploadActCountSprsht_init)
FormNameToURL_Map['frmcountsummarypreview'.lower()] = ('WICS.CountSummaryReport', None)
FormNameToURL_Map['frmrequestedcountsummary'.lower()] = ('WICS.CountSummaryReport-v-init', None)
# FormNameToURL_Map['frmimportsap'.lower()] = ('UploadSAPSprSht', None)
FormNameToURL_Map['frmmaterial'.lower()] = ('WICS.MaterialForm', None)   # make me work!
# FormNameToURL_Map['frmmpnlookup'.lower()] = ('MPNLookup', None)
# FormNameToURL_Map['frmParts-By-Type-with-LastCounts'.lower()] = ('MatlByPartType', None)
# FormNameToURL_Map['rptMaterialByLastCount'.lower()] = ('MatlByLastCountDate', None)
# FormNameToURL_Map['rptMaterialByDESCValue'.lower()] = ('MatlByDESCValue', None)
# FormNameToURL_Map['matllistupdt'.lower()] = ('UpdateMatlListfromSAP', _newcode.updtMatlList.fnUpdateMatlListfromSAP)
FormNameToURL_Map['matllistupdt'.lower()] = (None, views.Material.updtMatlList.fnUpdateMatlListfromSAP_init)
# FormNameToURL_Map['frmRandCountScheduler'.lower()] = (None, None)

# FormNameToURL_Map['frmCountScheduleEntry'.lower()] = ('CountScheduleForm', forms.CountScheduleRecordForm)
# FormNameToURL_Map['frmRequestCountScheduleEntry'.lower()] = ('RequestCountScheduleForm', None)
# FormNameToURL_Map['frmRequestedCountListEdit'.lower()] = ('RequestCountListEdit', None)
# FormNameToURL_Map['frmUploadCountSched'.lower()] = ('UploadCountSchedSprsht', None)
# FormNameToURL_Map['frmcount-schedulehistory-by-counterdate'.lower()] = ('CountScheduleList', None)
# FormNameToURL_Map['rptCountWorksheet'.lower()] = ('CountWorksheet', None)
# FormNameToURL_Map['rptCountWorksheetLoc'.lower()] = ('CountWorksheetLoc', None)
# FormNameToURL_Map['rptMaterialLocations'.lower()] = ('MaterialLocations', None)
# FormNameToURL_Map['LocationList'.lower()] = ('LocationList', None)
# FormNameToURL_Map['sap'.lower()] = (None, views.SAP.procs_SAP.fnShowSAP)
FormNameToURL_Map['sap'.lower()] = ('WICS.showtable-SAP', None)
# FormNameToURL_Map['tblActualCounts'.lower()] = ('ActualCountList', None)
# FormNameToURL_Map['PartTypeFm'.lower()] = ('PartTypeForm', forms.PartTypesForm)


FormNameToURL_Map['test01'.lower()] = ('', _newcode.test_xl_read.test_read)
FormNameToURL_Map['test02'.lower()] = ('', None)
# FormNameToURL_Map['test02'.lower()] = ('', None)
