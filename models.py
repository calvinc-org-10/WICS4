
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

from typing import Any

from sqlalchemy import (
    BigInteger, Integer, SmallInteger, Boolean,
    Double, 
    String,
    Date, 
    ForeignKeyConstraint, Index, UniqueConstraint,
    select,
    inspect, 
    )

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped, mapped_column, relationship, 
    )

from database import app_db

# ============================================================================
# LEGACY MODELS (for cMenu, cParameters, cGreetings, and User)
# ============================================================================

class cToolsdbBase(DeclarativeBase):
    """Base class for all models, using SQLAlchemy's DeclarativeBase."""
    query = app_db.session.query_property()

cTools_tablenames = {}
cTools_models = {}

# calvincTools override checklist:
# 1) If only the legacy table name differs, use cTools_tablenames.
# 2) If legacy columns differ, provide an override model in cTools_models.
# 3) Avoid relationship('menuGroups') / relationship('menuItems') strings in
#    override models unless both sides are in the same SQLAlchemy registry.
# 4) For legacy tables without ORM ForeignKey metadata, let calvincTools
#    init_cDatabase attach compatible relationships.

# class menuGroups(cToolsdbBase):
# cTools field name are same as Legacy WICS cMenuGroup model, so no need to override this class with custom field names.
cTools_tablenames['menuGroups'] = 'cMenu_menugroups'  # table name is different case than the default, so we need to specify it here

class WICS3_menuItems(cToolsdbBase):
    """Menu items model with database columns."""
    # __bind_key__ = cTools_bind_key
    __tablename__ = 'cMenu_menuitems'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    MenuGroup_id: Mapped[int|None] = mapped_column(BigInteger)
    MenuID: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    OptionNumber: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    OptionText: Mapped[str] = mapped_column(String(250), nullable=False)
    Command: Mapped[int|None] = mapped_column('Command_id', Integer)
    Argument: Mapped[str] = mapped_column(String(250), nullable=False)
    pword: Mapped[str] = mapped_column('PWord', String(250), nullable=False)
    top_line: Mapped[bool|None] = mapped_column('TopLine', Boolean)
    bottom_line: Mapped[bool|None] = mapped_column('BottomLine', Boolean)

    # Unique constraint
    __table_args__ = (
        UniqueConstraint('MenuGroup_id', 'MenuID', 'OptionNumber', 
                        name='uq_menu_group_MenuID_OptionNumber'),
    )
    
    def __repr__(self):
        return f'<MenuItem {self.MenuGroup_id},{self.MenuID}/{self.OptionNumber}>'
    
    def __str__(self):
        return f'{self.MenuGroup_id}, {self.MenuID}/{self.OptionNumber}, {self.OptionText}'

    def __init__(self, **kw: Any):
        """Initialize a new menuItems instance."""
        inspector = inspect(app_db.engine)
        if not inspector.has_table(self.__tablename__):
            # If the table does not exist, create it
            app_db.create_all()
        super().__init__(**kw)
# menuItems
cTools_models['menuItems'] = WICS3_menuItems  # add the model to the cTools_models dict for later reference by calvincTools_init()

class WICS3_cParameters(cToolsdbBase):
    """Parameters model with database columns."""
    # __bind_key__ = cTools_bind_key
    __tablename__ = 'cMenu_cparameters'
    
    parm_name: Mapped[str] = mapped_column('ParmName', String(100), primary_key=True)
    parm_value: Mapped[str] = mapped_column('ParmValue', String(512), default='', nullable=False)
    user_modifiable: Mapped[bool] = mapped_column('UserModifiable', Boolean, default=True,  nullable=False)
    comments: Mapped[str] = mapped_column('Comments', String(512), default='', nullable=False)

   
    def __repr__(self):
        return f'<Parameter {self.parm_name}>'
    
    def __str__(self):
        return f'{self.parm_name} ({self.parm_value})'
    
    @classmethod
    def get_parameter(cls, parm_name: str, default: str = '') -> str:
        """Django equivalent: getcParm"""
        stmt = select(cls).where(cls.parm_name == parm_name)
        param = app_db.session.execute(stmt).scalar_one_or_none()
        return param.parm_value if param else default
    
    @classmethod
    def set_parameter(cls, parm_name: str, parm_value: str, user_modifiable: bool = True, comments: str = ''):
        """Django equivalent: setcParm"""
        stmt = select(cls).where(cls.parm_name == parm_name)
        param = app_db.session.execute(stmt).scalar_one_or_none()
        if param:
            param.parm_value = parm_value
        else:
            param = cls(
                parm_name=parm_name,
                parm_value=parm_value,
                user_modifiable=user_modifiable,
                comments=comments
            )
            app_db.session.add(param)
        
        app_db.session.commit()
        return param
    # set_parameter
# cParameters
cTools_models['cParameters'] = WICS3_cParameters  # add the model to the cTools_models dict for later reference by calvincTools_init()

class WICS3_cGreetings(cToolsdbBase):
    """Greetings model with database columns."""
    # __bind_key__ = cTools_bind_key
    __tablename__ = 'cMenu_cgreetings'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    greeting: Mapped[str] = mapped_column('Greeting', String(2000), nullable=False)

    def __repr__(self):
        return f'<Greeting {self.id}>'
    
    def __str__(self):
        return f'{self.greeting} (ID: {self.id})'
# cGreetings
cTools_models['cGreetings'] = WICS3_cGreetings  # add the model to the cTools_models dict for later reference by calvincTools_init()

# class User(cToolsdbBase):
# cTools field name are same as Legacy WICS cMenuGroup model, so no need to override this class with custom field names.
cTools_tablenames['User'] = 'WICS4_users'  # table name is different case than the default, so we need to specify it here
