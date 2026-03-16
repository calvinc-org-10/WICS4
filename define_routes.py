from flask import render_template, redirect, url_for

import app_secrets


def define_routes(flskapp):
    @flskapp.route('/')       # I don't want / to be valid
    def app_homepage():
        """Home page route."""
        return render_template('errors/404.html'), 404

    @flskapp.route(app_secrets.startup_URL)
    def startup():
        """Startup page route."""
        return redirect(url_for('auth.login'))  # Redirect to the login page

    # quite optional    
    @flskapp.route('/about')
    def about():
        """About page route."""
        return render_template('about.html')

    # for testing Server-Sent Events (SSE) streaming
    from _newcode.streamtest import test_stream
    flskapp.add_url_rule('/SSE/test-stream', view_func=test_stream)

    # for Update Material List progress tracking
    from views.Materials.updtMatlList import init_UpldMatlList
    flskapp.add_url_rule('/SSE/InitUpdML', view_func=init_UpldMatlList, methods=['POST'])
    from views.Materials.updtMatlList import progress_UpdML
    flskapp.add_url_rule('/SSE/UpdMatlLst/<reqid>', view_func=progress_UpdML)


