
_pkgname='WICS4'
_base_ver_major=1
_base_ver_minor=0
_base_ver_patch='0'
_ver_date='2026-03-10-0900'
# _base_ver = f'{_base_ver_major}.{_base_ver_minor}.{_base_ver_patch}'
_base_ver = f'{_ver_date}'      # date versioning until things get stable, then switch to semantic versioning
__version__ = _base_ver
sysver = {
    'DEV': f'DEV{_base_ver}', 
    'PROD': _base_ver,
    'DEMO': f'DEMO{_base_ver}'
    } 

__author__ = "Calvin C"
__email__ = "calvinc404@gmail.com"

# PLANNED CHANGES
# =================


# Changelog:
# Version - Date - Description
# 1.0.0 - 2026-mm-dd - Initial version
