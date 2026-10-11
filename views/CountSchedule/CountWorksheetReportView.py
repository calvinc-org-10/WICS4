from datetime import date
from barcode import Code128

from flask import (
    current_app,
    abort,
    flash,
    redirect,
    request,
    url_for,
)
from flask_login import login_required
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload

from calvincTools.utils import (
    checkTemplate_and_render,
    coerce_date,
)
from database import app_db
from models import CountSchedule, MaterialList, ActualCounts


@login_required
def viewCountWorksheetReport(CountDate=None):

    wkshtDate = coerce_date(CountDate)
    
    stmt = (
        select(CountSchedule)
        .options(joinedload(CountSchedule.Material))
        .join(MaterialList, CountSchedule.Material_id == MaterialList.id)
        .where(CountSchedule.CountDate == wkshtDate)
        .order_by(CountSchedule.Counter, MaterialList.Material)
    )
    count_list = app_db.session.execute(stmt).scalars().all()
    
    # add barcodes, LastFoundAt, LastCountDate
    # distinct Materials scheduled for wkshtDate
    matl_stmt = (
        select(MaterialList)
        .where(MaterialList.id.in_(
            select(CountSchedule.Material_id)
            .where(CountSchedule.CountDate == wkshtDate)
            .distinct()
        ))
        .order_by(MaterialList.Material)
    )
    materials = app_db.session.execute(matl_stmt).scalars().all()
    matl_ids = [m.id for m in materials]

    # latest Actual CountDate per selected Material
    max_dt = (
        select(
            ActualCounts.Material_id,
            func.max(ActualCounts.CountDate).label('maxdt'),
        )
        .where(ActualCounts.Material_id.in_(matl_ids))
        .group_by(ActualCounts.Material_id)
        .subquery()
    )

    # every row from that latest date
    last_rows = app_db.session.execute(
        select(ActualCounts.Material_id, ActualCounts.CountDate, ActualCounts.LOCATION)
        .join(max_dt, and_(
            ActualCounts.Material_id == max_dt.c.Material_id,
            ActualCounts.CountDate == max_dt.c.maxdt,
        ))
        .order_by(ActualCounts.Material_id, ActualCounts.LOCATION)
    ).all()

    last_by_matl = {}
    for r in last_rows:
        entry = last_by_matl.setdefault(r.Material_id, {'date': r.CountDate, 'locs': []})
        if r.LOCATION not in entry['locs']:      # de-dupe repeated locations
            entry['locs'].append(r.LOCATION)

    def make_barcode(text: str) -> str:
        svg = Code128(str(text)).render(
            writer_options={'module_height': 7.0, 'module_width': 0.35,
                            'quiet_zone': 0.1, 'write_text': True,
                            'text_distance': 3.5}
        )
        return str(svg).replace("b'", "").replace('\\r', '').replace('\\n', '').replace("'", "")

    matl_info = {}
    for m in materials:
        last = last_by_matl.get(m.id)
        matl_info[m.id] = {
            'bcstr': make_barcode(m.Material),
            'LastFoundAt': ', '.join(last['locs']) if last else None,
            'LastCountDate': last['date'] if last else None,
        }

    # compile list of all dates with a schedule for date dropdown
    stmt_dates = select(CountSchedule.CountDate).distinct().order_by(CountSchedule.CountDate.desc())
    all_dates = [row[0] for row in app_db.session.execute(stmt_dates).all()]
    
    # collect the list of Counters so that tabs can be built in the html
    stmt_counters = select(CountSchedule.Counter).distinct().where(CountSchedule.CountDate == wkshtDate).order_by(CountSchedule.Counter)
    all_counters = [row[0] for row in app_db.session.execute(stmt_counters).all()]
    
    # later, add SAP info
    
    # templt = 'CountSchedule/rpt_CountWksht.html'
    templt = 'CountSchedule/rpt_CountWksht.html'
    cntext = {
        'CtSchd': count_list,
        'MatlInfo': matl_info,
        'CountDate': wkshtDate,
        'AllScheduledDates': all_dates,
        'CounterList': all_counters,
    }
    return checkTemplate_and_render(
        templt,
        **cntext
    )
