from models import async_comm


from flask import Response, stream_with_context


import json
import time


def progress_UplSprSht(reqid):

    def generate():
        last_version = 0

        while True:
            # session = HueySession()

            row = async_comm.get_async_comm_state(reqid)    # if the record has been deleted (e.g. by cleanup after failure), this will throw an exception, so default to None if we can't get the record

            if row and row.version > last_version:

                payload = json.dumps({
                    "statecode": row.statecode,
                    "statetext": row.statetext
                })  #should I dump the whole record here instead of just statecode and statetext?  Maybe not a good idea if there are big text fields or something, but it would be more flexible for the frontend if it had access to all the fields without me having to predict which ones it might want.  For now, I'll just include statecode and statetext since those are the ones I know the frontend will need, and I can always add more later if needed.

                yield f"data: {payload}\n\n"

                last_version = row.version

                if row.statecode == "done":
                    break

            # session.close()

            yield ": keepalive\n\n"

            time.sleep(1)
        # endwhile (until we break on statecode == "done")
    # generate

    r = Response(stream_with_context(generate()),
                 mimetype="text/event-stream")

    r.headers["X-Accel-Buffering"] = "no"

    return r