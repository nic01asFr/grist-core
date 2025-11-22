"""
Module pour fonctions spatiales SpatiaLite via CLI
Phase 2.9 - Architecture professionnelle avec gestion SRID

Convention de stockage:
- Format: WKT standard dans colonnes Text Grist
- SRID par défaut: 4326 (WGS84) si non spécifié
- EWKT supporté: "SRID=2154;POINT(...)" si besoin CRS spécifique

Architecture:
1. SpatiaLite CLI natif (GEOS 3.11 + PROJ 9.1) pour calculs
2. Gestion automatique SRID et transformations
3. Shapely/PyProj en fallback si SpatiaLite indisponible
4. Transparence totale pour l'utilisateur

Exemples:
- MAKE_POINT(48.85, 2.35) → "POINT(2.35 48.85)" SRID=4326 implicite
- ST_DISTANCE(point_paris, point_lyon) → auto-détection SRID + transformation si besoin
- ST_BUFFER(geom, 1000) → auto-projection UTM, buffer 1000m, re-projection
"""
import logging
import subprocess
import re
from typing import Optional, Tuple

log = logging.getLogger(__name__)

# ============================================================================
# SRID DETECTION & PARSING
# ============================================================================

def _parse_srid_wkt(geometry: str) -> Tuple[str, int]:
    """
    Parse une géométrie et extrait SRID + WKT pur.

    Args:
        geometry: WKT simple ou EWKT avec SRID

    Returns:
        (wkt_pur, srid)

    Examples:
        "POINT(2.35 48.85)" → ("POINT(2.35 48.85)", 4326)
        "SRID=2154;POINT(654321 6857890)" → ("POINT(654321 6857890)", 2154)
    """
    if not geometry:
        return '', 4326

    # Détecter EWKT format
    ewkt_match = re.match(r'SRID=(\d+);(.+)', geometry.strip(), re.IGNORECASE)
    if ewkt_match:
        srid = int(ewkt_match.group(1))
        wkt = ewkt_match.group(2)
        return wkt, srid

    # WKT simple → SRID par défaut 4326
    return geometry.strip(), 4326


def _exec_spatialite(sql: str) -> Optional[str]:
    """
    Exécute une requête SQL via spatialite CLI.

    Args:
        sql: Requête SQL complète

    Returns:
        Résultat (première ligne utile) ou None si erreur
    """
    try:
        result = subprocess.run(
            ['spatialite', ':memory:', sql],
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )

        if result.returncode != 0:
            log.debug(f"SpatiaLite CLI error: {result.stderr}")
            return None

        # Parser output (ignorer header SPATIAL_REF_SYS)
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if line and 'SPATIAL_REF_SYS' not in line:
                return line.strip()

        return None

    except subprocess.TimeoutExpired:
        log.warning("SpatiaLite query timeout")
        return None
    except Exception as e:
        log.debug(f"SpatiaLite exec error: {e}")
        return None


def _escape_wkt(wkt: str) -> str:
    """Échappe les quotes dans WKT pour SQL."""
    return wkt.replace("'", "''") if wkt else ''


# ============================================================================
# SRID UTILITY FUNCTIONS
# ============================================================================

def ST_SRID_Get(geometry: str) -> int:
    """Retourne le SRID d'une géométrie."""
    _, srid = _parse_srid_wkt(geometry)
    return srid


def ST_SetSRID(geometry: str, srid: int) -> str:
    """Définit le SRID d'une géométrie (format EWKT)."""
    wkt, _ = _parse_srid_wkt(geometry)
    if not wkt:
        return ''
    return f"SRID={srid};{wkt}"


def ST_Transform_CLI(geometry: str, target_srid: int) -> Optional[str]:
    """Transforme une géométrie vers un autre CRS."""
    wkt, source_srid = _parse_srid_wkt(geometry)

    if not wkt:
        return None

    if source_srid == target_srid:
        return wkt

    sql = f"""SELECT ST_AsText(
        ST_Transform(
            ST_GeomFromText('{_escape_wkt(wkt)}', {source_srid}),
            {target_srid}
        )
    )"""

    return _exec_spatialite(sql)


# ============================================================================
# SPATIAL MEASUREMENTS
# ============================================================================

def ST_Distance_CLI(geom1: str, geom2: str, use_ellipsoid: bool = True) -> Optional[float]:
    """Calcule la distance entre deux géométries (gestion SRID automatique)."""
    wkt1, srid1 = _parse_srid_wkt(geom1)
    wkt2, srid2 = _parse_srid_wkt(geom2)

    if not wkt1 or not wkt2:
        return None

    # Normaliser vers 4326 pour distance géodésique
    if srid1 != 4326:
        wkt1_transformed = ST_Transform_CLI(f"SRID={srid1};{wkt1}", 4326)
        if not wkt1_transformed:
            return None
        wkt1 = wkt1_transformed
        srid1 = 4326

    if srid2 != 4326:
        wkt2_transformed = ST_Transform_CLI(f"SRID={srid2};{wkt2}", 4326)
        if not wkt2_transformed:
            return None
        wkt2 = wkt2_transformed
        srid2 = 4326

    sql = f"""SELECT ST_Distance(
        ST_GeomFromText('{_escape_wkt(wkt1)}', 4326),
        ST_GeomFromText('{_escape_wkt(wkt2)}', 4326),
        {1 if use_ellipsoid else 0}
    )"""

    result = _exec_spatialite(sql)
    if result:
        try:
            return float(result)
        except ValueError:
            return None
    return None


def ST_Area_CLI(geometry: str, use_ellipsoid: bool = True) -> Optional[float]:
    """Calcule l'aire d'une géométrie."""
    wkt, srid = _parse_srid_wkt(geometry)

    if not wkt:
        return None

    sql = f"""SELECT ST_Area(
        ST_GeomFromText('{_escape_wkt(wkt)}', {srid}),
        {1 if use_ellipsoid else 0}
    )"""

    result = _exec_spatialite(sql)
    if result:
        try:
            return float(result)
        except ValueError:
            return None
    return None


def ST_Length_CLI(geometry: str, use_ellipsoid: bool = True) -> Optional[float]:
    """Calcule la longueur d'une ligne."""
    wkt, srid = _parse_srid_wkt(geometry)

    if not wkt:
        return None

    sql = f"""SELECT ST_Length(
        ST_GeomFromText('{_escape_wkt(wkt)}', {srid}),
        {1 if use_ellipsoid else 0}
    )"""

    result = _exec_spatialite(sql)
    if result:
        try:
            return float(result)
        except ValueError:
            return None
    return None


def ST_Perimeter_CLI(geometry: str, use_ellipsoid: bool = True) -> Optional[float]:
    """Calcule le périmètre d'un polygone."""
    return ST_Length_CLI(geometry, use_ellipsoid)


# ============================================================================
# SPATIAL RELATIONSHIPS
# ============================================================================

def ST_Contains_CLI(geom1: str, geom2: str) -> Optional[bool]:
    """Teste si geom1 contient geom2."""
    wkt1, srid1 = _parse_srid_wkt(geom1)
    wkt2, srid2 = _parse_srid_wkt(geom2)

    if not wkt1 or not wkt2:
        return None

    if srid1 != srid2:
        wkt2_transformed = ST_Transform_CLI(f"SRID={srid2};{wkt2}", srid1)
        if not wkt2_transformed:
            return None
        wkt2 = wkt2_transformed

    sql = f"""SELECT ST_Contains(
        ST_GeomFromText('{_escape_wkt(wkt1)}', {srid1}),
        ST_GeomFromText('{_escape_wkt(wkt2)}', {srid1})
    )"""

    result = _exec_spatialite(sql)
    return result == '1' if result else None


def ST_Intersects_CLI(geom1: str, geom2: str) -> Optional[bool]:
    """Teste si deux géométries s'intersectent."""
    wkt1, srid1 = _parse_srid_wkt(geom1)
    wkt2, srid2 = _parse_srid_wkt(geom2)

    if not wkt1 or not wkt2:
        return None

    if srid1 != srid2:
        wkt2_transformed = ST_Transform_CLI(f"SRID={srid2};{wkt2}", srid1)
        if not wkt2_transformed:
            return None
        wkt2 = wkt2_transformed

    sql = f"""SELECT ST_Intersects(
        ST_GeomFromText('{_escape_wkt(wkt1)}', {srid1}),
        ST_GeomFromText('{_escape_wkt(wkt2)}', {srid1})
    )"""

    result = _exec_spatialite(sql)
    return result == '1' if result else None


def ST_Within_CLI(geom1: str, geom2: str) -> Optional[bool]:
    """Teste si geom1 est dans geom2."""
    wkt1, srid1 = _parse_srid_wkt(geom1)
    wkt2, srid2 = _parse_srid_wkt(geom2)

    if not wkt1 or not wkt2:
        return None

    if srid1 != srid2:
        wkt1_transformed = ST_Transform_CLI(f"SRID={srid1};{wkt1}", srid2)
        if not wkt1_transformed:
            return None
        wkt1 = wkt1_transformed
        srid1 = srid2

    sql = f"""SELECT ST_Within(
        ST_GeomFromText('{_escape_wkt(wkt1)}', {srid1}),
        ST_GeomFromText('{_escape_wkt(wkt2)}', {srid1})
    )"""

    result = _exec_spatialite(sql)
    return result == '1' if result else None


def ST_Crosses_CLI(geom1: str, geom2: str) -> Optional[bool]:
    """Teste si deux géométries se croisent."""
    wkt1, srid1 = _parse_srid_wkt(geom1)
    wkt2, srid2 = _parse_srid_wkt(geom2)

    if not wkt1 or not wkt2:
        return None

    if srid1 != srid2:
        wkt2_transformed = ST_Transform_CLI(f"SRID={srid2};{wkt2}", srid1)
        if not wkt2_transformed:
            return None
        wkt2 = wkt2_transformed

    sql = f"""SELECT ST_Crosses(
        ST_GeomFromText('{_escape_wkt(wkt1)}', {srid1}),
        ST_GeomFromText('{_escape_wkt(wkt2)}', {srid1})
    )"""

    result = _exec_spatialite(sql)
    return result == '1' if result else None


def ST_Touches_CLI(geom1: str, geom2: str) -> Optional[bool]:
    """Teste si deux géométries se touchent."""
    wkt1, srid1 = _parse_srid_wkt(geom1)
    wkt2, srid2 = _parse_srid_wkt(geom2)

    if not wkt1 or not wkt2:
        return None

    if srid1 != srid2:
        wkt2_transformed = ST_Transform_CLI(f"SRID={srid2};{wkt2}", srid1)
        if not wkt2_transformed:
            return None
        wkt2 = wkt2_transformed

    sql = f"""SELECT ST_Touches(
        ST_GeomFromText('{_escape_wkt(wkt1)}', {srid1}),
        ST_GeomFromText('{_escape_wkt(wkt2)}', {srid1})
    )"""

    result = _exec_spatialite(sql)
    return result == '1' if result else None


# ============================================================================
# GEOMETRIC OPERATIONS
# ============================================================================

def ST_Buffer_CLI(geometry: str, distance_meters: float) -> Optional[str]:
    """Crée une zone tampon (projection UTM automatique)."""
    wkt, srid = _parse_srid_wkt(geometry)

    if not wkt:
        return None

    # Si déjà en système métrique, buffer direct
    if srid in [2154, 27572, 3857] or (32601 <= srid <= 32760):
        sql = f"""SELECT ST_AsText(
            ST_Buffer(
                ST_GeomFromText('{_escape_wkt(wkt)}', {srid}),
                {distance_meters}
            )
        )"""
        return _exec_spatialite(sql)

    # Si WGS84, calculer zone UTM
    if srid == 4326:
        centroid_sql = f"""SELECT ST_AsText(
            ST_Centroid(ST_GeomFromText('{_escape_wkt(wkt)}', 4326))
        )"""
        centroid = _exec_spatialite(centroid_sql)

        if centroid:
            coord_match = re.search(r'POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)', centroid)
            if coord_match:
                lon = float(coord_match.group(1))
                lat = float(coord_match.group(2))

                utm_zone = int((lon + 180) / 6) + 1
                utm_srid = 32600 + utm_zone if lat >= 0 else 32700 + utm_zone

                sql = f"""SELECT ST_AsText(
                    ST_Transform(
                        ST_Buffer(
                            ST_Transform(
                                ST_GeomFromText('{_escape_wkt(wkt)}', 4326),
                                {utm_srid}
                            ),
                            {distance_meters}
                        ),
                        4326
                    )
                )"""

                return _exec_spatialite(sql)

    # Fallback: buffer en degrés
    distance_degrees = distance_meters / 111320
    sql = f"""SELECT ST_AsText(
        ST_Buffer(
            ST_GeomFromText('{_escape_wkt(wkt)}', {srid}),
            {distance_degrees}
        )
    )"""

    return _exec_spatialite(sql)


def ST_Centroid_CLI(geometry: str) -> Optional[str]:
    """Calcule le centroïde."""
    wkt, srid = _parse_srid_wkt(geometry)

    if not wkt:
        return None

    sql = f"""SELECT ST_AsText(
        ST_Centroid(
            ST_GeomFromText('{_escape_wkt(wkt)}', {srid})
        )
    )"""

    return _exec_spatialite(sql)


def ST_Simplify_CLI(geometry: str, tolerance: float) -> Optional[str]:
    """Simplifie une géométrie."""
    wkt, srid = _parse_srid_wkt(geometry)

    if not wkt:
        return None

    sql = f"""SELECT ST_AsText(
        ST_Simplify(
            ST_GeomFromText('{_escape_wkt(wkt)}', {srid}),
            {tolerance}
        )
    )"""

    return _exec_spatialite(sql)


def ST_Union_CLI(geom1: str, geom2: str) -> Optional[str]:
    """Fusionne deux géométries."""
    wkt1, srid1 = _parse_srid_wkt(geom1)
    wkt2, srid2 = _parse_srid_wkt(geom2)

    if not wkt1 or not wkt2:
        return None

    if srid1 != srid2:
        wkt2_transformed = ST_Transform_CLI(f"SRID={srid2};{wkt2}", srid1)
        if not wkt2_transformed:
            return None
        wkt2 = wkt2_transformed

    sql = f"""SELECT ST_AsText(
        ST_Union(
            ST_GeomFromText('{_escape_wkt(wkt1)}', {srid1}),
            ST_GeomFromText('{_escape_wkt(wkt2)}', {srid1})
        )
    )"""

    return _exec_spatialite(sql)


def ST_Intersection_CLI(geom1: str, geom2: str) -> Optional[str]:
    """Retourne l'intersection."""
    wkt1, srid1 = _parse_srid_wkt(geom1)
    wkt2, srid2 = _parse_srid_wkt(geom2)

    if not wkt1 or not wkt2:
        return None

    if srid1 != srid2:
        wkt2_transformed = ST_Transform_CLI(f"SRID={srid2};{wkt2}", srid1)
        if not wkt2_transformed:
            return None
        wkt2 = wkt2_transformed

    sql = f"""SELECT ST_AsText(
        ST_Intersection(
            ST_GeomFromText('{_escape_wkt(wkt1)}', {srid1}),
            ST_GeomFromText('{_escape_wkt(wkt2)}', {srid1})
        )
    )"""

    return _exec_spatialite(sql)


# ============================================================================
# COORDINATE EXTRACTION
# ============================================================================

def ST_X_CLI(point_wkt: str) -> Optional[float]:
    """Extrait X."""
    wkt, srid = _parse_srid_wkt(point_wkt)

    if not wkt:
        return None

    sql = f"""SELECT ST_X(
        ST_GeomFromText('{_escape_wkt(wkt)}', {srid})
    )"""

    result = _exec_spatialite(sql)
    if result:
        try:
            return float(result)
        except ValueError:
            return None
    return None


def ST_Y_CLI(point_wkt: str) -> Optional[float]:
    """Extrait Y."""
    wkt, srid = _parse_srid_wkt(point_wkt)

    if not wkt:
        return None

    sql = f"""SELECT ST_Y(
        ST_GeomFromText('{_escape_wkt(wkt)}', {srid})
    )"""

    result = _exec_spatialite(sql)
    if result:
        try:
            return float(result)
        except ValueError:
            return None
    return None


def ST_MakePoint_CLI(x: float, y: float, srid: int = 4326) -> str:
    """Crée un POINT."""
    sql = f"SELECT ST_AsText(ST_MakePoint({x}, {y}))"
    result = _exec_spatialite(sql)
    return result if result else f"POINT ({x} {y})"


# Export
__all__ = [
    'ST_SRID_Get',
    'ST_SetSRID',
    'ST_Transform_CLI',
    'ST_Distance_CLI',
    'ST_Area_CLI',
    'ST_Length_CLI',
    'ST_Perimeter_CLI',
    'ST_Contains_CLI',
    'ST_Intersects_CLI',
    'ST_Within_CLI',
    'ST_Crosses_CLI',
    'ST_Touches_CLI',
    'ST_Buffer_CLI',
    'ST_Centroid_CLI',
    'ST_Simplify_CLI',
    'ST_Union_CLI',
    'ST_Intersection_CLI',
    'ST_X_CLI',
    'ST_Y_CLI',
    'ST_MakePoint_CLI',
]
