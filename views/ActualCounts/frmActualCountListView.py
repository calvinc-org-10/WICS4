from datetime import date

from flask import (
    current_app,
    abort,
    flash,
    redirect,
    request,
    url_for,
)
from flask_login import login_required
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from calvincTools.mathexpr_parser import eval_arith
from calvincTools.utils import checkTemplate_and_render
from database import app_db
from models import ActualCounts, MaterialList


_MAX_LISTRECS = 5000


def _get_max_listrecs() -> int:
    configured_limit = str(current_app.config.get('COUNTLIST_RECLIMIT', _MAX_LISTRECS))
    if configured_limit.isnumeric():
        parsed_limit = int(configured_limit)
        if parsed_limit > 0:
            return parsed_limit
    return _MAX_LISTRECS


def _parse_post_int(name: str) -> int:
    raw_value = request.form.get(name, '').strip()
    if not raw_value:
        abort(400, f'Missing required field {name}.')
    try:
        parsed_value = int(raw_value)
    except ValueError as ex:
        raise ValueError(f'Invalid integer value for {name}: {raw_value}') from ex
    if parsed_value <= 0:
        raise ValueError(f'{name} must be greater than 0.')
    return parsed_value


def _parse_post_date(name: str) -> date:
    raw_value = request.form.get(name, '').strip()
    if not raw_value:
        raise ValueError(f'Missing required field {name}.')
    try:
        return date.fromisoformat(raw_value)
    except ValueError as ex:
        raise ValueError(f'Invalid date value for {name}: {raw_value}') from ex


@login_required
def fnActualCountListView():
    if request.method == 'POST':
        if 'copyCountFromid' in request.form:
            try:
                copy_count_from_id = _parse_post_int('copyCountFromid')
                copy_count_to_date = _parse_post_date('copyCountToDate')
            except ValueError as ex:
                flash(str(ex), 'error')
                return redirect(url_for('WICS.ActualCountList'))

            source_count = app_db.session.get(ActualCounts, copy_count_from_id)
            if source_count is None:
                abort(404, f'Count record {copy_count_from_id} not found.')

            copied_count = ActualCounts(
                CountDate=copy_count_to_date,
                Counter=source_count.Counter,
                LOCATION=source_count.LOCATION,
                FLAG_PossiblyNotRecieved=source_count.FLAG_PossiblyNotRecieved,
                FLAG_MovementDuringCount=source_count.FLAG_MovementDuringCount,
                Material_id=source_count.Material_id,
                LocationOnly=source_count.LocationOnly,
                CycCtID=source_count.CycCtID,
                CTD_QTY_Expr=source_count.CTD_QTY_Expr,
                PKGID_Desc=source_count.PKGID_Desc,
                TAGQTY=source_count.TAGQTY,
                Notes=source_count.Notes,
            )
            app_db.session.add(copied_count)
            app_db.session.commit()
            flash(
                f'Count copied successfully from ID {copy_count_from_id} to record {copied_count.id}, date {copy_count_to_date}',
                'success',
            )
            return redirect(url_for('WICS.ActualCountList'))

        if 'deleteCountid' in request.form:
            try:
                delete_count_id = _parse_post_int('deleteCountid')
            except ValueError as ex:
                flash(str(ex), 'error')
                return redirect(url_for('WICS.ActualCountList'))

            delete_count = app_db.session.get(ActualCounts, delete_count_id)
            if delete_count is None:
                abort(404, f'Count record {delete_count_id} not found.')
            app_db.session.delete(delete_count)
            app_db.session.commit()
            flash(f'Deleted count record {delete_count_id}.', 'success')
            return redirect(url_for('WICS.ActualCountList'))

        abort(400, 'Unsupported Actual Count List operation.')

    max_listrecs = _get_max_listrecs()
    stmt = (
        select(ActualCounts)
        .options(joinedload(ActualCounts.Material))
        .join(MaterialList, ActualCounts.Material_id == MaterialList.id)
        .order_by(ActualCounts.CountDate.desc(), MaterialList.Material, ActualCounts.id)
        .limit(max_listrecs)
    )
    actual_count_list = app_db.session.execute(stmt).scalars().all()
    for record in actual_count_list:
        qty_eval = None
        if not record.LocationOnly and record.CTD_QTY_Expr:
            qty_eval = eval_arith(record.CTD_QTY_Expr)
        setattr(record, 'CTD_QTY_Eval', qty_eval)

    templt = 'ActualCounts/frm_ActualCountList.html'
    cntext = {
        'ActCtList': actual_count_list,
        'max_listrecs': max_listrecs,
    }
    return checkTemplate_and_render(
        templt,
        **cntext
    )
