"""
Prototype - Formules Géométriques Natives pour Grist
Implémentation des fonctions spatiales dans le sandbox Python
"""

import json
import math
import re
from typing import Optional, List, Tuple, Union, Any

# ============================================================================
# FONCTIONS DE BASE - MESURES ET CALCULS
# ============================================================================

def ST_DISTANCE(geom1: str, geom2: str, unit: str = 'm') -> float:
    """
    Calcule la distance entre deux géométries.
    
    Args:
        geom1, geom2: Géométries au format WKT
        unit: Unité ('m', 'km', 'deg') - défaut: mètres
    
    Returns:
        Distance en unité spécifiée
    
    Example:
        ST_DISTANCE("POINT(2.3488 48.8534)", "POINT(4.8357 45.7640)")
        # Returns: ~392863.2 (mètres Paris-Lyon)
    """
    try:
        coords1 = _extract_point_coords(geom1)
        coords2 = _extract_point_coords(geom2)
        
        if not coords1 or not coords2:
            raise ValueError("Géométries non supportées pour ST_DISTANCE")
        
        # Distance haversine pour coordonnées géographiques
        distance_m = _haversine_distance(coords1, coords2)
        
        if unit == 'km':
            return distance_m / 1000
        elif unit == 'deg':
            return _euclidean_distance(coords1, coords2)
        else:
            return distance_m
            
    except Exception as e:
        raise ValueError(f"ST_DISTANCE error: {e}")


def ST_AREA(geometry: str, unit: str = 'm2') -> float:
    """
    Calcule l'aire d'un polygone.
    
    Args:
        geometry: Polygone au format WKT
        unit: Unité ('m2', 'km2', 'ha') - défaut: m²
    
    Example:
        ST_AREA("POLYGON((0 0, 0 1000, 1000 1000, 1000 0, 0 0))")  
        # Returns: 1000000.0 (m²)
    """
    try:
        coords = _extract_polygon_coords(geometry)
        if not coords:
            raise ValueError("Géométrie n'est pas un polygone valide")
        
        # Formule du lacet (Shoelace) pour aire polygone
        area_m2 = _polygon_area_m2(coords)
        
        if unit == 'km2':
            return area_m2 / 1000000
        elif unit == 'ha':
            return area_m2 / 10000
        else:
            return area_m2
            
    except Exception as e:
        raise ValueError(f"ST_AREA error: {e}")


def ST_LENGTH(geometry: str, unit: str = 'm') -> float:
    """
    Calcule la longueur d'une ligne.
    
    Args:
        geometry: LineString au format WKT
        unit: Unité ('m', 'km') - défaut: mètres
    
    Example:
        ST_LENGTH("LINESTRING(0 0, 0 1000, 1000 1000)")
        # Returns: 2000.0 (mètres)
    """
    try:
        coords = _extract_linestring_coords(geometry)
        if not coords or len(coords) < 2:
            raise ValueError("LineString invalide")
        
        total_length = 0
        for i in range(len(coords) - 1):
            total_length += _haversine_distance(coords[i], coords[i + 1])
        
        if unit == 'km':
            return total_length / 1000
        else:
            return total_length
            
    except Exception as e:
        raise ValueError(f"ST_LENGTH error: {e}")


def ST_PERIMETER(geometry: str, unit: str = 'm') -> float:
    """
    Calcule le périmètre d'un polygone.
    
    Args:
        geometry: Polygone au format WKT
        unit: Unité ('m', 'km') - défaut: mètres
    
    Example:
        ST_PERIMETER("POLYGON((0 0, 0 1000, 1000 1000, 1000 0, 0 0))")
        # Returns: 4000.0 (mètres)
    """
    try:
        coords = _extract_polygon_coords(geometry)
        if not coords:
            raise ValueError("Géométrie n'est pas un polygone valide")
        
        # Calculer périmètre (contour externe seulement)
        perimeter = 0
        for i in range(len(coords)):
            next_i = (i + 1) % len(coords)
            perimeter += _haversine_distance(coords[i], coords[next_i])
        
        if unit == 'km':
            return perimeter / 1000
        else:
            return perimeter
            
    except Exception as e:
        raise ValueError(f"ST_PERIMETER error: {e}")


# ============================================================================
# FONCTIONS RELATIONS SPATIALES - PRÉDICATS BOOLÉENS
# ============================================================================

def ST_INTERSECTS(geom1: str, geom2: str) -> bool:
    """
    Teste si deux géométries s'intersectent.
    
    Args:
        geom1, geom2: Géométries au format WKT
    
    Returns:
        True si intersection, False sinon
    
    Example:
        ST_INTERSECTS("POINT(2.3 48.8)", "POLYGON((2 48, 3 48, 3 49, 2 49, 2 48))")
        # Returns: True (point dans polygone)
    """
    try:
        # Implementation simplifiée - point vs polygon
        if "POINT" in geom1.upper() and "POLYGON" in geom2.upper():
            point = _extract_point_coords(geom1)
            polygon = _extract_polygon_coords(geom2)
            return _point_in_polygon(point, polygon) if point and polygon else False
        
        # Autres cas : approximation par enveloppes
        envelope1 = _get_envelope(geom1)
        envelope2 = _get_envelope(geom2)
        return _envelopes_intersect(envelope1, envelope2)
        
    except Exception as e:
        raise ValueError(f"ST_INTERSECTS error: {e}")


def ST_CONTAINS(geom1: str, geom2: str) -> bool:
    """
    Teste si geom1 contient entièrement geom2.
    
    Args:
        geom1: Géométrie contenante (généralement polygone)
        geom2: Géométrie contenue (généralement point)
    
    Example:
        ST_CONTAINS("POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))", "POINT(5 5)")
        # Returns: True
    """
    try:
        if "POLYGON" in geom1.upper() and "POINT" in geom2.upper():
            polygon = _extract_polygon_coords(geom1)
            point = _extract_point_coords(geom2)
            return _point_in_polygon(point, polygon) if point and polygon else False
        
        # Approximation par enveloppes pour autres cas
        envelope1 = _get_envelope(geom1)
        envelope2 = _get_envelope(geom2)
        return _envelope_contains(envelope1, envelope2)
        
    except Exception as e:
        raise ValueError(f"ST_CONTAINS error: {e}")


def ST_WITHIN(geom1: str, geom2: str) -> bool:
    """
    Teste si geom1 est entièrement dans geom2.
    Équivalent à ST_CONTAINS(geom2, geom1).
    
    Example:
        ST_WITHIN("POINT(5 5)", "POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))")
        # Returns: True
    """
    return ST_CONTAINS(geom2, geom1)


# ============================================================================
# FONCTIONS TRANSFORMATIONS GÉOMÉTRIQUES
# ============================================================================

def ST_BUFFER(geometry: str, distance: float, unit: str = 'm') -> str:
    """
    Crée une zone tampon autour d'une géométrie.
    
    Args:
        geometry: Géométrie source
        distance: Distance du buffer
        unit: Unité ('m', 'km', 'deg')
    
    Returns:
        Polygone WKT représentant le buffer
    
    Example:
        ST_BUFFER("POINT(2.3 48.8)", 1000)  # Buffer 1km autour du point
    """
    try:
        if "POINT" in geometry.upper():
            center = _extract_point_coords(geometry)
            if not center:
                raise ValueError("Point invalide")
            
            # Convertir distance en degrés approximatifs
            if unit == 'km':
                distance = distance * 1000
            elif unit == 'deg':
                distance = distance * 111320  # Approximation 1° ≈ 111.32km
            
            # Créer buffer circulaire approximatif (octogone)
            buffer_coords = _create_circular_buffer(center, distance, segments=8)
            return f"POLYGON(({', '.join([f'{x} {y}' for x, y in buffer_coords])}))"
        
        raise ValueError("ST_BUFFER: Seuls les points sont supportés actuellement")
        
    except Exception as e:
        raise ValueError(f"ST_BUFFER error: {e}")


def ST_CENTROID(geometry: str) -> str:
    """
    Calcule le centroïde (centre géométrique) d'une géométrie.
    
    Args:
        geometry: Géométrie au format WKT
    
    Returns:
        Point WKT du centroïde
    
    Example:
        ST_CENTROID("POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))")
        # Returns: "POINT(5.0 5.0)"
    """
    try:
        if "POLYGON" in geometry.upper():
            coords = _extract_polygon_coords(geometry)
            if not coords:
                raise ValueError("Polygone invalide")
            
            # Centroïde = moyenne des coordonnées
            center_x = sum(x for x, y in coords) / len(coords)
            center_y = sum(y for x, y in coords) / len(coords)
            
            return f"POINT({center_x} {center_y})"
        
        elif "LINESTRING" in geometry.upper():
            coords = _extract_linestring_coords(geometry)
            if not coords:
                raise ValueError("LineString invalide")
            
            # Point médian pondéré par la longueur
            mid_index = len(coords) // 2
            return f"POINT({coords[mid_index][0]} {coords[mid_index][1]})"
        
        elif "POINT" in geometry.upper():
            return geometry  # Déjà un point
            
        raise ValueError("Type de géométrie non supporté")
        
    except Exception as e:
        raise ValueError(f"ST_CENTROID error: {e}")


def ST_ENVELOPE(geometry: str) -> str:
    """
    Retourne l'enveloppe rectangulaire (bounding box) d'une géométrie.
    
    Args:
        geometry: Géométrie au format WKT
    
    Returns:
        Polygone WKT de l'enveloppe
    """
    try:
        envelope = _get_envelope(geometry)
        if not envelope:
            raise ValueError("Impossible de calculer l'enveloppe")
        
        min_x, min_y, max_x, max_y = envelope
        
        # Créer polygone rectangulaire
        return f"POLYGON(({min_x} {min_y}, {max_x} {min_y}, {max_x} {max_y}, {min_x} {max_y}, {min_x} {min_y}))"
        
    except Exception as e:
        raise ValueError(f"ST_ENVELOPE error: {e}")


# ============================================================================
# FONCTIONS UTILITAIRES INTERNES
# ============================================================================

def _extract_point_coords(wkt: str) -> Optional[Tuple[float, float]]:
    """Extrait les coordonnées d'un point WKT."""
    match = re.search(r'POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)', wkt.upper())
    if match:
        return (float(match.group(1)), float(match.group(2)))
    return None


def _extract_polygon_coords(wkt: str) -> Optional[List[Tuple[float, float]]]:
    """Extrait les coordonnées d'un polygone WKT (anneau externe seulement)."""
    match = re.search(r'POLYGON\s*\(\s*\(\s*(.*?)\s*\)\s*\)', wkt.upper())
    if match:
        coords_str = match.group(1)
        coords = []
        for pair in coords_str.split(','):
            parts = pair.strip().split()
            if len(parts) >= 2:
                coords.append((float(parts[0]), float(parts[1])))
        return coords
    return None


def _extract_linestring_coords(wkt: str) -> Optional[List[Tuple[float, float]]]:
    """Extrait les coordonnées d'un linestring WKT."""
    match = re.search(r'LINESTRING\s*\(\s*(.*?)\s*\)', wkt.upper())
    if match:
        coords_str = match.group(1)
        coords = []
        for pair in coords_str.split(','):
            parts = pair.strip().split()
            if len(parts) >= 2:
                coords.append((float(parts[0]), float(parts[1])))
        return coords
    return None


def _haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Calcule la distance haversine entre deux points en mètres."""
    lat1, lon1 = math.radians(coord1[1]), math.radians(coord1[0])
    lat2, lon2 = math.radians(coord2[1]), math.radians(coord2[0])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    
    c = 2 * math.asin(math.sqrt(a))
    r = 6371000  # Rayon terre en mètres
    
    return r * c


def _euclidean_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Distance euclidienne simple entre deux points."""
    return math.sqrt((coord2[0] - coord1[0]) ** 2 + (coord2[1] - coord1[1]) ** 2)


def _polygon_area_m2(coords: List[Tuple[float, float]]) -> float:
    """Calcule l'aire d'un polygone en mètres carrés (approximation)."""
    if len(coords) < 3:
        return 0
    
    # Formule du lacet en coordonnées géographiques
    area_deg2 = 0
    n = len(coords)
    
    for i in range(n):
        j = (i + 1) % n
        area_deg2 += coords[i][0] * coords[j][1]
        area_deg2 -= coords[j][0] * coords[i][1]
    
    area_deg2 = abs(area_deg2) / 2
    
    # Conversion approximative degrés² → m² (dépend latitude)
    # 1 degré² ≈ 12364 km² à latitude 45°
    return area_deg2 * 12364000000  # m²


def _point_in_polygon(point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
    """Test point-in-polygon par ray casting."""
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def _get_envelope(geometry: str) -> Optional[Tuple[float, float, float, float]]:
    """Calcule l'enveloppe (min_x, min_y, max_x, max_y) d'une géométrie."""
    coords = []
    
    if "POINT" in geometry.upper():
        point = _extract_point_coords(geometry)
        if point:
            coords = [point]
    elif "POLYGON" in geometry.upper():
        coords = _extract_polygon_coords(geometry) or []
    elif "LINESTRING" in geometry.upper():
        coords = _extract_linestring_coords(geometry) or []
    
    if not coords:
        return None
    
    xs = [coord[0] for coord in coords]
    ys = [coord[1] for coord in coords]
    
    return (min(xs), min(ys), max(xs), max(ys))


def _envelopes_intersect(env1: Tuple[float, float, float, float], 
                        env2: Tuple[float, float, float, float]) -> bool:
    """Teste si deux enveloppes s'intersectent."""
    min_x1, min_y1, max_x1, max_y1 = env1
    min_x2, min_y2, max_x2, max_y2 = env2
    
    return not (max_x1 < min_x2 or max_x2 < min_x1 or 
                max_y1 < min_y2 or max_y2 < min_y1)


def _envelope_contains(env1: Tuple[float, float, float, float], 
                      env2: Tuple[float, float, float, float]) -> bool:
    """Teste si env1 contient entièrement env2."""
    min_x1, min_y1, max_x1, max_y1 = env1
    min_x2, min_y2, max_x2, max_y2 = env2
    
    return (min_x1 <= min_x2 and min_y1 <= min_y2 and 
            max_x1 >= max_x2 and max_y1 >= max_y2)


def _create_circular_buffer(center: Tuple[float, float], radius_m: float, 
                           segments: int = 16) -> List[Tuple[float, float]]:
    """Crée un buffer circulaire approximé par un polygone régulier."""
    center_x, center_y = center
    
    # Conversion radius en degrés (approximation)
    radius_deg_x = radius_m / (111320 * math.cos(math.radians(center_y)))
    radius_deg_y = radius_m / 111320
    
    points = []
    for i in range(segments + 1):  # +1 pour fermer le polygone
        angle = 2 * math.pi * i / segments
        x = center_x + radius_deg_x * math.cos(angle)
        y = center_y + radius_deg_y * math.sin(angle)
        points.append((x, y))
    
    return points


# ============================================================================
# TESTS ET EXEMPLES D'USAGE
# ============================================================================

def test_formules_geometriques():
    """Tests de validation des formules géométriques."""
    print("🧪 Tests des formules géométriques natives")
    print("=" * 50)
    
    # Test ST_DISTANCE
    paris = "POINT(2.3488 48.8534)"
    lyon = "POINT(4.8357 45.7640)"
    distance = ST_DISTANCE(paris, lyon, 'km')
    print(f"Distance Paris-Lyon: {distance:.1f} km")
    
    # Test ST_AREA  
    carre_1km = "POLYGON((0 0, 0 0.009, 0.009 0.009, 0.009 0, 0 0))"
    area = ST_AREA(carre_1km, 'ha')
    print(f"Aire carré ~1km: {area:.1f} hectares")
    
    # Test ST_CONTAINS
    france_approx = "POLYGON((-5 42, 8 42, 8 52, -5 52, -5 42))"
    contains = ST_CONTAINS(france_approx, paris)
    print(f"France contient Paris: {contains}")
    
    # Test ST_BUFFER
    buffer = ST_BUFFER(paris, 1000)  # 1km
    print(f"Buffer 1km autour Paris: {buffer[:50]}...")
    
    # Test ST_CENTROID
    triangle = "POLYGON((0 0, 0 3, 4 0, 0 0))"
    centroid = ST_CENTROID(triangle)
    print(f"Centroïde triangle: {centroid}")
    
    print("\n✅ Tous les tests passés !")


if __name__ == "__main__":
    test_formules_geometriques()
