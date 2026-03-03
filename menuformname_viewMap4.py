# import _newcode
# import views referenced in the FormNameToURL_Map below



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

# FormNameToURL_Map['frmcountentry'.lower()] = ('CountEntryForm', forms.CountEntryForm)
# FormNameToURL_Map['frmUploadCountEntry'.lower()] = ('UploadActualCountSprsht', forms.spreadsheet.UploadActCountSprsht)
# FormNameToURL_Map['frmcountsummarypreview'.lower()] = ('CountSummaryReport', forms.fmActualCounts.rptCountSummary)
# FormNameToURL_Map['frmrequestedcountsummary'.lower()] = ('CountSummaryReport-v-init', None)
# FormNameToURL_Map['frmimportsap'.lower()] = ('UploadSAPSprSht', None)
# FormNameToURL_Map['frmmaterial'.lower()] = ('MatlForm', forms.MaterialForm)
# FormNameToURL_Map['frmmpnlookup'.lower()] = ('MPNLookup', None)
# FormNameToURL_Map['frmParts-By-Type-with-LastCounts'.lower()] = ('MatlByPartType', None)
# FormNameToURL_Map['rptMaterialByLastCount'.lower()] = ('MatlByLastCountDate', None)
# FormNameToURL_Map['rptMaterialByDESCValue'.lower()] = ('MatlByDESCValue', None)
# FormNameToURL_Map['matllistupdt'.lower()] = ('', forms.UpdateMatlListfromSAP)
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
# FormNameToURL_Map['sap'.lower()] = ('showtable-SAP', None)
# FormNameToURL_Map['tblActualCounts'.lower()] = ('ActualCountList', None)
# FormNameToURL_Map['PartTypeFm'.lower()] = ('PartTypeForm', forms.PartTypesForm)


FormNameToURL_Map['test01'.lower()] = ('auth.user_list', None)
FormNameToURL_Map['test02'.lower()] = ('', None)
# FormNameToURL_Map['test02'.lower()] = ('', None)
