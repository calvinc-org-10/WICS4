from typing import Any
from datetime import datetime

from sqlalchemy import (
    UniqueConstraint,
    inspect,
    )
from sqlalchemy.exc import IntegrityError

from database import app_db
from calvincTools.mixins import _ModelInitMixin


# ============================================================================
# MENU SYSTEM MODELS
# ============================================================================


#### NO!!! Let calvinCTools do this, otherwise those models will be wrong!!
# def init_cDatabase(flskapp):
    # """Create all tables in the database."""
    # return  # NO!!! Let calvinCTools do this, otherwise those models will be wrong!!
    # with flskapp.app_context():
    #     app_db.create_all()
    #     # Ensure that the tables are created when the module is imported
    #     # nope, not when module imported. app context needed first
# create_all_tables

