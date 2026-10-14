from datetime import date
from barcode import Code128

from sqlalchemy import select, func, and_

from database import app_db
from models import ActualCounts


def LastLocations(matl_ids:list[int]):
    """
    Get the last known locations and count dates for the given material IDs.

    Args:
        matl_ids (list[int]): List of material IDs to query.

    Returns:
        dict: A dictionary mapping material IDs to their last known locations ['LastFoundAt'] and count dates ['LastCountDate'].
    """
    
    
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

    matl_info = {}
    for m in matl_ids:
        last = last_by_matl.get(m)
        matl_info[m] = {
            'LastCountDate': last['date'] if last else None,
            'LastFoundAt': last['locs'] if last else [],
        }
        
    return matl_info
