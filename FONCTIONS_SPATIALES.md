# Fonctions Spatiales Grist - Documentation Complète

**Phase 2 terminée** : 30+ fonctions géospatiales disponibles dans Grist
Technologie : **Shapely 2.0.6 + PyProj 3.7.0 + SpatiaLite 5.0.1**

---

## 🌍 Import et Conversion de Données

### MAKE_POINT(lat, lon, format='WKT')
Crée un point depuis latitude/longitude.

```python
MAKE_POINT(48.85, 2.35)
# → 'POINT (2.35 48.85)'

MAKE_POINT($latitude, $longitude)
# Utilise les colonnes du tableau

MAKE_POINT(48.85, 2.35, 'GeoJSON')
# → '{"type":"Point","coordinates":[2.35,48.85]}'
```

**Cas d'usage** : Importer des données depuis Excel/CSV avec colonnes lat/lon séparées.

---

### ST_GeomFromText(wkt, srid=4326)
Crée une géométrie depuis WKT (Well-Known Text).

```python
ST_GeomFromText('POINT(2.35 48.85)')
ST_GeomFromText('LINESTRING(0 0, 1 1, 2 2)')
ST_GeomFromText('POLYGON((0 0, 4 0, 4 4, 0 4, 0 0))')
```

---

### ST_AsText(geometry)
Convertit n'importe quelle géométrie en WKT standard.

```python
ST_AsText('{"type":"Point","coordinates":[2.35,48.85]}')
# → 'POINT (2.35 48.85)'
```

**Cas d'usage** : Normaliser des géométries GeoJSON vers WKT.

---

### ST_GeomFromGeoJSON(geojson)
Convertit GeoJSON en WKT.

```python
ST_GeomFromGeoJSON('{"type":"Point","coordinates":[2.35,48.85]}')
# → 'POINT (2.35 48.85)'
```

---

### ST_AsGeoJSON(wkt)
Convertit WKT en GeoJSON.

```python
ST_AsGeoJSON('POINT(2.35 48.85)')
# → '{"type":"Point","coordinates":[2.35,48.85]}'
```

**Cas d'usage** : Export pour cartes web (Leaflet, Mapbox).

---

## 🗺️ Transformations de Référentiels (SRID/EPSG)

### ST_Transform(geometry, source_srid, target_srid)
Transforme une géométrie d'un système de coordonnées vers un autre.

```python
# Lambert 93 (France) → WGS84 (GPS)
ST_Transform('POINT(654321 6857890)', 2154, 4326)
# → 'POINT (2.378 48.819)'

# WGS84 → Web Mercator (Google Maps)
ST_Transform($geom, 4326, 3857)

# Lambert II étendu → WGS84
ST_Transform($geom, 27572, 4326)
```

**Référentiels courants** :
- **4326** : WGS84 (GPS, lat/lon en degrés)
- **3857** : Web Mercator (cartes web, mètres)
- **2154** : Lambert 93 (France officiel, mètres)
- **27572** : Lambert II étendu (ancienne France, mètres)

---

### DETECT_CRS(geometry, column_hint='')
Détecte automatiquement le référentiel d'une géométrie.

```python
DETECT_CRS('POINT(2.35 48.85)')
# → 4326 (WGS84)

DETECT_CRS('POINT(654321 6857890)')
# → 2154 (Lambert 93)

DETECT_CRS($geom, $nom_colonne)
# Utilise le nom de colonne comme indice
```

**Indices automatiques** :
- Colonnes nommées `*_wgs84`, `*_l93`, `*_gps` → détection automatique
- Valeurs -180 à 180 / -90 à 90 → WGS84
- Grandes valeurs (> 20M) → Web Mercator
- X:100k-1.3M, Y:6M-7.2M → Lambert 93

---

## 📏 Mesures et Calculs

### ST_DISTANCE(geom1, geom2, unit='m')
Calcule la distance entre deux géométries.

```python
ST_DISTANCE('POINT(2.35 48.85)', 'POINT(2.29 48.86)', 'm')
# → 4521.3 (mètres)

ST_DISTANCE($point1, $point2, 'km')
# → 4.521 (kilomètres)

ST_DISTANCE($point1, $point2, 'miles')
# → 2.810 (miles)
```

**Unités** : `m`, `km`, `miles`, `nm` (nautical miles)

---

### ST_AREA(geometry, unit='m2')
Calcule l'aire d'un polygone.

```python
ST_AREA('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))', 'm2')
# → 100.0 (mètres carrés)

ST_AREA($polygone, 'km2')
# Hectares : utilisez 'ha'
```

---

### ST_LENGTH(geometry, unit='m')
Calcule la longueur d'une ligne.

```python
ST_LENGTH('LINESTRING(0 0, 10 0, 10 10)', 'm')
# → 20.0

ST_LENGTH($ligne, 'km')
```

---

### ST_PERIMETER(geometry, unit='m')
Calcule le périmètre d'un polygone.

```python
ST_PERIMETER('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))', 'm')
# → 40.0
```

---

## 🔍 Tests Topologiques

### ST_CONTAINS(geom1, geom2)
Teste si geom1 contient geom2.

```python
ST_CONTAINS($departement, $ville)
# → True si la ville est dans le département
```

---

### ST_INTERSECTS(geom1, geom2)
Teste si deux géométries s'intersectent.

```python
ST_INTERSECTS($zone1, $zone2)
# → True s'ils se chevauchent
```

---

### ST_WITHIN(geom1, geom2)
Teste si geom1 est entièrement dans geom2.

```python
ST_WITHIN($point, $zone)
# → True si le point est dans la zone
```

---

### ST_CROSSES(geom1, geom2)
Teste si deux géométries se croisent.

```python
ST_CROSSES($route, $riviere)
```

---

### ST_TOUCHES(geom1, geom2)
Teste si deux géométries se touchent (frontières communes).

```python
ST_TOUCHES($parcelle1, $parcelle2)
```

---

## 🛠️ Opérations Géométriques

### ST_BUFFER(geometry, distance, unit='m')
Crée une zone tampon autour d'une géométrie.

```python
ST_BUFFER('POINT(2.35 48.85)', 1000, 'm')
# → Cercle de 1km de rayon

ST_BUFFER($point, 500, 'm')
# Zone de 500m autour du point
```

---

### ST_CENTROID(geometry)
Retourne le centre géométrique.

```python
ST_CENTROID('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))')
# → 'POINT (5 5)'

ST_CENTROID($zone)
# Centre de la zone
```

---

### ST_SIMPLIFY(geometry, tolerance)
Simplifie une géométrie (algorithme Douglas-Peucker).

```python
ST_SIMPLIFY($geometrie_detaillee, 0.001)
# Simplifie en gardant les points importants
```

---

### ST_UNION(geom1, geom2)
Fusionne deux géométries.

```python
ST_UNION($zone1, $zone2)
# → Géométrie combinée
```

---

### ST_INTERSECTION(geom1, geom2)
Retourne l'intersection de deux géométries.

```python
ST_INTERSECTION($zone1, $zone2)
# → Zone commune
```

---

## 🧰 Utilitaires

### ST_X(point), ST_Y(point)
Extrait les coordonnées X/Y d'un point.

```python
ST_X('POINT(2.35 48.85)')
# → 2.35

ST_Y('POINT(2.35 48.85)')
# → 48.85

# Utilisation pratique:
$longitude = ST_X($point)
$latitude = ST_Y($point)
```

---

### GEOMETRY_TYPE(geometry)
Retourne le type de géométrie.

```python
GEOMETRY_TYPE('POINT(2.35 48.85)')
# → 'Point'

GEOMETRY_TYPE('LINESTRING(0 0, 1 1)')
# → 'LineString'

GEOMETRY_TYPE($geom)
# → 'Point', 'LineString', 'Polygon', etc.
```

---

### IS_VALID(geometry)
Vérifie si une géométrie est topologiquement valide.

```python
IS_VALID('POINT(2.35 48.85)')
# → True

IS_VALID('POLYGON((0 0, 1 1, 0 0))')
# → False (< 4 points requis)
```

---

### ST_ISVALID(geometry)
Alias de IS_VALID.

```python
ST_ISVALID($geom)
```

---

## 📊 Exemples Pratiques

### Exemple 1 : Importer des données GPS
Vous avez un CSV avec colonnes `latitude` et `longitude` :

```python
$geometrie = MAKE_POINT($latitude, $longitude)
```

### Exemple 2 : Calculer la distance entre points
```python
$distance_km = ST_DISTANCE($point_depart, $point_arrivee, 'km')
```

### Exemple 3 : Trouver les points dans une zone
```python
$dans_zone = ST_WITHIN($point, $polygone_zone)
# Utiliser comme filtre dans les formules
```

### Exemple 4 : Transformer Lambert 93 vers GPS
```python
$gps = ST_Transform($geom_lambert93, 2154, 4326)
```

### Exemple 5 : Créer une zone de 500m autour d'un point
```python
$zone_500m = ST_BUFFER($point, 500, 'm')
```

### Exemple 6 : Convertir pour export web
```python
$geojson = ST_AsGeoJSON($geometrie)
# Utiliser dans cartes Leaflet/Mapbox
```

### Exemple 7 : Détecter automatiquement le système de coordonnées
```python
$srid = DETECT_CRS($geometrie)
# Puis transformer si nécessaire
$wgs84 = ST_Transform($geometrie, $srid, 4326)
```

---

## 🎯 Workflows Complets

### Workflow : Import de données géoréférencées

1. **Données avec lat/lon séparées** :
   ```python
   $geom = MAKE_POINT($lat, $lon)
   ```

2. **Données en Lambert 93** :
   ```python
   $geom = ST_GeomFromText(f"POINT({$X} {$Y})")
   $geom_wgs84 = ST_Transform($geom, 2154, 4326)
   ```

3. **Données GeoJSON** :
   ```python
   $geom = ST_GeomFromGeoJSON($geojson_column)
   ```

### Workflow : Analyse spatiale

1. **Trouver les magasins dans un rayon de 5km** :
   ```python
   ST_DISTANCE($magasin.localisation, $client.adresse, 'km') < 5
   ```

2. **Calculer la surface d'une parcelle** :
   ```python
   ST_AREA($parcelle, 'ha')  # Hectares
   ```

3. **Vérifier si une adresse est dans une commune** :
   ```python
   ST_WITHIN($adresse, $commune.geometrie)
   ```

---

## 📚 Référence des SRID/EPSG Français

| Code  | Nom              | Usage                | Type      |
|-------|------------------|----------------------|-----------|
| 4326  | WGS84            | GPS, web             | Degrés    |
| 3857  | Web Mercator     | Google Maps, OSM     | Mètres    |
| 2154  | Lambert 93       | France métropolitaine| Mètres    |
| 27572 | Lambert II étendu| Ancienne France      | Mètres    |
| 32631 | UTM Zone 31N     | France ouest         | Mètres    |

---

## 🔧 Technologies Utilisées

- **Shapely 2.0.6** : Manipulation géométries (wrapper GEOS C++)
- **PyProj 3.7.0** : Transformations coordonnées (wrapper PROJ)
- **SpatiaLite 5.0.1** : SQL spatial (200+ fonctions PostGIS)
- **GEOS 3.11** : Algorithmes géométriques
- **PROJ 9.1** : Projections cartographiques

---

## 📞 Support

- **Documentation Shapely** : https://shapely.readthedocs.io
- **Documentation PyProj** : https://pyproj4.github.io/pyproj
- **Référence PostGIS** : https://postgis.net/docs/reference.html
- **EPSG.io** : https://epsg.io (recherche de codes SRID)

---

**Mis à jour** : Phase 2 complète - 30+ fonctions spatiales opérationnelles
