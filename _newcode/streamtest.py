from flask import Response

# @app.route("/test-stream")
def test_stream():

    def gen():
        import time
        for i in range(5):
            yield f"data: {i}\n\n"
            time.sleep(1)

    r = Response(gen(), mimetype="text/event-stream")
    r.headers["X-Accel-Buffering"] = "no"
    return r