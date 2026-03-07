
####################################################################################
####################################################################################
####################################################################################

##### the suite of procs to support fnUpdateMatlListfromSAP

def proc_MatlListSAPSprsheet_00InitUMLasync_comm(dbToUse, reqid, UpdateExistFldList):
    acomm = set_async_comm_state(
        dbToUse,
        reqid,
        statecode = 'rdng-sprsht-init',
        statetext = 'Initializing ...',
        new_async=True
        )
    set_async_comm_state(
        dbToUse, 
        f'{reqid}-UpdExstFldList',
        statecode = 'UpdateExistFldList',
        statetext = f'{UpdateExistFldList}',
        new_async=True
        )

def proc_MatlListSAPSprsheet_00CopyUMLSpreadsheet(req, reqid):
    dbToUse = user_db(req)
    acomm = set_async_comm_state(
        dbToUse,
        reqid,
        statecode = 'uploading-sprsht',
        statetext = 'Uploading Spreadsheet',
        )

    SAPFile = req.FILES['SAPFile']
    svdir = getcParm(req, 'SAP-FILELOC')
    fName = svdir+"tmpMatlList"+str(uuid.uuid4())+ExcelWorkbook_fileext
    with open(fName, "wb") as destination:
        for chunk in SAPFile.chunks():
            destination.write(chunk)

    return fName

def proc_MatlListSAPSprsheet_01ReadSpreadsheet(dbToUse, reqid, fName):
    acomm = set_async_comm_state(
        dbToUse, 
        reqid,
        statecode = 'rdng-sprsht',
        statetext = 'Reading Spreadsheet',
        )

    tmpMaterialListUpdate.objects.using(dbToUse).all().delete()

    wb = load_workbook(filename=fName, read_only=True)
    ws = wb.active
    SAPcolmnNames = ws[1]
    SAPcol = {'Plant':None,'Material': None}
    SAP_SSName_TableName_map = {
            'Material': 'Material',
            'Material description': 'Description',
            'Plant': 'Plant', 'Plnt': 'Plant',
            'Material type': 'SAPMaterialType',  'MTyp': 'SAPMaterialType',
            'Material Group': 'SAPMaterialGroup', 'Matl Group': 'SAPMaterialGroup',
            'Manufact.': 'SAPManuf', 
            'MPN': 'SAPMPN', 
            'ABC': 'SAPABC', 
            'Price': 'Price', 'Standard price': 'Price',
            'Price unit': 'PriceUnit', 'per': 'PriceUnit',
            'Currency':'Currency',
            }
    for col in SAPcolmnNames:
        if col.value in SAP_SSName_TableName_map:
            SAPcol[SAP_SSName_TableName_map[col.value]] = col.column - 1
    if (SAPcol['Material'] == None or SAPcol['Plant'] == None):
        set_async_comm_state(
            dbToUse,
            reqid,
            statecode = 'fatalerr',
            statetext = 'SAP Spreadsheet has bad header row. Plant and/or Material is missing.  See Calvin to fix this.',
            result = 'FAIL - bad spreadsheet',
            )

        wb.close()
        os.remove(fName)
        return

    numrows = ws.max_row
    nRows = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        nRows += 1
        if nRows % 100 == 0:
            set_async_comm_state(
                dbToUse,
                reqid,
                statecode = 'rdng-sprsht',
                statetext = f'Reading Spreadsheet ... record {nRows} of {numrows}<br><progress max="{numrows}" value="{nRows}"></progress>',
                )

        if row[SAPcol['Material']]==None: MatNum = ''
        else: MatNum = row[SAPcol['Material']]
        validTmpRec = False
        ## create a blank tmpMaterialListUpdate record,
        newrec = tmpMaterialListUpdate()
        if regex.match(".*[\n\t\xA0].*",MatNum):
            validTmpRec = True
            ## refuse to work with special chars embedded in the MatNum
            newrec.recStatus = 'err-MatlNum'
            newrec.errmsg = f'error: {MatNum!a} is an unusable part number. It contains invalid characters and cannot be added to WICS'
        elif len(str(MatNum)):
            validTmpRec = True
            _org = SAPPlants_org.objects.using(dbToUse).filter(SAPPlant=row[SAPcol['Plant']])[0].org        #TODO: handle empty table
            newrec.org = _org
        # endif invalid Material
        if validTmpRec:
            ## populate by looping through SAPcol,
            ## then save
            for dbColName, ssColNum in SAPcol.items():
                setattr(newrec,dbColName,row[ssColNum])
            newrec.save(using=dbToUse)
    # endfor

    wb.close()
    os.remove(fName)
def done_MatlListSAPSprsheet_01ReadSpreadsheet(t):
    dbToUse = t.args[0]
    reqid = t.args[1]
    statecode = async_comm.objects.using(dbToUse).get(pk=reqid).statecode
    #DOITNOW!!! handle not t.success, t.result
    if statecode != 'fatalerr':
        set_async_comm_state(
            dbToUse,
            reqid,
            statecode = 'done-rdng-sprsht',
            statetext = f'Finished Reading Spreadsheet',
            )
        proc_MatlListSAPSprsheet_02_identifyexistingMaterial(dbToUse, reqid)

def proc_MatlListSAPSprsheet_02_identifyexistingMaterial(dbToUse, reqid):
    set_async_comm_state(
        dbToUse,
        reqid,
        statecode = 'get-matl-link',
        statetext = f'Finding SAP MM60 Materials already in WICS Material List',
        )
    UpdMaterialLinkSQL = 'UPDATE WICS_tmpmateriallistupdate, (select id, org_id, Material from WICS_materiallist) as MasterMaterials'
    UpdMaterialLinkSQL += ' set WICS_tmpmateriallistupdate.MaterialLink_id = MasterMaterials.id, '
    UpdMaterialLinkSQL += "     WICS_tmpmateriallistupdate.recStatus = 'FOUND' "
    UpdMaterialLinkSQL += ' where WICS_tmpmateriallistupdate.org_id = MasterMaterials.org_id '
    UpdMaterialLinkSQL += '   and WICS_tmpmateriallistupdate.Material = MasterMaterials.Material '
    with connections[dbToUse].cursor() as cursor:
        cursor.execute(UpdMaterialLinkSQL)

    set_async_comm_state(
        dbToUse,
        reqid,
        statecode = 'id-del-matl',
        statetext = f'Identifying WICS Materials no longer in SAP MM60 Materials',
        )
    MustKeepMatlsSelCond = ''
    MustKeepMatlsSelCond += ' AND ' if MustKeepMatlsSelCond else ''
    MustKeepMatlsSelCond += 'id NOT IN (SELECT DISTINCT tmucopy.MaterialLink_id AS Material_id FROM WICS_tmpmateriallistupdate tmucopy WHERE tmucopy.MaterialLink_id IS NOT NULL)'
    MustKeepMatlsSelCond += ' AND ' if MustKeepMatlsSelCond else ''
    MustKeepMatlsSelCond += 'id NOT IN (SELECT DISTINCT Material_id FROM WICS_actualcounts)'
    MustKeepMatlsSelCond += ' AND ' if MustKeepMatlsSelCond else ''
    MustKeepMatlsSelCond += 'id NOT IN (SELECT DISTINCT Material_id FROM WICS_countschedule)'
    MustKeepMatlsSelCond += ' AND ' if MustKeepMatlsSelCond else ''
    MustKeepMatlsSelCond += 'id NOT IN (SELECT DISTINCT Material_id FROM WICS_sap_sohrecs)'

    DeleteMatlsSelectSQL = "INSERT INTO WICS_tmpmateriallistupdate (recStatus, delMaterialLink, MaterialLink_id, org_id, Material, Description, Plant "
    DeleteMatlsSelectSQL += ", SAPMaterialType, SAPMaterialGroup, Currency  ) "    # these can go once I set null=True on these fields
    DeleteMatlsSelectSQL += " SELECT  concat('DEL ',FORMAT(id,0)), id, NULL, org_id, Material, Description, Plant "
    DeleteMatlsSelectSQL += ", SAPMaterialType, SAPMaterialGroup, Currency  "    # these can go once I set null=True on these fields
    DeleteMatlsSelectSQL += " FROM WICS_materiallist"
    DeleteMatlsSelectSQL += f" WHERE ({MustKeepMatlsSelCond})"
    with connections[dbToUse].cursor() as cursor:
        cursor.execute(DeleteMatlsSelectSQL)

    set_async_comm_state(
        dbToUse,
        reqid,
        statecode = 'id-add-matl',
        statetext = f'Identifying SAP MM60 Materials new to WICS',
        )
    MarkAddMatlsSelectSQL = "UPDATE WICS_tmpmateriallistupdate"
    MarkAddMatlsSelectSQL += " SET recStatus = 'ADD'"
    MarkAddMatlsSelectSQL += " WHERE (MaterialLink_id IS NULL) AND (recStatus is NULL)"
    with connections[dbToUse].cursor() as cursor:
        cursor.execute(MarkAddMatlsSelectSQL)
        transaction.on_commit(partial(done_MatlListSAPSprsheet_02_identifyexistingMaterial,dbToUse,reqid))
def done_MatlListSAPSprsheet_02_identifyexistingMaterial(dbToUse, reqid):
    set_async_comm_state(
        dbToUse,
        reqid,
        statecode = 'get-matl-link-done',
        statetext = f'Finished linking SAP MM60 list to existing WICS Materials',
        )
    
    proc_MatlListSAPSprsheet_03_UpdateExistingRecs(dbToUse, reqid)

def proc_MatlListSAPSprsheet_03_UpdateExistingRecs(dbToUse, reqid):
    def setstate_MatlListSAPSprsheet_03_UpdateExistingRecs(dbToUse, fldName):
        acomm = set_async_comm_state(
            dbToUse,
            reqid,
            statecode = 'upd-existing-recs',
            statetext = f'Updating _{fldName}_ Field in Existing Records',
            )

    setstate_MatlListSAPSprsheet_03_UpdateExistingRecs(dbToUse, '')

    # (Form Name, db fld Name, zero/blank value)
    FormTodbFld_map = [
        ('Description','Description','""'),
        ('SAPMatlType','SAPMaterialType','""'),
        ('SAPMatlGroup','SAPMaterialGroup','""'),
        ('SAPManuf','SAPManuf','""'),
        ('SAPMPN','SAPMPN','""'),
        ('SAPABC','SAPABC','""'),
        ('SAPPrice','Price',0),
        ('SAPPrice','PriceUnit',0),
        ('SAPPrice','Currency','""'),
    ]

    UpdateExistFldList_str = async_comm.objects.using(dbToUse).get(pk=f"{reqid}-UpdExstFldList").statetext
    UpdateExistFldList = ast.literal_eval(UpdateExistFldList_str)

    if UpdateExistFldList:
        for formName, dbName, zeroVal in FormTodbFld_map:
            if formName in UpdateExistFldList:
                setstate_MatlListSAPSprsheet_03_UpdateExistingRecs(dbToUse, dbName)
                # UPDATE this field
                UpdSQLSetStmt = f"MatlList.{dbName}=tmpMatl.{dbName}"
                UpdSQLWhereStmt = f"(IFNULL(tmpMatl.{dbName},{zeroVal}) != {zeroVal} AND IFNULL(MatlList.{dbName},{zeroVal})!=IFNULL(tmpMatl.{dbName},{zeroVal}))"

                UpdSQLStmt = "UPDATE WICS_materiallist AS MatlList, WICS_tmpmateriallistupdate AS tmpMatl"
                UpdSQLStmt += f" SET {UpdSQLSetStmt}"
                UpdSQLStmt += f" WHERE (tmpMatl.MaterialLink_id=MatlList.id) AND {UpdSQLWhereStmt}"
                with connections[dbToUse].cursor() as cursor:
                    cursor.execute(UpdSQLStmt)
            #endif formName in UpdateExistFldList
        #endfor
    # endif UpdateExistFldList not empty
    done_MatlListSAPSprsheet_03_UpdateExistingRecs(dbToUse, reqid)
def done_MatlListSAPSprsheet_03_UpdateExistingRecs(dbToUse, reqid):
    set_async_comm_state(
        dbToUse,
        reqid,
        statecode = 'upd-existing-recs-done',
        statetext = f'Finished Updating Existing Records to MM60 values',
        )
    proc_MatlListSAPSprsheet_04_Remove(dbToUse, reqid)

def proc_MatlListSAPSprsheet_04_Remove(dbToUse, reqid):
    ## MustKeepMatlsDelCond = ''
    ## if MustKeepMatlsDelCond: MustKeepMatlsDelCond += ' AND '
    ## MustKeepMatlsDelCond += 'id IN (SELECT DISTINCT delMaterialLink FROM WICS_tmpmateriallistupdate WHERE recStatus like "DEL%")'

    set_async_comm_state(
        dbToUse,
        reqid,
        statecode = 'del-matl',
        statetext = f'Removing WICS Materials no longer in SAP MM60 Materials',
        )
    # do the Removals
    ## DeleteMatlsDoitSQL = "DELETE FROM WICS_materiallist"
    ## DeleteMatlsDoitSQL += f" WHERE ({MustKeepMatlsDelCond})"
    DeleteMatlsDoitSQL = 'DELETE MATL'
    DeleteMatlsDoitSQL += ' FROM WICS_materiallist AS MATL INNER JOIN WICS_tmpmateriallistupdate AS TMP'
    DeleteMatlsDoitSQL += '    ON MATL.id = TMP.delMaterialLink'
    DeleteMatlsDoitSQL += ' WHERE TMP.recStatus like "DEL%"'
    with connections[dbToUse].cursor() as cursor:
        cursor.execute(DeleteMatlsDoitSQL)
        transaction.on_commit(partial(done_MatlListSAPSprsheet_04_Remove,dbToUse,reqid))
def done_MatlListSAPSprsheet_04_Remove(dbToUse,reqid):
    mandatorytaskdonekey = f'MatlX{reqid}'
    statecodeVal = ".03D."
    existingstatecode = ''
    if async_comm.objects.using(dbToUse).filter(pk=mandatorytaskdonekey).exists(): existingstatecode = async_comm.objects.using(dbToUse).get(pk=mandatorytaskdonekey).statecode
    MatlXval = existingstatecode + statecodeVal
    set_async_comm_state(
        dbToUse,
        mandatorytaskdonekey,
        statecode = MatlXval,
        statetext = '',
        new_async = True
        )
    set_async_comm_state(
        dbToUse,
        reqid,
        statecode = 'done-del-matl',
        statetext = f'Finished Removing WICS Materials no longer in SAP MM60 Materials',
        )
    proc_MatlListSAPSprsheet_04_Add(dbToUse, reqid)

def proc_MatlListSAPSprsheet_04_Add(dbToUse, reqid):
    set_async_comm_state(
        dbToUse,
        reqid,
        statecode = 'add-matl',
        statetext = f'Adding SAP MM60 Materials new to WICS',
        )
    UnknownTypeID = WhsePartTypes.objects.using(dbToUse).get(WhsePartType=WICS.globals._PartTypeName_UNKNOWN)
    # do the adds
    # one day django will implement insert ... select.  Until then ...
    AddMatlsSelectSQL = "SELECT"
    AddMatlsSelectSQL += " org_id, Material, Description, Plant, " + str(UnknownTypeID.pk) + " AS PartType_id,"
    AddMatlsSelectSQL += " SAPMaterialType, SAPMaterialGroup, Price, PriceUnit, Currency,"
    AddMatlsSelectSQL += " '' AS TypicalContainerQty, '' AS TypicalPalletQty, '' AS Notes"
    AddMatlsSelectSQL += " FROM WICS_tmpmateriallistupdate"
    AddMatlsSelectSQL += " WHERE (MaterialLink_id IS NULL) AND (recStatus = 'ADD') "

    AddMatlsDoitSQL = "INSERT INTO WICS_materiallist"
    AddMatlsDoitSQL += " (org_id, Material, Description, Plant, PartType_id,"
    AddMatlsDoitSQL += " SAPMaterialType, SAPMaterialGroup, Price, PriceUnit, Currency,"
    AddMatlsDoitSQL += " TypicalContainerQty, TypicalPalletQty, Notes)"
    AddMatlsDoitSQL += " " + AddMatlsSelectSQL
    with connections[dbToUse].cursor() as cursor:
        cursor.execute(AddMatlsDoitSQL)

    set_async_comm_state(
        dbToUse,
        reqid,
        statecode = 'add-matl-get-recid',
        statetext = f'Getting Record ids of SAP MM60 Materials new to WICS',
        )
    UpdMaterialLinkSQL = 'UPDATE WICS_tmpmateriallistupdate, (select id, org_id, Material from WICS_materiallist) as MasterMaterials'
    UpdMaterialLinkSQL += ' set WICS_tmpmateriallistupdate.MaterialLink_id = MasterMaterials.id '
    UpdMaterialLinkSQL += ' where WICS_tmpmateriallistupdate.org_id = MasterMaterials.org_id '
    UpdMaterialLinkSQL += '   and WICS_tmpmateriallistupdate.Material = MasterMaterials.Material '
    UpdMaterialLinkSQL += "   and (MaterialLink_id IS NULL) AND (recStatus = 'ADD')"
    with connections[dbToUse].cursor() as cursor:
        cursor.execute(UpdMaterialLinkSQL)
        transaction.on_commit(partial(done_MatlListSAPSprsheet_04_Add,dbToUse,reqid))
def done_MatlListSAPSprsheet_04_Add(dbToUse, reqid):
    mandatorytaskdonekey = f'MatlX{reqid}'
    statecodeVal = ".03A."
    existingstatecode = ''
    if async_comm.objects.using(dbToUse).filter(pk=mandatorytaskdonekey).exists(): existingstatecode = async_comm.objects.using(dbToUse).get(pk=mandatorytaskdonekey).statecode
    MatlXval = existingstatecode + statecodeVal
    set_async_comm_state(
        dbToUse,
        mandatorytaskdonekey,
        statecode = MatlXval,
        statetext = '',
        new_async = True
        )
    set_async_comm_state(
        dbToUse,
        reqid,
        statecode = 'done-add-matl',
        statetext = f'Finished Adding SAP MM60 Materials new to WICS',
        )

def proc_MatlListSAPSprsheet_99_FinalProc(dbToUse, reqid):
    set_async_comm_state(
        dbToUse,
        reqid,
        statecode = 'done',
        statetext = 'Finished Processing Spreadsheet',
        )
    
def proc_MatlListSAPSprsheet_99_Cleanup(dbToUse, reqid):
    # also kill reqid, acomm, qcluster process
    async_comm.objects.using(dbToUse).filter(pk=reqid).delete()
    async_comm.objects.using(dbToUse).filter(pk=f"{reqid}-UpdExstFldList").delete()

    # when we can start django-q programmatically, this is where we kill that process
    try:
        os.kill(int(reqid), signal.SIGTERM)
    except AttributeError:
        pass
    try:
        os.kill(int(reqid), signal.SIGKILL)
    except AttributeError:
        pass

    # delete the temporary table
    tmpMaterialListUpdate.objects.using(dbToUse).all().delete()

@login_required
def fnUpdateMatlListfromSAP(req):

    dbToUse = user_db(req)

    client_phase = req.POST['phase'] if 'phase' in req.POST else None
    reqid = req.COOKIES['reqid'] if 'reqid' in req.COOKIES else None

    if req.method == 'POST':
        # check if the mandatory commits have been done and change the status code if so
        if reqid is not None:
            mandatory_commit_key = f'MatlX{reqid}'
            mandatory_commit_list = ['03A', '03D']
            if async_comm.objects.using(dbToUse).filter(pk=mandatory_commit_key).exists():
                mandatory_commits_recorded = async_comm.objects.using(dbToUse).get(pk=mandatory_commit_key).statecode
                if all((c in mandatory_commits_recorded) for c in mandatory_commit_list):
                    proc_MatlListSAPSprsheet_99_FinalProc(dbToUse, reqid)
                    async_comm.objects.using(dbToUse).filter(pk=mandatory_commit_key).delete()

        retinfo = HttpResponse()
        if client_phase=='init-upl':
            # start django_q broker
            reqid = subprocess.Popen(
                ['python', f'{django_settings.BASE_DIR}/manage.py', 'qcluster']
            ).pid
            # reqid = random.randint(1, 100000000000)
            retinfo.set_cookie('reqid',str(reqid))

            UpdateExistFldList = req.POST.getlist('UpIfCh', default=[])
            proc_MatlListSAPSprsheet_00InitUMLasync_comm(dbToUse, reqid, UpdateExistFldList)

            UMLSSName = proc_MatlListSAPSprsheet_00CopyUMLSpreadsheet(req, reqid)
            async_task(proc_MatlListSAPSprsheet_01ReadSpreadsheet, dbToUse, reqid, UMLSSName, hook=done_MatlListSAPSprsheet_01ReadSpreadsheet)

            acomm = async_comm.objects.using(dbToUse).values().get(pk=reqid)    # something's very wrong if this doesn't exist
            retinfo.write(json.dumps(acomm))
            return retinfo
        elif client_phase=='waiting':
            acomm = async_comm.objects.using(dbToUse).values().get(pk=reqid)    # something's very wrong if this doesn't exist
            retinfo.write(json.dumps(acomm))
            return retinfo
        elif client_phase=='wantresults':
            ImpErrList = tmpMaterialListUpdate.objects.using(dbToUse).filter(recStatus__startswith='err')
            AddedMatlsList = tmpMaterialListUpdate.objects.using(dbToUse).filter(recStatus='ADD')
            RemvdMatlsList = tmpMaterialListUpdate.objects.using(dbToUse).filter(recStatus__startswith='DEL')
            cntext = {
                'ImpErrList':ImpErrList,
                'AddedMatls':AddedMatlsList,
                'RemvdMatls':RemvdMatlsList,
                }
            templt = 'frmUpdateMatlListfromSAP_done.html'
            return render(req, templt, cntext)
        elif client_phase=='cleanup-after-failure':
            pass
        elif client_phase=='resultspresented':
            proc_MatlListSAPSprsheet_99_Cleanup(dbToUse, reqid)
            retinfo.delete_cookie('reqid')

            return retinfo
        else:
            return
        #endif client_phase
    else:   # req.method != 'POST'
        # (hopefully,) this is the initial phase; all others will be part of a POST request

        cntext = {
            'reqid': -1,
            }
        templt = 'frmUpdateMatlListfromSAP_phase0.html'
    #endif req.method = 'POST'

    return render(req, templt, cntext)
