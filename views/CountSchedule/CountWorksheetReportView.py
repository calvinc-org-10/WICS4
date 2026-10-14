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

from views.ActualCounts import LastLocations
from database import app_db
from models import CountSchedule, MaterialList, ActualCounts


# move to misc WICS util
def make_barcode(text: str) -> str:
    svg = Code128(str(text)).render(
        writer_options={'module_height': 7.0, 'module_width': 0.35,
                        'quiet_zone': 0.1, 'write_text': True,
                        'text_distance': 3.5}
    )
    return str(svg).replace("b'", "").replace('\\r', '').replace('\\n', '').replace("'", "")

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

    matl_info = LastLocations(matl_ids)
    for m in materials:
        matl_info[m.id]['bcstr'] = make_barcode(m.orgMaterialNum or '')
    
    # compile list of all dates with a schedule for date dropdown
    stmt_dates = select(CountSchedule.CountDate).distinct().order_by(CountSchedule.CountDate.desc())
    all_dates = [row[0] for row in app_db.session.execute(stmt_dates).all()]
    
    # collect the list of Counters so that tabs can be built in the html
    stmt_counters = select(CountSchedule.Counter).distinct().where(CountSchedule.CountDate == wkshtDate).order_by(CountSchedule.Counter)
    all_counters = [row[0] for row in app_db.session.execute(stmt_counters).all()]
    
    # later, add SAP info
    
    # later, build LocationList per Counter
    
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
