from typing import Any
from datetime import datetime

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import (
    UniqueConstraint,
    inspect,
    )
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped, mapped_column,
    )
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.local import LocalProxy

from calvincTools.cMenu import MENUCOMMAND
from calvincTools.cMenu.initial_menus import initial_menus

from database import app_db
# Create a local proxy for the database instance
db_instance = LocalProxy(lambda: app_db)

cTools_bind_key = 'cToolsdb'
cTools_tablenames = {}

##############################################
##############################################
##############################################

class cToolsdbBase(DeclarativeBase):
    """Base class for all models, using SQLAlchemy's DeclarativeBase."""
    pass

class menuGroups(cToolsdbBase):
    """Menu groups model with database columns."""
    __bind_key__ = cTools_bind_key
    __tablename__ = cTools_tablenames.get('menuGroups', 'cMenu_menuGroups')
    
    id = db_instance.Column(db_instance.Integer, primary_key=True)
    GroupName = db_instance.Column(db_instance.String(100), unique=True, nullable=False, index=True)
    GroupInfo = db_instance.Column(db_instance.String(250), default='')
    
    # Relationships
    menu_items = db_instance.relationship('menuItems', back_populates='menu_group', lazy='selectin')
    
    def __repr__(self):
        return f'<MenuGroup {self.id} - {self.GroupName}>'
    
    def __str__(self):
        return f'menuGroup {self.GroupName}'

    @classmethod
    def createtable(cls, flskapp):
        """Create the table and populate with initial data if empty."""
        with flskapp.app_context():
            # Create tables if they don't exist
            db_instance.create_all()

            if not db_instance.session.query(cls).first():
                cls.create_newgroup(
                    group_name="Initial Group", 
                    group_info="Group Info here", 
                    isSuperUser=True
                    )
        # endwith app context
    # createtable
    
    @classmethod
    def create_newgroup(cls, group_name: str, group_info: str, isSuperUser: bool = False, group_id = None):
        """Create a new menu group with default menu items."""
        
        init_menu_type = 'new.super.menugroup.newmenu' if isSuperUser else 'new.ordinary.menugroup.newmenu'
        
        with current_app.app_context():
            try:
                if isinstance(group_id, int):
                    # Check if group_id already exists
                    existing_group = db_instance.session.query(cls).filter_by(id=group_id).first()
                    if existing_group:
                        raise ValueError(f"A group with the ID '{group_id}' already exists.")
                # endif group_id check
                
                # Create new group
                if group_id is not None:
                    new_group = cls(id=group_id, GroupName=group_name, GroupInfo=group_info)
                else:
                    new_group = cls(GroupName=group_name, GroupInfo=group_info)
                db_instance.session.add(new_group)
                db_instance.session.commit()
                
                # Add default menu items for the new group
                new_group_id = new_group.id
                # menuItems_cls = getattr(current_module, 'menuItems')
                menuItems_cls = menuItems

                menu_items = [ 
                    menuItems_cls(
                        MenuGroup_id=new_group_id, MenuID=0, OptionNumber=item['OptionNumber'], 
                        OptionText=item['OptionText'], 
                        Command=item['Command'], Argument=item['Argument'], 
                        pword=item.get('PWord',''), 
                        top_line=item.get('TopLine', 0),
                        bottom_line=item.get('BottomLine', 0)
                        )
                    for item in initial_menus[init_menu_type]
                    ]
                db_instance.session.add_all(menu_items)
                db_instance.session.commit()
                
                return new_group
            except IntegrityError:
                db_instance.session.rollback()
                raise ValueError(f"A group with the name '{group_name}' already exists.")
            finally:
                db_instance.session.close() 
            # end try (creating new group and menu items)
        # endwith app context
    # create_newgroup
# menuGroups

class menuItems(cToolsdbBase):
    """Menu items model with database columns."""
    __bind_key__ = cTools_bind_key
    __tablename__ = cTools_tablenames.get('menuItems', 'cMenu_menuItems')
    
    id = db_instance.Column(db_instance.Integer, primary_key=True)
    MenuGroup_id = db_instance.Column(db_instance.Integer, db_instance.ForeignKey('cMenu_menuGroups.id', ondelete='RESTRICT'), nullable=True)
    MenuID = db_instance.Column(db_instance.SmallInteger, nullable=False)
    OptionNumber = db_instance.Column(db_instance.SmallInteger, nullable=False)
    OptionText = db_instance.Column(db_instance.String(250), nullable=False)
    Command = db_instance.Column(db_instance.Integer, nullable=True)
    Argument = db_instance.Column(db_instance.String(250), default='')
    pword = db_instance.Column(db_instance.String(250), default='')
    top_line = db_instance.Column(db_instance.Boolean, nullable=True)
    bottom_line = db_instance.Column(db_instance.Boolean, nullable=True)
    
    # Relationships
    menu_group = db_instance.relationship('menuGroups', back_populates='menu_items', lazy='joined')
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('MenuGroup_id', 'MenuID', 'OptionNumber', 
                        name='uq_menu_group_MenuID_OptionNumber'),
    )
    
    def __repr__(self):
        return f'<MenuItem {self.MenuGroup_id},{self.MenuID}/{self.OptionNumber}>'
    
    def __str__(self):
        return f'{self.menu_group}, {self.MenuID}/{self.OptionNumber}, {self.OptionText}'

    def __init__(self, **kw: Any):
        """Initialize a new menuItems instance."""
        inspector = inspect(db_instance.engine)
        if not inspector.has_table(self.__tablename__):
            # If the table does not exist, create it
            db_instance.create_all()
        super().__init__(**kw)
# menuItems

class cParameters(cToolsdbBase):
    """Parameters model with database columns."""
    __bind_key__ = cTools_bind_key
    __tablename__ = cTools_tablenames.get('cParameters', 'cMenu_cParameters')
    
    parm_name: str = db_instance.Column(db_instance.String(100), primary_key=True)
    parm_value: str = db_instance.Column(db_instance.String(512), default='', nullable=False)
    user_modifiable: bool = db_instance.Column(db_instance.Boolean, default=True, nullable=False)
    comments: str = db_instance.Column(db_instance.String(512), default='', nullable=False)
    
    def __repr__(self):
        return f'<Parameter {self.parm_name}>'
    
    def __str__(self):
        return f'{self.parm_name} ({self.parm_value})'
    
    @classmethod
    def get_parameter(cls, parm_name: str, default: str = '') -> str:
        """Django equivalent: getcParm"""
        param = cls.query.filter_by(parm_name=parm_name).first()
        return param.parm_value if param else default
    
    @classmethod
    def set_parameter(cls, parm_name: str, parm_value: str, user_modifiable: bool = True, comments: str = ''):
        """Django equivalent: setcParm"""
        param = cls.query.filter_by(parm_name=parm_name).first()
        if param:
            param.parm_value = parm_value
        else:
            param = cls(
                parm_name=parm_name,
                parm_value=parm_value,
                user_modifiable=user_modifiable,
                comments=comments
            )
            db_instance.session.add(param)
        
        db_instance.session.commit()
        return param
    # set_parameter
# cParameters

class cGreetings(cToolsdbBase):
    """Greetings model with database columns."""
    __bind_key__ = cTools_bind_key
    __tablename__ = cTools_tablenames.get('cGreetings', 'cMenu_cGreetings')
    
    id = db_instance.Column(db_instance.Integer, primary_key=True)
    greeting = db_instance.Column(db_instance.String(2000), nullable=False)
    
    def __repr__(self):
        return f'<Greeting {self.id}>'
    
    def __str__(self):
        return f'{self.greeting} (ID: {self.id})'
# cGreetings

class User(cToolsdbBase):
    """
    User model for authentication with database columns.
    Inherit from UserMixin to get default implementations for:
    - is_authenticated, is_active, is_anonymous, get_id()
    """
    __bind_key__ =  cTools_bind_key
    __tablename__ = cTools_tablenames.get('User', 'users')

    id = db_instance.Column(db_instance.Integer, primary_key=True)
    username = db_instance.Column(db_instance.String(80), unique=True, nullable=False, index=True)
    email = db_instance.Column(db_instance.String(120), unique=True, nullable=False, index=True)
    password_hash = db_instance.Column(db_instance.String(255), nullable=False)
    FLDis_active = db_instance.Column(db_instance.Boolean, default=True, nullable=False)
    is_superuser = db_instance.Column(db_instance.Boolean, default=False, nullable=False)
    permissions = db_instance.Column(db_instance.String(1024), nullable=False, default='')
    menuGroup = db_instance.Column(db_instance.Integer, db_instance.ForeignKey(menuGroups.id), nullable=True)
    date_joined = db_instance.Column(db_instance.DateTime, default=datetime.now, nullable=False)
    last_login = db_instance.Column(db_instance.DateTime, nullable=True)

    @property
    def is_active(self):
        return self.FLDis_active
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash."""
        verdict = check_password_hash(self.password_hash, password)
        return verdict

    def has_permission(self, permission_name: str) -> bool:
        """Check if the user has a specific permission."""
        if self.is_superuser:
            return True  # Superusers have all permissions
        permissions_list = self.permissions.lower().split(',') if self.permissions else []
        return permission_name.lower() in permissions_list

    def update_last_login(self):
        """Update the last login timestamp."""
        self.last_login = datetime.now()
        db_instance.session.commit()

    def __repr__(self):
        return f'<User {self.username}>'

    def __init__(self, **kw: Any):
        """Initialize a user instance."""
        inspector = inspect(db_instance.engine)
        if not inspector.has_table(self.__tablename__):
            # If the table does not exist, create it
            db_instance.create_all()
        super().__init__(**kw)
# User
