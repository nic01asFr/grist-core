# Geospatial Functions in Grist

This document describes the geospatial capabilities added to Grist, enabling spatial data analysis and geographic computations directly within spreadsheet formulas.

## Overview

Grist now supports 30+ spatial functions for working with geographic data, including:
- Point, Line, and Polygon geometries
- Distance and area calculations
- Spatial relationships (contains, intersects, within)
- Coordinate system transformations (WGS84, Lambert93, Web Mercator)
- Import/export in WKT and GeoJSON formats

## Technology Stack

### Core Libraries
- **Shapely 2.0.6**: Geometry manipulation and operations (GEOS wrapper)
- **PyProj 3.7.0**: Coordinate reference system transformations (PROJ wrapper)
- **SpatiaLite 5.0.1**: SQL spatial functions (PostGIS-compatible)
- **GEOS 3.11**: Computational geometry engine
- **PROJ 9.1**: Cartographic projections library

### Architecture

The implementation uses a **hybrid approach**:
1. **Python layer** (Shapely/PyProj): Parsing, validation, transformations
2. **RPC layer** (sandbox): Secure execution of spatial operations
3. **SpatiaLite CLI**: Fallback for complex operations via subprocess

Note: `mod_spatialite` cannot be loaded as a SQLite extension in node-sqlite3 due to version conflicts with the statically-compiled SQLite. All spatial operations are therefore executed via Python.

## Installation

### System Dependencies (Dockerfile)

```dockerfile
RUN apt-get install -y \
  libspatialite7 \
  libsqlite3-mod-spatialite \
  spatialite-bin \
  libgeos-dev \
  libproj-dev \
  proj-bin
```

### Python Dependencies (requirements.txt)

```
shapely==2.0.6
pyproj==3.7.0
```

## Function Categories

### 1. Import and Data Conversion

#### `MAKE_POINT(lat, lon, format='WKT')`
Create a point from latitude/longitude coordinates.

```python
MAKE_POINT(48.8584, 2.2945)
# → 'POINT (2.2945 48.8584)'

MAKE_POINT($latitude, $longitude, 'GeoJSON')
# → '{"type":"Point","coordinates":[2.2945,48.8584]}'
```

**Use case**: Import CSV data with separate lat/lon columns.

---

#### `ST_GeomFromText(wkt, srid=4326)`
Parse Well-Known Text into a geometry.

```python
ST_GeomFromText('POINT(2.35 48.85)')
ST_GeomFromText('LINESTRING(0 0, 1 1, 2 2)')
ST_GeomFromText('POLYGON((0 0, 4 0, 4 4, 0 4, 0 0))')
```

---

#### `ST_AsText(geometry)`
Convert any geometry to standard WKT.

```python
ST_AsText('{"type":"Point","coordinates":[2.35,48.85]}')
# → 'POINT (2.35 48.85)'
```

---

#### `ST_GeomFromGeoJSON(geojson)`
Convert GeoJSON to WKT.

```python
ST_GeomFromGeoJSON('{"type":"Point","coordinates":[2.35,48.85]}')
# → 'POINT (2.35 48.85)'
```

---

#### `ST_AsGeoJSON(wkt)`
Convert WKT to GeoJSON.

```python
ST_AsGeoJSON('POINT(2.35 48.85)')
# → '{"type":"Point","coordinates":[2.35,48.85]}'
```

**Use case**: Export for web mapping (Leaflet, Mapbox).

---

### 2. Coordinate Reference Systems (CRS)

#### `ST_Transform(geometry, source_srid, target_srid)`
Transform geometry between coordinate systems.

```python
# Lambert 93 (France) → WGS84 (GPS)
ST_Transform('POINT(654321 6857890)', 2154, 4326)
# → 'POINT (2.378 48.819)'

# WGS84 → Web Mercator
ST_Transform($geom, 4326, 3857)
```

**Common EPSG codes**:
- **4326**: WGS84 (GPS, lat/lon degrees)
- **3857**: Web Mercator (web maps, meters)
- **2154**: Lambert 93 (France official, meters)
- **27572**: Lambert II extended (legacy France, meters)

---

#### `DETECT_CRS(geometry, column_hint='')`
Auto-detect coordinate reference system.

```python
DETECT_CRS('POINT(2.35 48.85)')  # → 4326 (WGS84)
DETECT_CRS('POINT(654321 6857890)')  # → 2154 (Lambert 93)
```

**Detection heuristics**:
- Values -180 to 180 / -90 to 90 → WGS84
- Large values (> 20M) → Web Mercator
- X: 100k-1.3M, Y: 6M-7.2M → Lambert 93

---

### 3. Measurements

#### `ST_DISTANCE(geom1, geom2, unit='m')`
Calculate distance between geometries.

```python
ST_DISTANCE('POINT(2.35 48.85)', 'POINT(2.29 48.86)', 'm')
# → 4521.3 (meters)

ST_DISTANCE($point1, $point2, 'km')
# → 4.521 (kilometers)
```

**Units**: `m`, `km`, `miles`, `nm` (nautical miles)

---

#### `ST_AREA(geometry, unit='m2')`
Calculate polygon area.

```python
ST_AREA('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))', 'm2')
# → 100.0 (square meters)

ST_AREA($polygon, 'ha')  # hectares
```

---

#### `ST_LENGTH(geometry, unit='m')`
Calculate line length.

```python
ST_LENGTH('LINESTRING(0 0, 10 0, 10 10)', 'm')
# → 20.0
```

---

#### `ST_PERIMETER(geometry, unit='m')`
Calculate polygon perimeter.

```python
ST_PERIMETER('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))', 'm')
# → 40.0
```

---

### 4. Spatial Relationships

#### `ST_CONTAINS(geom1, geom2)`
Test if geom1 contains geom2.

```python
ST_CONTAINS($department, $city)
# → True if city is inside department
```

---

#### `ST_INTERSECTS(geom1, geom2)`
Test if geometries intersect.

```python
ST_INTERSECTS($zone1, $zone2)
# → True if they overlap
```

---

#### `ST_WITHIN(geom1, geom2)`
Test if geom1 is entirely within geom2.

```python
ST_WITHIN($point, $zone)
# → True if point is inside zone
```

---

#### `ST_CROSSES(geom1, geom2)`
Test if geometries cross.

```python
ST_CROSSES($road, $river)
```

---

#### `ST_TOUCHES(geom1, geom2)`
Test if geometries share a boundary.

```python
ST_TOUCHES($parcel1, $parcel2)
```

---

### 5. Geometric Operations

#### `ST_BUFFER(geometry, distance, unit='m')`
Create buffer zone around geometry.

```python
ST_BUFFER('POINT(2.35 48.85)', 1000, 'm')
# → Circle with 1km radius

ST_BUFFER($point, 500, 'm')
# 500m zone around point
```

---

#### `ST_CENTROID(geometry)`
Return geometric center.

```python
ST_CENTROID('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))')
# → 'POINT (5 5)'
```

---

#### `ST_SIMPLIFY(geometry, tolerance)`
Simplify geometry (Douglas-Peucker algorithm).

```python
ST_SIMPLIFY($detailed_geometry, 0.001)
```

---

#### `ST_UNION(geom1, geom2)`
Merge two geometries.

```python
ST_UNION($zone1, $zone2)
```

---

#### `ST_INTERSECTION(geom1, geom2)`
Return intersection of two geometries.

```python
ST_INTERSECTION($zone1, $zone2)
```

---

### 6. Utilities

#### `ST_X(point)`, `ST_Y(point)`
Extract X/Y coordinates from point.

```python
ST_X('POINT(2.35 48.85)')  # → 2.35
ST_Y('POINT(2.35 48.85)')  # → 48.85

$longitude = ST_X($point)
$latitude = ST_Y($point)
```

---

#### `GEOMETRY_TYPE(geometry)`
Return geometry type.

```python
GEOMETRY_TYPE('POINT(2.35 48.85)')  # → 'Point'
GEOMETRY_TYPE('LINESTRING(0 0, 1 1)')  # → 'LineString'
```

---

#### `IS_VALID(geometry)`
Validate geometry topology.

```python
IS_VALID('POINT(2.35 48.85)')  # → True
IS_VALID('POLYGON((0 0, 1 1, 0 0))')  # → False (< 4 points)
```

---

## Complete Example: Lat/Lon Import

### Scenario
You have a table with separate `latitude` and `longitude` columns:

| id | name         | latitude | longitude |
|----|--------------|----------|-----------|
| 1  | Eiffel Tower | 48.8584  | 2.2945    |
| 2  | Sacré-Cœur   | 48.8867  | 2.3431    |

### Step 1: Create Geometry Column

Add column `geometry` with formula:
```python
MAKE_POINT($latitude, $longitude)
```

Result:
```
POINT (2.2945 48.8584)
POINT (2.3431 48.8867)
```

### Step 2: Export to GeoJSON

Add column `geojson` with formula:
```python
ST_AsGeoJSON($geometry)
```

Result:
```json
{"type":"Point","coordinates":[2.2945,48.8584]}
```

### Step 3: Calculate Distances

Add column `distance_to_eiffel` with formula:
```python
ST_DISTANCE(
  $geometry,
  MAKE_POINT(48.8584, 2.2945),
  'km'
)
```

### Step 4: Find Nearby Points

Filter formula:
```python
ST_DISTANCE($geometry, $reference_point, 'km') < 5
```

---

## Performance Considerations

### For Large Tables

1. **Pre-compute geometries**: Convert formula columns to data after initial calculation
2. **Use appropriate units**: Avoid unnecessary unit conversions
3. **Simplify geometries**: Use `ST_SIMPLIFY` for complex shapes

### Best Practices

1. **Store in WKT**: Use WKT (Well-Known Text) as the canonical format
2. **Convert on demand**: Generate GeoJSON only when exporting
3. **Validate inputs**: Use `IS_VALID` to check geometry topology
4. **Document CRS**: Include SRID in column names (e.g., `geom_wgs84`, `geom_l93`)

---

## Troubleshooting

### Empty Results

If spatial functions return empty strings:
1. Check geometry format with `GEOMETRY_TYPE($geom)`
2. Validate with `IS_VALID($geom)`
3. Verify CRS compatibility

### Performance Issues

For slow calculations on large datasets:
1. Pre-compute static geometries
2. Use spatial indexing (convert to data)
3. Reduce geometry complexity with `ST_SIMPLIFY`

---

## Reference

### External Resources

- **Shapely Documentation**: https://shapely.readthedocs.io
- **PyProj Documentation**: https://pyproj4.github.io/pyproj
- **PostGIS Reference**: https://postgis.net/docs/reference.html
- **EPSG Registry**: https://epsg.io

### Function Compatibility

These functions follow PostGIS/SpatiaLite naming conventions for compatibility with standard GIS workflows.

---

## Implementation Notes

### Why Not Load mod_spatialite in Node?

The `mod_spatialite.so` extension cannot be loaded in node-sqlite3 because:
1. It links against system `libsqlite3.so`
2. node-sqlite3 uses statically-compiled SQLite
3. Symbol conflicts occur between the two SQLite versions

Solution: All spatial operations run in the Python sandbox via Shapely/PyProj, with SpatiaLite CLI as fallback for complex operations.

### Security

All spatial functions execute in the sandboxed Python environment, preventing:
- Filesystem access
- Network access
- Arbitrary code execution

---

**Version**: Phase 2 Complete - 30+ geospatial functions
**Last Updated**: 2025-11-22
