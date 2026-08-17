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

    from views.ActualCounts.upldActCounts import fnUploadActCountSprsht
    WICS_bp.add_url_rule('/UploadActualCounts',
        view_func=fnUploadActCountSprsht,      #type: ignore
        methods=['GET', 'POST'], 
        endpoint='UploadActualCounts'
        )

    ### MaterialForm routes
    #########################
    from views.Material.frmMaterial import (
        fnMaterialForm, 
        fnMaterialForm_copycount,
        fnMaterialForm_photos,
        )

    WICS_bp.add_url_rule('/MaterialForm', 
        view_func=fnMaterialForm, 
        methods=['GET', 'POST'], 
        endpoint='MaterialForm'
        )
    WICS_bp.add_url_rule('/MaterialForm/recnum/<int:recNum>', 
        view_func=fnMaterialForm, 
        methods=['GET', 'POST'], 
        defaults={'gotoRec':True, 'newRec':False},
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

    # photo operations ajax call for a material record
    WICS_bp.add_url_rule('/MaterialForm/photos/<int:recNum>',
        view_func=fnMaterialForm_photos, 
        methods=['POST'], 
        endpoint='MaterialFormPhotos'
        )
    # copy count record ajax call for a material record
    WICS_bp.add_url_rule('/MaterialForm/copycount/<int:recNum>',
        view_func=fnMaterialForm_copycount, 
        methods=['POST'], 
        endpoint='MaterialFormCopyCount'
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

    ### Count Summary Report routes
    #########################
    from views.ActualCounts import rptCountSummary
    WICS_bp.add_url_rule('/CountSummaryRpt',
        view_func=rptCountSummary.fnCountSummaryRpt, 
        methods=['GET'], 
        endpoint='CountSummaryReport',
        )
    WICS_bp.add_url_rule('/CountSummaryRpt/v/REQ',
        view_func=rptCountSummary.fnCountSummaryReqRpt, 
        methods=['GET'], 
        endpoint='CountSummaryReport-vREQ-init',
        )
    WICS_bp.add_url_rule('/CountSummaryRpt/v/<string:Rptvariation>',
        view_func=rptCountSummary.fnCountSummaryRpt, 
        methods=['GET'], 
        endpoint='CountSummaryReport-v',
        )
    WICS_bp.add_url_rule('/CountSummaryRpt/v/<string:Rptvariation>/<string:passedCountDate>',
        view_func=rptCountSummary.fnCountSummaryRpt, 
        methods=['GET'], 
        endpoint='CountSummaryReport-v-dt',
        )
    WICS_bp.add_url_rule('/CountSummaryRpt/<string:passedCountDate>',
        view_func=rptCountSummary.fnCountSummaryRpt, 
        methods=['GET'], 
        endpoint='CountSummaryReport-dt',
        )

    ### SAP Table routes
    #########################
    from views.SAP import procs_SAP
    WICS_bp.add_url_rule('/SAP',
        view_func=procs_SAP.fnShowSAP, 
        methods=['GET'], 
        endpoint='showtable-SAP',
        )
    WICS_bp.add_url_rule('/SAP/<string:reqDate>',
        view_func=procs_SAP.fnShowSAP, 
        methods=['GET'], 
        endpoint='showtable-SAP-dt',
        )
    WICS_bp.add_url_rule('/SAP/exst/<string:reqDate>',
        view_func=procs_SAP.fnajaxSAPExists, 
        methods=['GET'], 
        endpoint='SAPajaxExists',
        )
    

    flskapp.register_blueprint(WICS_bp)

#################################################

    # the old WICS3 Django paths
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
    from async_procs.progress_UplSprSht import progress_UplSprSht
    SSE_bp.add_url_rule('/UplSprSht/<reqid>', view_func=progress_UplSprSht)

    flskapp.register_blueprint(SSE_bp)
