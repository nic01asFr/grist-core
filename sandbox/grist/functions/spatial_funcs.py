"""
Fonctions spatiales SpatiaLite pour Grist
Phase 2: 20 fonctions ST_* optimisées avec SpatiaLite via RPC Python

Ces fonctions sont disponibles dans les formules Grist pour manipuler
des géométries géographiques (points, lignes, polygones).
"""

# Import des fonctions spatiales depuis usertypes (module parent)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from usertypes import (
    ST_DISTANCE,
    ST_AREA,
    ST_CONTAINS,
    ST_CENTROID,
    ST_INTERSECTS,
    ST_WITHIN,
    ST_CROSSES,
    ST_TOUCHES,
    ST_BUFFER,
    ST_UNION,
    ST_INTERSECTION,
    ST_SIMPLIFY,
    ST_LENGTH,
    ST_PERIMETER,
    ST_X,
    ST_Y,
    ST_MAKEPOINT,
    ST_GEOMFROMGEOJSON,
    ST_ASGEOJSON,
    ST_ISVALID,
)

# Export explicite pour __all__
__all__ = [
    'ST_DISTANCE',
    'ST_AREA',
    'ST_CONTAINS',
    'ST_CENTROID',
    'ST_INTERSECTS',
    'ST_WITHIN',
    'ST_CROSSES',
    'ST_TOUCHES',
    'ST_BUFFER',
    'ST_UNION',
    'ST_INTERSECTION',
    'ST_SIMPLIFY',
    'ST_LENGTH',
    'ST_PERIMETER',
    'ST_X',
    'ST_Y',
    'ST_MAKEPOINT',
    'ST_GEOMFROMGEOJSON',
    'ST_ASGEOJSON',
    'ST_ISVALID',
]
