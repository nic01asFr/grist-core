"""
Import et conversion de géométries avec Shapely et PyProj
Phase 2.7: Utilisation des bibliothèques standard géospatiales

Bibliothèques utilisées:
- Shapely 2.0+: Manipulation géométries (wrapper GEOS)
- PyProj 3.7+: Transformations coordonnées (wrapper PROJ)

Formats supportés:
- WKT (Well-Known Text): POINT(2.35 48.85)
- WKB (Well-Known Binary)
- GeoJSON: {"type": "Point", "coordinates": [2.35, 48.85]}
- Coordonnées séparées: lat/lon, X/Y

Référentiels (SRID/EPSG):
- EPSG:4326 (WGS84): GPS, lat/lon
- EPSG:3857 (Web Mercator): Google Maps, OSM
- EPSG:2154 (Lambert 93): France
- EPSG:27572 (Lambert II): ancienne France
"""

import json
import logging
from typing import Optional, Tuple, Union

log = logging.getLogger(__name__)

# Import conditionnel des bibliothèques géospatiales
try:
    from shapely import wkt, wkb
    from shapely.geometry import Point, LineString, Polygon, shape, mapping
    from shapely.geometry.base import BaseGeometry
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    log.warning("Shapely not available - using fallback implementations")

try:
    from pyproj import Transformer, CRS
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False
    log.warning("PyProj not available - SRID transformations disabled")


def parse_geometry(value: str) -> Optional[BaseGeometry]:
    """
    Parse une géométrie depuis différents formats vers Shapely.

    Args:
        value: Géométrie en WKT, GeoJSON, ou coordonnées

    Returns:
        Objet Shapely Geometry ou None
    """
    if not SHAPELY_AVAILABLE or not value:
        return None

    value = value.strip()

    # WKT
    try:
        return wkt.loads(value)
    except Exception:
        pass

    # GeoJSON
    try:
        geojson = json.loads(value)
        if isinstance(geojson, dict) and 'type' in geojson:
            return shape(geojson)
    except Exception:
        pass

    # Coordonnées simples "lon, lat" ou "lon lat"
    try:
        import re
        coord_match = re.match(r'^(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)$', value)
        if coord_match:
            lon, lat = float(coord_match.group(1)), float(coord_match.group(2))
            return Point(lon, lat)
    except Exception:
        pass

    return None


def transform_geometry(geom: BaseGeometry, source_crs: Union[int, str],
                       target_crs: Union[int, str]) -> Optional[BaseGeometry]:
    """
    Transforme une géométrie d'un CRS vers un autre avec PyProj.

    Args:
        geom: Géométrie Shapely
        source_crs: CRS source (code EPSG ou string PROJ)
        target_crs: CRS cible

    Returns:
        Géométrie transformée ou None
    """
    if not PYPROJ_AVAILABLE or not geom:
        return geom

    try:
        # Convertir les codes EPSG en strings si nécessaire
        if isinstance(source_crs, int):
            source_crs = f"EPSG:{source_crs}"
        if isinstance(target_crs, int):
            target_crs = f"EPSG:{target_crs}"

        # Créer le transformateur (avec cache automatique PyProj)
        transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)

        # Transformer les coordonnées
        from shapely.ops import transform
        return transform(transformer.transform, geom)

    except Exception as e:
        log.debug(f"Transformation {source_crs} → {target_crs} failed: {e}")
        return geom


def detect_crs_from_coordinates(lon: float, lat: float) -> int:
    """
    Détecte le CRS probable depuis les valeurs de coordonnées.

    Heuristiques:
    - WGS84: -180 < lon < 180, -90 < lat < 90
    - Web Mercator: valeurs > 20M (mètres)
    - Lambert 93: X ~ 100k-1.3M, Y ~ 6M-7.2M
    - Lambert II: X ~ 0-1.3M, Y ~ 1.6M-2.8M

    Returns:
        Code EPSG (4326 par défaut)
    """
    # WGS84 (degrés décimaux)
    if -180 <= lon <= 180 and -90 <= lat <= 90:
        return 4326

    # Web Mercator (mètres, grandes valeurs)
    if abs(lon) > 20000000 or abs(lat) > 20000000:
        return 3857

    # Lambert 93 France (mètres)
    if 100000 <= lon <= 1300000 and 6000000 <= lat <= 7200000:
        return 2154

    # Lambert II étendu (mètres)
    if 0 <= lon <= 1300000 and 1600000 <= lat <= 2800000:
        return 27572

    # Par défaut WGS84
    return 4326


# ===== Fonctions exportées pour Grist =====

def ST_GeomFromText(wkt_string: str, srid: int = 4326) -> str:
    """
    Crée une géométrie depuis WKT (standard PostGIS/SpatiaLite).

    Args:
        wkt_string: Well-Known Text (ex: 'POINT(2.35 48.85)')
        srid: Code EPSG (défaut 4326 = WGS84)

    Returns:
        WKT normalisé

    Exemples:
        ST_GeomFromText('POINT(2.35 48.85)')
        ST_GeomFromText('LINESTRING(0 0, 1 1, 2 2)', 4326)
    """
    if not wkt_string:
        return ''

    if not SHAPELY_AVAILABLE:
        return wkt_string  # Fallback: retourne tel quel

    try:
        geom = wkt.loads(wkt_string)
        return wkt.dumps(geom)  # Normalise le WKT
    except Exception:
        return wkt_string


def ST_AsText(geometry: str) -> str:
    """
    Convertit n'importe quelle géométrie en WKT standard.

    Args:
        geometry: Géométrie (WKT, GeoJSON, coordonnées)

    Returns:
        WKT standard

    Exemples:
        ST_AsText('{"type":"Point","coordinates":[2.35,48.85]}')
        → 'POINT (2.35 48.85)'
    """
    if not geometry:
        return ''

    geom = parse_geometry(geometry)
    if geom and SHAPELY_AVAILABLE:
        return wkt.dumps(geom)
    return geometry


def ST_GeomFromGeoJSON(geojson_string: str) -> str:
    """
    Convertit GeoJSON en WKT.

    Args:
        geojson_string: Chaîne GeoJSON

    Returns:
        WKT

    Exemples:
        ST_GeomFromGeoJSON('{"type":"Point","coordinates":[2.35,48.85]}')
        → 'POINT (2.35 48.85)'
    """
    if not geojson_string or not SHAPELY_AVAILABLE:
        return ''

    try:
        geojson = json.loads(geojson_string)
        geom = shape(geojson)
        return wkt.dumps(geom)
    except Exception:
        return ''


def ST_AsGeoJSON(wkt_geometry: str) -> str:
    """
    Convertit WKT en GeoJSON.

    Args:
        wkt_geometry: Géométrie WKT

    Returns:
        Chaîne GeoJSON

    Exemples:
        ST_AsGeoJSON('POINT(2.35 48.85)')
        → '{"type":"Point","coordinates":[2.35,48.85]}'
    """
    if not wkt_geometry or not SHAPELY_AVAILABLE:
        return ''

    try:
        geom = wkt.loads(wkt_geometry)
        return json.dumps(mapping(geom))
    except Exception:
        return ''


def ST_Transform(geometry: str, source_srid: int, target_srid: int) -> str:
    """
    Transforme une géométrie d'un CRS vers un autre (PyProj/PROJ).

    Args:
        geometry: Géométrie WKT
        source_srid: Code EPSG source
        target_srid: Code EPSG cible

    Returns:
        Géométrie transformée en WKT

    Exemples:
        ST_Transform($geom, 2154, 4326)  # Lambert93 → WGS84
        ST_Transform('POINT(654321 6857890)', 2154, 4326)
        → 'POINT (2.35 48.85)'
    """
    if not geometry or not SHAPELY_AVAILABLE:
        return geometry

    if source_srid == target_srid:
        return geometry

    try:
        geom = parse_geometry(geometry)
        if not geom:
            return geometry

        transformed = transform_geometry(geom, source_srid, target_srid)
        if transformed:
            return wkt.dumps(transformed)
    except Exception as e:
        log.debug(f"ST_Transform error: {e}")

    return geometry


def MAKE_POINT(lat: float, lon: float, output_format: str = 'WKT') -> str:
    """
    Crée un POINT depuis latitude/longitude.

    Args:
        lat: Latitude (degrés décimaux, -90 à 90)
        lon: Longitude (degrés décimaux, -180 à 180)
        output_format: 'WKT' ou 'GeoJSON'

    Returns:
        Géométrie POINT

    Exemples:
        MAKE_POINT(48.85, 2.35) → 'POINT (2.35 48.85)'
        MAKE_POINT($latitude, $longitude, 'GeoJSON')
    """
    if lat is None or lon is None:
        return ''

    if not SHAPELY_AVAILABLE:
        # Fallback simple
        if output_format.upper() == 'GEOJSON':
            return json.dumps({"type": "Point", "coordinates": [lon, lat]})
        return f"POINT({lon} {lat})"

    point = Point(lon, lat)

    if output_format.upper() == 'GEOJSON':
        return json.dumps(mapping(point))
    return wkt.dumps(point)


def DETECT_CRS(geometry: str, column_hint: str = '') -> int:
    """
    Détecte le CRS/SRID probable d'une géométrie.

    Args:
        geometry: Géométrie
        column_hint: Nom de colonne (peut contenir des indices)

    Returns:
        Code EPSG (4326 si indéterminé)

    Exemples:
        DETECT_CRS('POINT(654321 6857890)') → 2154 (Lambert93)
        DETECT_CRS('POINT(2.35 48.85)') → 4326 (WGS84)
        DETECT_CRS($geom, $column_name)
    """
    # Indices dans le nom de colonne
    if column_hint:
        hint = column_hint.lower()
        if '4326' in hint or 'wgs84' in hint or 'gps' in hint:
            return 4326
        elif '3857' in hint or 'mercator' in hint or 'webmercator' in hint:
            return 3857
        elif '2154' in hint or 'lambert93' in hint or 'l93' in hint:
            return 2154
        elif '27572' in hint or 'lambert2' in hint or 'l2e' in hint:
            return 27572

    # Extraction des coordonnées
    if not geometry:
        return 4326

    geom = parse_geometry(geometry)
    if geom and hasattr(geom, 'x') and hasattr(geom, 'y'):
        return detect_crs_from_coordinates(geom.x, geom.y)

    return 4326


def GEOMETRY_TYPE(geometry: str) -> str:
    """
    Retourne le type de géométrie.

    Args:
        geometry: Géométrie WKT ou GeoJSON

    Returns:
        Type: 'Point', 'LineString', 'Polygon', etc.

    Exemples:
        GEOMETRY_TYPE('POINT(2.35 48.85)') → 'Point'
        GEOMETRY_TYPE('LINESTRING(0 0, 1 1)') → 'LineString'
    """
    if not geometry or not SHAPELY_AVAILABLE:
        return ''

    geom = parse_geometry(geometry)
    if geom:
        return geom.geom_type
    return ''


def IS_VALID(geometry: str) -> bool:
    """
    Vérifie si une géométrie est valide (topologie).

    Args:
        geometry: Géométrie WKT

    Returns:
        True si valide

    Exemples:
        IS_VALID('POINT(2.35 48.85)') → True
        IS_VALID('POLYGON((0 0, 1 1, 0 0))') → False (< 4 points)
    """
    if not geometry or not SHAPELY_AVAILABLE:
        return False

    geom = parse_geometry(geometry)
    return geom.is_valid if geom else False


def ST_Distance_Shapely(geom1_wkt: str, geom2_wkt: str, use_geodesic: bool = True) -> float:
    """
    Calcule la distance entre deux géométries avec Shapely + PyProj.

    Args:
        geom1_wkt: Première géométrie WKT
        geom2_wkt: Deuxième géométrie WKT
        use_geodesic: Si True, utilise distance géodésique (WGS84), sinon planaire

    Returns:
        Distance en mètres (0 si erreur)

    Note:
        Pour distances géodésiques précises, les géométries doivent être en EPSG:4326.
        Si en autre CRS, transformez d'abord avec ST_Transform().
    """
    if not SHAPELY_AVAILABLE or not geom1_wkt or not geom2_wkt:
        return 0.0

    try:
        geom1 = parse_geometry(geom1_wkt)
        geom2 = parse_geometry(geom2_wkt)

        if not geom1 or not geom2:
            return 0.0

        if use_geodesic and PYPROJ_AVAILABLE:
            # Distance géodésique avec PyProj (précise sur ellipsoïde WGS84)
            from pyproj import Geod
            geod = Geod(ellps='WGS84')

            # Pour points simples
            if geom1.geom_type == 'Point' and geom2.geom_type == 'Point':
                lon1, lat1 = geom1.x, geom1.y
                lon2, lat2 = geom2.x, geom2.y
                _, _, distance = geod.inv(lon1, lat1, lon2, lat2)
                return abs(distance)
            else:
                # Pour géométries complexes, utiliser Shapely distance puis facteur correction
                # (approximation acceptable pour petites distances)
                planar_dist = geom1.distance(geom2)
                # Conversion degrés → mètres à latitude moyenne
                lat_avg = (geom1.centroid.y + geom2.centroid.y) / 2
                meters_per_degree = 111320 * abs(planar_dist)  # approximation
                return meters_per_degree
        else:
            # Distance planaire Shapely (unités du CRS)
            return geom1.distance(geom2)

    except Exception as e:
        log.debug(f"ST_Distance_Shapely error: {e}")
        return 0.0


def ST_Area_Shapely(geom_wkt: str, use_geodesic: bool = True) -> float:
    """
    Calcule l'aire d'une géométrie avec Shapely + PyProj.

    Args:
        geom_wkt: Géométrie WKT (POLYGON, MULTIPOLYGON)
        use_geodesic: Si True, projette en UTM pour calcul précis en m²

    Returns:
        Aire en mètres carrés (0 si erreur)
    """
    if not SHAPELY_AVAILABLE or not geom_wkt:
        return 0.0

    try:
        geom = parse_geometry(geom_wkt)
        if not geom or geom.is_empty:
            return 0.0

        if use_geodesic and PYPROJ_AVAILABLE and geom.geom_type in ('Polygon', 'MultiPolygon'):
            # Projeter en UTM approprié pour calcul aire précise
            # Déterminer zone UTM depuis centroid
            centroid = geom.centroid
            lon, lat = centroid.x, centroid.y

            # Calculer zone UTM
            utm_zone = int((lon + 180) / 6) + 1
            utm_epsg = 32600 + utm_zone if lat >= 0 else 32700 + utm_zone

            # Projeter en UTM
            geom_utm = transform_geometry(geom, 4326, utm_epsg)
            if geom_utm:
                return geom_utm.area

        # Fallback: aire planaire
        return geom.area

    except Exception as e:
        log.debug(f"ST_Area_Shapely error: {e}")
        return 0.0


def ST_Length_Shapely(geom_wkt: str, use_geodesic: bool = True) -> float:
    """
    Calcule la longueur d'une géométrie linéaire.

    Args:
        geom_wkt: Géométrie WKT (LINESTRING, MULTILINESTRING)
        use_geodesic: Si True, projette en UTM pour calcul précis

    Returns:
        Longueur en mètres
    """
    if not SHAPELY_AVAILABLE or not geom_wkt:
        return 0.0

    try:
        geom = parse_geometry(geom_wkt)
        if not geom:
            return 0.0

        if use_geodesic and PYPROJ_AVAILABLE:
            # Projeter en UTM
            centroid = geom.centroid
            lon, lat = centroid.x, centroid.y
            utm_zone = int((lon + 180) / 6) + 1
            utm_epsg = 32600 + utm_zone if lat >= 0 else 32700 + utm_zone

            geom_utm = transform_geometry(geom, 4326, utm_epsg)
            if geom_utm:
                return geom_utm.length

        return geom.length

    except Exception as e:
        log.debug(f"ST_Length_Shapely error: {e}")
        return 0.0


def ST_Contains_Shapely(geom1_wkt: str, geom2_wkt: str) -> bool:
    """
    Teste si geom1 contient entièrement geom2.

    Args:
        geom1_wkt: Géométrie contenante WKT
        geom2_wkt: Géométrie contenue WKT

    Returns:
        True si geom1 contient geom2
    """
    if not SHAPELY_AVAILABLE or not geom1_wkt or not geom2_wkt:
        return False

    try:
        geom1 = parse_geometry(geom1_wkt)
        geom2 = parse_geometry(geom2_wkt)

        if not geom1 or not geom2:
            return False

        return geom1.contains(geom2)

    except Exception as e:
        log.debug(f"ST_Contains_Shapely error: {e}")
        return False


def ST_Intersects_Shapely(geom1_wkt: str, geom2_wkt: str) -> bool:
    """Teste si deux géométries s'intersectent."""
    if not SHAPELY_AVAILABLE or not geom1_wkt or not geom2_wkt:
        return False

    try:
        geom1 = parse_geometry(geom1_wkt)
        geom2 = parse_geometry(geom2_wkt)
        return geom1.intersects(geom2) if geom1 and geom2 else False
    except Exception as e:
        log.debug(f"ST_Intersects_Shapely error: {e}")
        return False


def ST_Within_Shapely(geom1_wkt: str, geom2_wkt: str) -> bool:
    """Teste si geom1 est entièrement dans geom2."""
    if not SHAPELY_AVAILABLE or not geom1_wkt or not geom2_wkt:
        return False

    try:
        geom1 = parse_geometry(geom1_wkt)
        geom2 = parse_geometry(geom2_wkt)
        return geom1.within(geom2) if geom1 and geom2 else False
    except Exception as e:
        log.debug(f"ST_Within_Shapely error: {e}")
        return False


def ST_Crosses_Shapely(geom1_wkt: str, geom2_wkt: str) -> bool:
    """Teste si deux géométries se croisent."""
    if not SHAPELY_AVAILABLE or not geom1_wkt or not geom2_wkt:
        return False

    try:
        geom1 = parse_geometry(geom1_wkt)
        geom2 = parse_geometry(geom2_wkt)
        return geom1.crosses(geom2) if geom1 and geom2 else False
    except Exception as e:
        log.debug(f"ST_Crosses_Shapely error: {e}")
        return False


def ST_Touches_Shapely(geom1_wkt: str, geom2_wkt: str) -> bool:
    """Teste si deux géométries se touchent (frontière commune)."""
    if not SHAPELY_AVAILABLE or not geom1_wkt or not geom2_wkt:
        return False

    try:
        geom1 = parse_geometry(geom1_wkt)
        geom2 = parse_geometry(geom2_wkt)
        return geom1.touches(geom2) if geom1 and geom2 else False
    except Exception as e:
        log.debug(f"ST_Touches_Shapely error: {e}")
        return False


def ST_Buffer_Shapely(geom_wkt: str, distance_meters: float) -> str:
    """
    Crée une zone tampon autour d'une géométrie.

    Args:
        geom_wkt: Géométrie WKT
        distance_meters: Distance du buffer en mètres

    Returns:
        Géométrie buffered en WKT
    """
    if not SHAPELY_AVAILABLE or not geom_wkt:
        return ''

    try:
        geom = parse_geometry(geom_wkt)
        if not geom:
            return ''

        # Si en WGS84, projeter en UTM pour buffer métrique précis
        if PYPROJ_AVAILABLE:
            centroid = geom.centroid
            lon, lat = centroid.x, centroid.y
            utm_zone = int((lon + 180) / 6) + 1
            utm_epsg = 32600 + utm_zone if lat >= 0 else 32700 + utm_zone

            # Projeter → buffer → re-projeter
            geom_utm = transform_geometry(geom, 4326, utm_epsg)
            if geom_utm:
                buffered_utm = geom_utm.buffer(distance_meters)
                buffered_wgs84 = transform_geometry(buffered_utm, utm_epsg, 4326)
                if buffered_wgs84:
                    return wkt.dumps(buffered_wgs84)

        # Fallback: buffer en degrés (approximation)
        buffered = geom.buffer(distance_meters / 111320)  # mètres → degrés approximatif
        return wkt.dumps(buffered)

    except Exception as e:
        log.debug(f"ST_Buffer_Shapely error: {e}")
        return ''


def ST_Centroid_Shapely(geom_wkt: str) -> str:
    """
    Calcule le centroïde d'une géométrie.

    Returns:
        POINT WKT du centroïde
    """
    if not SHAPELY_AVAILABLE or not geom_wkt:
        return ''

    try:
        geom = parse_geometry(geom_wkt)
        if not geom:
            return ''

        centroid = geom.centroid
        return wkt.dumps(centroid)

    except Exception as e:
        log.debug(f"ST_Centroid_Shapely error: {e}")
        return ''


def ST_Simplify_Shapely(geom_wkt: str, tolerance: float) -> str:
    """
    Simplifie une géométrie (Douglas-Peucker).

    Args:
        geom_wkt: Géométrie WKT
        tolerance: Tolérance de simplification

    Returns:
        Géométrie simplifiée WKT
    """
    if not SHAPELY_AVAILABLE or not geom_wkt:
        return ''

    try:
        geom = parse_geometry(geom_wkt)
        if not geom:
            return ''

        simplified = geom.simplify(tolerance, preserve_topology=True)
        return wkt.dumps(simplified)

    except Exception as e:
        log.debug(f"ST_Simplify_Shapely error: {e}")
        return ''


def ST_Union_Shapely(geom1_wkt: str, geom2_wkt: str) -> str:
    """Fusionne deux géométries."""
    if not SHAPELY_AVAILABLE or not geom1_wkt or not geom2_wkt:
        return ''

    try:
        geom1 = parse_geometry(geom1_wkt)
        geom2 = parse_geometry(geom2_wkt)

        if not geom1 or not geom2:
            return ''

        union = geom1.union(geom2)
        return wkt.dumps(union)

    except Exception as e:
        log.debug(f"ST_Union_Shapely error: {e}")
        return ''


def ST_Intersection_Shapely(geom1_wkt: str, geom2_wkt: str) -> str:
    """Retourne l'intersection de deux géométries."""
    if not SHAPELY_AVAILABLE or not geom1_wkt or not geom2_wkt:
        return ''

    try:
        geom1 = parse_geometry(geom1_wkt)
        geom2 = parse_geometry(geom2_wkt)

        if not geom1 or not geom2:
            return ''

        intersection = geom1.intersection(geom2)
        if intersection.is_empty:
            return ''

        return wkt.dumps(intersection)

    except Exception as e:
        log.debug(f"ST_Intersection_Shapely error: {e}")
        return ''


def ST_X_Shapely(point_wkt: str) -> float:
    """Extrait la coordonnée X d'un POINT."""
    if not SHAPELY_AVAILABLE or not point_wkt:
        return 0.0

    try:
        geom = parse_geometry(point_wkt)
        if geom and geom.geom_type == 'Point':
            return geom.x
        return 0.0
    except Exception:
        return 0.0


def ST_Y_Shapely(point_wkt: str) -> float:
    """Extrait la coordonnée Y d'un POINT."""
    if not SHAPELY_AVAILABLE or not point_wkt:
        return 0.0

    try:
        geom = parse_geometry(point_wkt)
        if geom and geom.geom_type == 'Point':
            return geom.y
        return 0.0
    except Exception:
        return 0.0


def ST_MakePoint_Shapely(x: float, y: float) -> str:
    """Crée un POINT depuis coordonnées X/Y."""
    if not SHAPELY_AVAILABLE:
        return ''

    try:
        point = Point(x, y)
        return wkt.dumps(point)
    except Exception:
        return ''


def ST_Perimeter_Shapely(geom_wkt: str, use_geodesic: bool = True) -> float:
    """
    Calcule le périmètre d'un polygone.

    Returns:
        Périmètre en mètres
    """
    if not SHAPELY_AVAILABLE or not geom_wkt:
        return 0.0

    try:
        geom = parse_geometry(geom_wkt)
        if not geom:
            return 0.0

        # Le périmètre = longueur de la frontière externe
        if geom.geom_type in ('Polygon', 'MultiPolygon'):
            if use_geodesic and PYPROJ_AVAILABLE:
                # Projeter en UTM
                centroid = geom.centroid
                lon, lat = centroid.x, centroid.y
                utm_zone = int((lon + 180) / 6) + 1
                utm_epsg = 32600 + utm_zone if lat >= 0 else 32700 + utm_zone

                geom_utm = transform_geometry(geom, 4326, utm_epsg)
                if geom_utm:
                    return geom_utm.length  # Pour polygones, length = périmètre

            return geom.length

        return 0.0

    except Exception as e:
        log.debug(f"ST_Perimeter_Shapely error: {e}")
        return 0.0


# Export pour Grist
__all__ = [
    # Import/Export
    'ST_GeomFromText',
    'ST_AsText',
    'ST_GeomFromGeoJSON',
    'ST_AsGeoJSON',
    'ST_Transform',
    'MAKE_POINT',
    'DETECT_CRS',
    'GEOMETRY_TYPE',
    'IS_VALID',
    # Spatial operations (Shapely-based)
    'ST_Distance_Shapely',
    'ST_Area_Shapely',
    'ST_Length_Shapely',
    'ST_Perimeter_Shapely',
    'ST_Contains_Shapely',
    'ST_Intersects_Shapely',
    'ST_Within_Shapely',
    'ST_Crosses_Shapely',
    'ST_Touches_Shapely',
    'ST_Buffer_Shapely',
    'ST_Centroid_Shapely',
    'ST_Simplify_Shapely',
    'ST_Union_Shapely',
    'ST_Intersection_Shapely',
    'ST_X_Shapely',
    'ST_Y_Shapely',
    'ST_MakePoint_Shapely',
]
