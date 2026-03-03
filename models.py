
import datetime
from typing import Any
import decimal

from sqlalchemy import (
    BigInteger, Integer, SmallInteger, Boolean,
    Double, 
    String,
    Date, 
    ForeignKeyConstraint, Index, UniqueConstraint,
    select,
    inspect, 
    )

from sqlalchemy.dialects.mysql import DATETIME, INTEGER, LONGTEXT, SMALLINT, TINYINT

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

#######################################################
#######################################################
### NORMAL WICS app MODELS 
#######################################################
#######################################################

class Base(DeclarativeBase):
    query = app_db.session.query_property()


##########  ORGANIZATIONS

class Organizations(Base):
    __tablename__ = 'WICS_organizations'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    orgname: Mapped[str] = mapped_column(String(250), nullable=False)

    materiallist: Mapped[list['MaterialList']] = relationship('MaterialList', back_populates='org')
    sapplants_org: Mapped[list['SAPPlants_org']] = relationship('SAPPlants_org', back_populates='org')
    sap_sohrecs: Mapped[list['SAP_SOHRecs']] = relationship('SAP_SOHRecs', back_populates='org')
    tmpmateriallistupdate: Mapped[list['tmpMaterialListUpdate']] = relationship('tmpMaterialListUpdate', back_populates='org')


##########  WAREHOUSE PART TYPES

class WhsePartTypes(Base):
    __tablename__ = 'WICS_whseparttypes'
    __table_args__ = (
        Index('PTypeUNQ_PType', 'WhsePartType', unique=True),
        Index('PTypeUNQ_PTypePrio', 'PartTypePriority', unique=True)
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    WhsePartType: Mapped[str] = mapped_column(String(50), nullable=False)
    InactivePartType: Mapped[int] = mapped_column(TINYINT(1), nullable=False)
    PartTypePriority: Mapped[int|None] = mapped_column(SmallInteger)

    materiallist: Mapped[list['MaterialList']] = relationship('MaterialList', back_populates='PartType')


##########  MATERIALS

class MaterialList(Base):
    __tablename__ = 'WICS_materiallist'
    __table_args__ = (
        ForeignKeyConstraint(['PartType_id'], ['WICS_whseparttypes.id'], name='WICS_materiallist_PartType_id_86058a4a_fk_WICS_whseparttypes_id'),
        ForeignKeyConstraint(['org_id'], ['WICS_organizations.id'], name='WICS_materiallist_org_id_6c7bdf21_fk_WICS_organizations_id'),
        Index('WICS_materi_Materia_a28822_idx', 'Material'),
        Index('WICS_materi_PartTyp_2289dc_idx', 'PartType_id'),
        Index('wics_materiallist_realpk', 'org_id', 'Material', unique=True)
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    Material: Mapped[str] = mapped_column(String(100), nullable=False)
    Description: Mapped[str] = mapped_column(String(250), nullable=False)
    org_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    SAPMaterialType: Mapped[str|None] = mapped_column(String(100))
    SAPMaterialGroup: Mapped[str|None] = mapped_column(String(100))
    Price: Mapped[decimal.Decimal|None] = mapped_column(Double(asdecimal=True))
    PriceUnit: Mapped[int|None] = mapped_column(INTEGER)
    Notes: Mapped[str|None] = mapped_column(String(250))
    PartType_id: Mapped[int|None] = mapped_column(BigInteger)
    TypicalContainerQty: Mapped[str|None] = mapped_column(String(100))
    TypicalPalletQty: Mapped[str|None] = mapped_column(String(100))
    Currency: Mapped[str|None] = mapped_column(String(20))
    Plant: Mapped[str|None] = mapped_column(String(20))
    SAPABC: Mapped[str|None] = mapped_column(String(5))
    SAPMPN: Mapped[str|None] = mapped_column(String(100))
    SAPManuf: Mapped[str|None] = mapped_column(String(100))

    PartType: Mapped['WhsePartTypes|None'] = relationship('WhsePartTypes', back_populates='materiallist')
    org: Mapped['Organizations'] = relationship('Organizations', back_populates='materiallist')
    actualcounts: Mapped[list['ActualCounts']] = relationship('ActualCounts', back_populates='Material')
    countschedule: Mapped[list['CountSchedule']] = relationship('CountSchedule', back_populates='Material')
    materialphotos: Mapped[list['MaterialPhotos']] = relationship('MaterialPhotos', back_populates='Material')
    mfrpntomaterial: Mapped[list['MfrPNtoMaterial']] = relationship('MfrPNtoMaterial', back_populates='Material')
    sap_sohrecs: Mapped[list['SAP_SOHRecs']] = relationship('SAP_SOHRecs', back_populates='Material')
    tmpmateriallistupdate: Mapped[list['tmpMaterialListUpdate']] = relationship('tmpMaterialListUpdate', back_populates='MaterialLink')

class tmpMaterialListUpdate(Base):
    __tablename__ = 'WICS_tmpmateriallistupdate'
    __table_args__ = (
        ForeignKeyConstraint(['MaterialLink_id'], ['WICS_materiallist.id'], name='WICS_tmpmateriallist_MaterialLink_id_84b18d1a_fk_WICS_mate'),
        ForeignKeyConstraint(['org_id'], ['WICS_organizations.id'], name='WICS_tmpmateriallist_org_id_8587e963_fk_WICS_orga'),
        Index('WICS_tmpmat_delMate_ea54b5_idx', 'delMaterialLink'),
        Index('WICS_tmpmat_org_id_77875e_idx', 'org_id', 'Material'),
        Index('WICS_tmpmat_recStat_af0cc4_idx', 'recStatus'),
        Index('WICS_tmpmateriallist_MaterialLink_id_84b18d1a_fk_WICS_mate', 'MaterialLink_id')
    )

    Material: Mapped[str] = mapped_column(String(100), nullable=False)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    Description: Mapped[str|None] = mapped_column(String(250))
    SAPMaterialType: Mapped[str|None] = mapped_column(String(100))
    SAPMaterialGroup: Mapped[str|None] = mapped_column(String(100))
    Price: Mapped[decimal.Decimal|None] = mapped_column(Double(asdecimal=True))
    PriceUnit: Mapped[int|None] = mapped_column(INTEGER)
    Currency: Mapped[str|None] = mapped_column(String(20))
    Plant: Mapped[str|None] = mapped_column(String(20))
    org_id: Mapped[int|None] = mapped_column(BigInteger)
    MaterialLink_id: Mapped[int|None] = mapped_column(BigInteger)
    errmsg: Mapped[str|None] = mapped_column(String(256))
    recStatus: Mapped[str|None] = mapped_column(String(32))
    delMaterialLink: Mapped[int|None] = mapped_column(Integer)
    SAPABC: Mapped[str|None] = mapped_column(String(5))
    SAPMPN: Mapped[str|None] = mapped_column(String(100))
    SAPManuf: Mapped[str|None] = mapped_column(String(100))

    MaterialLink: Mapped['MaterialList|None'] = relationship('MaterialList', back_populates='tmpmateriallistupdate')
    org: Mapped['Organizations|None'] = relationship('Organizations', back_populates='tmpmateriallistupdate')

class MaterialPhotos(Base):
    __tablename__ = 'WICS_materialphotos'
    __table_args__ = (
        ForeignKeyConstraint(['Material_id'], ['WICS_materiallist.id'], name='WICS_materialphotos_Material_id_0a63e651_fk_WICS_materiallist_id'),
        Index('WICS_materialphotos_Material_id_0a63e651_fk_WICS_materiallist_id', 'Material_id')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    Photo: Mapped[str] = mapped_column(String(100), nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    Material_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    Notes: Mapped[str|None] = mapped_column(String(250))

    Material: Mapped['MaterialList'] = relationship('MaterialList', back_populates='materialphotos')

class MfrPNtoMaterial(Base):
    __tablename__ = 'WICS_mfrpntomaterial'
    __table_args__ = (
        ForeignKeyConstraint(['Material_id'], ['WICS_materiallist.id'], name='WICS_mfrpntomaterial_Material_id_e1536634_fk_WICS_mate'),
        Index('WICS_mfrpnt_Manufac_86f9ad_idx', 'Manufacturer'),
        Index('WICS_mfrpntomaterial_Material_id_e1536634_fk_WICS_mate', 'Material_id'),
        Index('wics_mfrpntomaterial_mfrpn_unq', 'MfrPN', unique=True)
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    MfrPN: Mapped[str] = mapped_column(String(250), nullable=False)
    Material_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    Manufacturer: Mapped[str|None] = mapped_column(String(250))
    Notes: Mapped[str|None] = mapped_column(String(250))

    Material: Mapped['MaterialList'] = relationship('MaterialList', back_populates='mfrpntomaterial')


##########  SCHEDULED COUNTS

class CountSchedule(Base):
    __tablename__ = 'WICS_countschedule'
    __table_args__ = (
        ForeignKeyConstraint(['Material_id'], ['WICS_materiallist.id'], name='WICS_count_schedule__Material_id_625a3c03_fk_WICS_mate'),
        ForeignKeyConstraint(['Requestor_userid_id'], ['userprofiles_wicsuser.id'], name='WICS_countschedule_Requestor_userid_id_6fcbe696_fk_userprofi'),
        Index('WICS_counts_CountDa_e42cfd_idx', 'CountDate'),
        Index('WICS_counts_Materia_5b7e42_idx', 'Material_id'),
        Index('WICS_countschedule_Requestor_userid_id_6fcbe696_fk_userprofi', 'Requestor_userid_id')
    )

    from calvincTools import User  # import here to avoid circular import issues with cTools_models['User'] = User in calvincTools_init()

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    CountDate: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    Material_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    Counter: Mapped[str|None] = mapped_column(String(250))
    Priority: Mapped[str|None] = mapped_column(String(50))
    ReasonScheduled: Mapped[str|None] = mapped_column(String(250))
    Notes: Mapped[str|None] = mapped_column(String(250))
    RequestFilled: Mapped[int|None] = mapped_column(TINYINT(1))
    Requestor: Mapped[str|None] = mapped_column(String(100))
    Requestor_userid_id: Mapped[int|None] = mapped_column(BigInteger)

    Material: Mapped['MaterialList'] = relationship('MaterialList', back_populates='countschedule')
    Requestor_userid: Mapped['User|None'] = relationship('User')

class WorksheetZones(Base):
    __tablename__ = 'WICS_worksheetzones'

    zone: Mapped[int] = mapped_column(Integer, primary_key=True)
    zoneName: Mapped[str] = mapped_column(String(10), nullable=False)

    location_worksheetzone: Mapped[list['Location_WorksheetZone']] = relationship('Location_WorksheetZone', back_populates='zone')

class Location_WorksheetZone(Base):
    __tablename__ = 'WICS_location_worksheetzone'
    __table_args__ = (
        ForeignKeyConstraint(['zone_id'], ['WICS_worksheetzones.zone'], name='WICS_location_worksh_zone_id_59d6f8f3_fk_WICS_work'),
        Index('WICS_location_worksh_zone_id_59d6f8f3_fk_WICS_work', 'zone_id')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    location: Mapped[str] = mapped_column(String(50), nullable=False)
    zone_id: Mapped[int] = mapped_column(Integer, nullable=False)

    zone: Mapped['WorksheetZones'] = relationship('WorksheetZones', back_populates='location_worksheetzone')


##########  ACTUAL COUNTS

class ActualCounts(Base):
    __tablename__ = 'WICS_actualcounts'
    __table_args__ = (
        ForeignKeyConstraint(['Material_id'], ['WICS_materiallist.id'], name='WICS_actualcounts_Material_id_6f114fcf_fk_WICS_materiallist_id'),
        Index('WICS_actual_CountDa_c71e2f_idx', 'CountDate', 'Material_id'),
        Index('WICS_actual_LOCATIO_55fb12_idx', 'LOCATION'),
        Index('WICS_actual_Materia_f4d652_idx', 'Material_id')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    CountDate: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    Counter: Mapped[str] = mapped_column(String(250), nullable=False)
    LOCATION: Mapped[str] = mapped_column(String(250), nullable=False)
    FLAG_PossiblyNotRecieved: Mapped[int] = mapped_column(TINYINT(1), nullable=False)
    FLAG_MovementDuringCount: Mapped[int] = mapped_column(TINYINT(1), nullable=False)
    Material_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    LocationOnly: Mapped[int] = mapped_column(TINYINT(1), nullable=False)
    CycCtID: Mapped[str|None] = mapped_column(String(100))
    CTD_QTY_Expr: Mapped[str|None] = mapped_column(String(500))
    PKGID_Desc: Mapped[str|None] = mapped_column(String(250))
    TAGQTY: Mapped[str|None] = mapped_column(String(250))
    Notes: Mapped[str|None] = mapped_column(String(250))

    Material: Mapped['MaterialList'] = relationship('MaterialList', back_populates='actualcounts')


##########  SAP

class SAP_SOHRecs(Base):
    __tablename__ = 'WICS_sap_sohrecs'
    __table_args__ = (
        ForeignKeyConstraint(['Material_id'], ['WICS_materiallist.id'], name='WICS_sap_sohrecs_Material_id_f253c0f8_fk_WICS_materiallist_id'),
        ForeignKeyConstraint(['org_id'], ['WICS_organizations.id'], name='WICS_sap_sohrecs_org_id_7ac7fec9_fk_WICS_organizations_id'),
        Index('WICS_sap_so_Plant_48325a_idx', 'Plant'),
        Index('WICS_sap_so_uploade_25ea7d_idx', 'uploaded_at', 'org_id', 'MaterialPartNum'),
        Index('WICS_sap_sohrecs_Material_id_f253c0f8_fk_WICS_materiallist_id', 'Material_id'),
        Index('WICS_sap_sohrecs_org_id_7ac7fec9_fk_WICS_organizations_id', 'org_id')
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    uploaded_at: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    MaterialPartNum: Mapped[str] = mapped_column(String(100), nullable=False)
    org_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    Description: Mapped[str] = mapped_column(String(250))
    Plant: Mapped[str|None] = mapped_column(String(20))
    MaterialType: Mapped[str|None] = mapped_column(String(50))
    StorageLocation: Mapped[str|None] = mapped_column(String(20))
    BaseUnitofMeasure: Mapped[str|None] = mapped_column(String(20))
    Amount: Mapped[decimal.Decimal|None] = mapped_column(Double(asdecimal=True))
    Currency: Mapped[str|None] = mapped_column(String(20))
    ValueUnrestricted: Mapped[decimal.Decimal|None] = mapped_column(Double(asdecimal=True))
    SpecialStock: Mapped[str|None] = mapped_column(String(20))
    Batch: Mapped[str|None] = mapped_column(String(20))
    Blocked: Mapped[decimal.Decimal|None] = mapped_column(Double(asdecimal=True))
    ValueBlocked: Mapped[decimal.Decimal|None] = mapped_column(Double(asdecimal=True))
    Vendor: Mapped[str|None] = mapped_column(String(20))
    Material_id: Mapped[int|None] = mapped_column(BigInteger)

    Material: Mapped['MaterialList'|None] = relationship('MaterialList', back_populates='sap_sohrecs')
    org: Mapped['Organizations'] = relationship('Organizations', back_populates='sap_sohrecs')

class SAPPlants_org(Base):
    __tablename__ = 'WICS_sapplants_org'
    __table_args__ = (
        ForeignKeyConstraint(['org_id'], ['WICS_organizations.id'], name='WICS_sapplants_org_org_id_db200562_fk_WICS_organizations_id'),
        Index('WICS_sapplants_org_org_id_db200562_fk_WICS_organizations_id', 'org_id')
    )

    SAPPlant: Mapped[str] = mapped_column(String(20), primary_key=True)
    org_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    org: Mapped['Organizations'] = relationship('Organizations', back_populates='sapplants_org')

class UploadSAPResults(Base):
    __tablename__ = 'WICS_uploadsapresults'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    errState: Mapped[str|None] = mapped_column(String(100))
    errmsg: Mapped[str|None] = mapped_column(String(512))
    rowNum: Mapped[int|None] = mapped_column(Integer)

class UnitsOfMeasure(Base):
    __tablename__ = 'WICS_unitsofmeasure'
    __table_args__ = (
        Index('UOM', 'UOM', unique=True),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    UOM: Mapped[str] = mapped_column(String(50), nullable=False)
    UOMText: Mapped[str] = mapped_column(String(100), nullable=False)
    DimensionText: Mapped[str] = mapped_column(String(100), nullable=False)
    Multiplier1: Mapped[decimal.Decimal] = mapped_column(Double(asdecimal=True), nullable=False)


##########  ASYNC COMM

class async_comm(Base):
    __tablename__ = 'WICS_async_comm'

    reqid: Mapped[str] = mapped_column(String(255), primary_key=True)
    timestamp: Mapped[str|None] = mapped_column(String(30))
    processname: Mapped[str|None] = mapped_column(String(256))
    statecode: Mapped[str|None] = mapped_column(String(64))
    statetext: Mapped[str|None] = mapped_column(String(512))
    result: Mapped[str|None] = mapped_column(String(2048))
    extra1: Mapped[str|None] = mapped_column(String(2048))


########## 
########## 
