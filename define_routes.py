from flask import Blueprint
from flask import render_template, redirect, url_for

import app_secrets


def define_routes(flskapp):
    @flskapp.route('/')       # I don't want / to be valid
    def app_homepage():
        """Home page route."""
        return render_template('errors/404.html'), 404

    @flskapp.route(flskapp.config['STARTUP_URL'], methods=['GET', 'POST'])
    def startup():
        """Startup page route."""
        # return redirect(url_for('auth.login'))  # Redirect to the login page
        return flskapp.view_functions[flskapp.config['STARTUP_DELEGATE']]()

    # quite optional    
    @flskapp.route('/about')
    def about():
        """About page route."""
        return render_template('about.html')

#################################################
#################################################

    
    # WICS routes
    WICS_bp = Blueprint('WICS', __name__, url_prefix='/WICS')

    ### CountEntryForm routes
    #########################
    from views.ActualCounts.frmCountEntryView import fnCountEntryView
    
    WICS_bp.add_url_rule('/CountEntryForm', 
        view_func=fnCountEntryView, 
        methods=['GET', 'POST'], 
        endpoint='CountEntryForm'
        )
    WICS_bp.add_url_rule('/CountEntryForm/Go/<int:recNum>',
        view_func=fnCountEntryView,
        methods=['GET','POST'],
        endpoint='CountEntryFormGo'
        )
    WICS_bp.add_url_rule('/CountEntryForm/Go/<int:recNum>/<string:gotoCommand>',
        view_func=fnCountEntryView,
        methods=['GET','POST'],
        endpoint='CountEntryFormGo_Command'
        )
    WICS_bp.add_url_rule('/CountEntryForm/<int:recNum>/<string:reqDate>/<string:MatlNum>',
        view_func=fnCountEntryView,
        methods=['GET','POST'],
        defaults={'gotoCommand':'ChgKey'},
        endpoint='CountEntryForm_ChgKey'
        )

    ### MaterialForm routes
    #########################
    from views.Material.frmMaterial import fnMaterialForm

    WICS_bp.add_url_rule('/MaterialForm', 
        view_func=fnMaterialForm, 
        methods=['GET', 'POST'], 
        endpoint='MaterialForm'
        )
    WICS_bp.add_url_rule('/MaterialForm/recnum/<int:recNum>', 
        view_func=fnMaterialForm, 
        methods=['GET', 'POST'], 
        endpoint='MaterialFormRecNum'
        )
    WICS_bp.add_url_rule('/MaterialForm/newRec', 
        view_func=fnMaterialForm, 
        methods=['GET', 'POST'], 
        defaults={'gotoRec':False, 'newRec':True},
        endpoint='NewMaterialForm'
        )
    WICS_bp.add_url_rule('/MaterialForm/histcutoff/<int:recNum>/<string:HistoryCutoffDate>',
        view_func=fnMaterialForm,
        methods=['GET', 'POST'],
        endpoint='MaterialFormChgHistCutoffDate'
        )


    # this will start the huey pipeline
    ### UpdateMatlListfromSAP routes
    ###################################
    from views.Material.updtMatlList import fnUpdateMatlListfromSAP
    WICS_bp.add_url_rule('/UpdateMatlListfromSAP',
        view_func=fnUpdateMatlListfromSAP,      #type: ignore
        methods=['GET', 'POST'], 
        endpoint='UpdateMatlListfromSAP'
        )

    flskapp.register_blueprint(WICS_bp)

#################################################

    # the old WICS3 Django paths
    # path('MaterialForm',
    #         procs_Material.fnMaterialForm, name='MatlForm'),
    # path('MaterialForm/recnum/<int:recNum>',
    #         procs_Material.fnMaterialForm, name='MatlFormRecNum'),
    # path('MaterialForm/newRec',
    #         procs_Material.fnMaterialForm, {'gotoRec':False, 'newRec':True}, name='NewMatlForm'),
    # path('MaterialForm/histcutoff/<int:recNum>/<str:HistoryCutoffDate>',
    #         procs_Material.fnMaterialForm, name='MatlFormChgHistCutoffDate'),

    # path('ActualCountList',
    #         procs_ActualCounts.ActualCountListForm.as_view(), name='ActualCountList'),

    # path('CountScheduleList',
    #         procs_CountSchedule.CountScheduleListForm.as_view(),name='CountScheduleList'),


    # path('CountScheduleForm',
    #         views.fnCountScheduleRecView, name='CountScheduleForm'),
    # path('CountScheduleForm/Go/<int:recNum>',
    #         views.fnCountScheduleRecView, name='CountScheduleFormGo'),
    # path('CountScheduleForm/Go/<int:recNum>/<str:gotoCommand>',
    #         views.fnCountScheduleRecView,
    #         name='CountScheduleFormGo'),    
    # path('CountScheduleForm/<int:recNum>/<str:reqDate>/<str:MatlNum>',
    #         views.fnCountScheduleRecView, {'gotoCommand':'ChgKey'},
    #         name='CountScheduleForm'),

    # path('RequestCountScheduleForm',
    #         views.fnRequestCountScheduleRecView, name='RequestCountScheduleForm'),
    # path('RequestCountScheduleForm/<int:recNum>/<str:reqDate>/<str:MatlNum>',
    #         views.fnRequestCountScheduleRecView, {'gotoCommand':'ChgKey'},
    #         name='RequestCountScheduleForm'),
    # path('RequestedCountListEdit',
    #         views.fnRequestedCountEditListView, name='RequestCountListEdit'),
    # path('RequestedCountListEdit/<int:ShowFilledRequests>',
    #         views.fnRequestedCountEditListView, name='RequestCountListEditShowFilled'),

    # path('CountSummaryRpt/v/REQ',
    #         procs_ActualCounts.fnCountSummaryReqRpt, name='CountSummaryReport-v-init'),
    # path('CountSummaryRpt/v/<str:Rptvariation>',
    #         procs_ActualCounts.fnCountSummaryRpt, name='CountSummaryReport-v'),
    # path('CountSummaryRpt/v/<str:Rptvariation>/<str:passedCountDate>',
    #         procs_ActualCounts.fnCountSummaryRpt, name='CountSummaryReport-v'),
    # path('CountSummaryRpt',
    #         procs_ActualCounts.fnCountSummaryRpt, name='CountSummaryReport'),
    # path('CountSummaryRpt/<str:passedCountDate>',
    #         procs_ActualCounts.fnCountSummaryRpt, name='CountSummaryReport'),

    # path('CountWorksheet',
    #         procs_CountSchedule.viewCountWorksheetReport,name='CountWorksheet'),
    # path('CountWorksheet/<CountDate>',
    #         procs_CountSchedule.viewCountWorksheetReport,name='CountWorksheet'),
    # path('CountWorksheetLoc',
    #         procs_CountSchedule.viewCountWorksheetLocReport,name='CountWorksheetLoc'),
    # path('CountWorksheetLoc/<CountDate>',
    #         procs_CountSchedule.viewCountWorksheetLocReport,name='CountWorksheetLoc'),

    # path('MPN',
    #         procs_Material.fnMPNView, name='MPNLookup'),

    # path('MatlByPartType',
    #         procs_Material.MaterialByPartType.as_view(), name='MatlByPartType'),

    # path('MatlByLastCountDate',
    #         procs_Material.MaterialByLastCountDate.as_view(), name='MatlByLastCountDate'),

    # path('MatlByDESCValue',
    #         procs_Material.MaterialByDESCValue.as_view(), name='MatlByDESCValue'),

    # path('MaterialLocations',
    #         procs_Material.MaterialLocationsList.as_view(),name='MaterialLocations'),

    # path('LocationList',
    #         procs_Material.fnLocationList,name='LocationList'),

    # path('PartTypeForm',
    #         procs_Material.fnPartTypesForm, {'recNum':-999}, name='PartTypeForm'),
    # path('PartTypeForm/<int:recNum>',
    #         procs_Material.fnPartTypesForm, {'gotoRec':True}, name='ReloadPTypForm'),
    # path('DeltePartType/<int:recNum>',
    #         procs_Material.fnDeletPartTypes, name='DeletePTyp'),

    # path('SAP',procs_SAP.fnShowSAP,name='showtable-SAP'),
    # path('SAP/<str:reqDate>',procs_SAP.fnShowSAP,name='showtable-SAP'),
    
    # path('SAP/exists/ajax/<str:reqDate>',procs_SAP.fnajaxSAPExists,name='SAPajaxExists'),

    # path('UpldActCtSprsht', procs_ActualCounts.fnUploadActCountSprsht, name='UploadActualCountSprsht'),

    # path('UpldCtSchedSprsht', procs_CountSchedule.fnUploadCountSchedSprsht, name='UploadCountSchedSprsht'),

    # path('UpdateMatlListfromSAP',procs_SAP.fnUpdateMatlListfromSAP, name='UpdateMatlListfromSAP'),

    # path('UpldSAPSprsht',procs_SAP.fnUploadSAP, name='UploadSAPSprSht'),


#################################################

    # for testing Server-Sent Events (SSE) streaming
    from _newcode.streamtest import test_stream
    SSE_bp = Blueprint('SSE', __name__, url_prefix='/SSE')
    SSE_bp.add_url_rule('/test-stream', view_func=test_stream)

    # for Update Material List progress tracking
    # from views.Material.updtMatlList import init_UpldMatlList
    # this will start the huey pipeline
    # SSE_bp.add_url_rule('/InitUpdML', view_func=init_UpldMatlList, methods=['POST'])
    from views.Material.updtMatlList import progress_UpdML
    SSE_bp.add_url_rule('/UpdMatlLst/<reqid>', view_func=progress_UpdML)

    flskapp.register_blueprint(SSE_bp)
