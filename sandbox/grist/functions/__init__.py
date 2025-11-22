# pylint: disable=wildcard-import, unused-argument
from .date import *
from .info import *
from .logical import *
from .lookup import *
from .math import *
from .stats import *
from .text import *
from .schedule import *
from .prevnext import *   # pylint: disable=import-error
from .spatial_funcs import *  # Phase 2: Fonctions spatiales SpatiaLite (20 fonctions ST_*)
from .geo_import import *     # Phase 2.7: Import/conversion géométries (Shapely + PyProj)

# Export all uppercase names, for use with `from functions import *`.
__all__ = [k for k in dir() if not k.startswith('_') and k.isupper()]
