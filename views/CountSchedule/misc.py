from sqlalchemy import select

from models import CountSchedule
from database import app_db


# should I do a generic to return the record then check if that exists?
def CountScheduleRecordExist(Material_id, CountDate):
    """
    Check if a CountSchedule record exists for the given Material_id and CountDate.
    """

    stmt = (
        select(CountSchedule)
        .where(CountSchedule.Material_id == Material_id)
        .where(CountSchedule.CountDate == CountDate)
    )
    return app_db.session.execute(stmt).scalars().first() is not None
