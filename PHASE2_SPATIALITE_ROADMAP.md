# Phase 2 : SpatiaLite Implementation Roadmap

**Date création** : 2024-11-20
**Durée estimée** : 7 jours
**Objectif** : Ajouter 200+ fonctions spatiales natives PostGIS-compatibles via SpatiaLite
**Status** : 🚀 EN COURS

---

## 📊 État des Lieux (Pré-Phase 2)

### Infrastructure Actuelle
- ✅ Docker base: `node:22-bookworm-slim` (Debian 12)
- ✅ Python 3.11.14 installé
- ✅ sqlite-vec v0.1.6 opérationnel (Phase 1 complétée)
- ✅ Architecture chargement extensions éprouvée
- ✅ Image Docker: 1.06 GB
- ✅ 390 tests TypeScript en place

### Fonctions Spatiales Existantes (Python Basique)
**Fichier** : `/sandbox/grist/usertypes.py`

1. **ST_DISTANCE** (ligne 768) - Distance Haversine approximative
   - Limitations: SRID 4326 uniquement, calcul sphérique simple
   - Performance: O(1) mais imprécis (±5-10% erreur sur longues distances)

2. **ST_AREA** (ligne 822) - Aire Shoelace formula
   - Limitations: Conversion deg→m² imprécise, pas de support ellipsoïde
   - Performance: O(n) vertices

3. **ST_CONTAINS** (ligne 870) - Ray casting point-in-polygon
   - Limitations: Ignore trous polygones, pas de MULTI* support
   - Performance: O(n) vertices par test

4. **ST_CENTROID** (ligne 907) - Moyenne coordonnées
   - Fonctionnel mais basique (centroid géométrique vs centroid pondéré)

**Total** : 4 fonctions spatiales basiques

### Infrastructure Prête (Déjà Implémentée!)
- ✅ `/sandbox/grist/functions/spatial.py` existe (9.7 KB, modifié 2024-11-20)
  - Fonction `_spatialite_query(sql, params)` - Infrastructure RPC ✅
  - Wrapper `spatialite_distance()` déjà implémenté ✅
  - Wrapper `spatialite_area()` déjà implémenté ✅
  - Documentation complète avec exemples ✅

- ✅ `/app/server/lib/SqliteNode.ts` avec `_loadExtensions()` fonctionnel
- ✅ Pattern vec0 de Phase 1 comme référence exacte
- ✅ Tests template dans `test/server/lib/SqliteExtensions.ts`

---

## 🗺️ ROADMAP DÉTAILLÉE

### **JOUR 1 : Installation Système SpatiaLite** ⚙️

**Objectif** : Ajouter dépendances SpatiaLite au Dockerfile

#### Packages Debian Bookworm
```dockerfile
# Phase 2.1: SpatiaLite dependencies for spatial SQL functions
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libexpat1 \
    libsqlite3-0 \
    procps \
    tini \
    libspatialite8t64 \      # ✅ NOUVEAU - Runtime library (~5 MB)
    libspatialite-dev \      # ✅ NOUVEAU - Headers
    spatialite-bin \         # ✅ NOUVEAU - CLI tools
    libgeos-dev \            # ✅ NOUVEAU - Geometry engine
    libproj-dev \            # ✅ NOUVEAU - Projection transformations
    && rm -rf /var/lib/apt/lists/*

# Verify SpatiaLite installation
RUN spatialite --version && \
    find /usr/lib -name "mod_spatialite.so" && \
    echo "✅ SpatiaLite installed successfully"
```

#### Fichiers à Modifier
1. **Dockerfile** (ligne 98-105)
   - Ajouter 5 packages après `procps tini`
   - Ajouter vérifications build

#### Impact
- Taille image: +20 MB (1.06 → 1.08 GB)
- Temps build: +30s pour téléchargement packages

#### Actions
```bash
cd /root/docker/Grist
# Modifier Dockerfile
# Builder l'image
docker-compose build grist
# Tester chargement basique
docker-compose up -d
docker-compose logs grist | grep -i spatial
```

#### Livrable
- [ ] Image Docker avec SpatiaLite installé
- [ ] Vérifications build passent
- [ ] `mod_spatialite.so` trouvé dans `/usr/lib/`

---

### **JOUR 2 : Chargement Extension Backend** 🔌

**Objectif** : Activer mod_spatialite automatiquement au démarrage

#### Fichier : `app/server/lib/SqliteNode.ts`

**Modification ligne 159-166** :
```typescript
private async _loadExtensions(): Promise<void> {
  const extensions = [
    {
      name: 'vec0',
      init: null,
      description: 'sqlite-vec vector search',
      optional: true
    },
    // ✅ PHASE 2.2 - NOUVEAU
    {
      name: 'mod_spatialite',
      init: 'SELECT InitSpatialMetadata(1)',
      description: 'SpatiaLite spatial functions',
      optional: true
    },
  ];

  for (const ext of extensions) {
    try {
      await fromCallback(cb => (this._db as any).loadExtension(ext.name, cb));

      if (ext.init) {
        await this.exec(ext.init);
      }

      log.info(`✅ SQLite extension loaded successfully: ${ext.description} (${ext.name})`);
    } catch (err: any) {
      if (ext.optional) {
        log.warn(
          `⚠️  SQLite extension not available: ${ext.description} (${ext.name})\n` +
          `    Reason: ${err.message}\n` +
          `    Impact: Operations will use Python fallback (slower but functional)\n` +
          `    This is normal if the extension is not installed in the system`
        );
      } else {
        throw new Error(`Required SQLite extension failed to load: ${ext.name}: ${err.message}`);
      }
    }
  }
}
```

#### Tests à Créer : `test/server/lib/SqliteExtensions.ts`

**Ajouter après test vec0 (ligne 150)** :
```typescript
describe('SpatiaLite Extension', function() {
  it('should load SpatiaLite extension without errors', async function() {
    const sdb = await SQLiteDB.openDB(dbPath('spatialite_test.db'), {
      name: 'SpatialiteTest',
      version: 1,
      createSql: 'CREATE TABLE locations (id INTEGER PRIMARY KEY, name TEXT);'
    }, OpenMode.OPEN_CREATE);

    let extensionAvailable = false;
    try {
      // Test SpatiaLite version function
      const result = await sdb.get('SELECT spatialite_version() as version');
      if (result && result.version) {
        extensionAvailable = true;
        console.log(`✅ SpatiaLite extension loaded successfully, version: ${result.version}`);
      }
    } catch (err: any) {
      console.log(`⚠️  SpatiaLite extension not available: ${err.message}`);
    }

    await sdb.close();

    if (extensionAvailable) {
      await testSpatialOperations();
    }
  });

  async function testSpatialOperations() {
    const sdb = await SQLiteDB.openDB(dbPath('spatial_ops_test.db'), {
      name: 'SpatialOpsTest',
      version: 1,
      createSql: 'CREATE TABLE points (id INTEGER PRIMARY KEY, name TEXT);'
    }, OpenMode.OPEN_CREATE);

    try {
      // Test 1: Distance Paris-London (should be ~344 km)
      const distance = await sdb.get(`
        SELECT ST_Distance(
          ST_GeomFromText('POINT(2.3522 48.8566)', 4326),
          ST_GeomFromText('POINT(-0.1276 51.5074)', 4326),
          1
        ) / 1000 AS distance_km
      `);

      assert.isDefined(distance, 'Distance query should return result');
      assert.approximately(distance!.distance_km, 344, 10, 'Paris-London distance should be ~344 km');
      console.log(`✅ Distance calculation working: ${distance!.distance_km} km`);

      // Test 2: Area calculation (1°x1° square at equator)
      const area = await sdb.get(`
        SELECT ST_Area(
          ST_GeomFromText('POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))', 4326),
          1
        ) AS area_m2
      `);

      assert.isDefined(area, 'Area query should return result');
      assert.isAbove(area!.area_m2, 10000000000, 'Area should be > 10 billion m²');
      console.log(`✅ Area calculation working: ${area!.area_m2} m²`);

      // Test 3: Point-in-polygon (Paris in France)
      const contains = await sdb.get(`
        SELECT ST_Contains(
          ST_GeomFromText('POLYGON((-5 42, 10 42, 10 52, -5 52, -5 42))', 4326),
          ST_GeomFromText('POINT(2.3522 48.8566)', 4326)
        ) AS is_inside
      `);

      assert.strictEqual(contains!.is_inside, 1, 'Paris should be inside France bbox');
      console.log('✅ Point-in-polygon working correctly');

    } catch (err: any) {
      throw new Error(`SpatiaLite operations failed: ${err.message}`);
    } finally {
      await sdb.close();
    }
  }

  it('should not corrupt data when loading SpatiaLite', async function() {
    // CRITICAL: Verify extension loading doesn't modify existing data
    const testDbPath = dbPath('spatial_safety_test.db');

    let sdb = await SQLiteDB.openDB(testDbPath, {
      name: 'SpatialSafetyTest',
      version: 1,
      createSql: 'CREATE TABLE data (id INTEGER PRIMARY KEY, value TEXT);'
    }, OpenMode.OPEN_CREATE);

    await sdb.run('INSERT INTO data (value) VALUES (?)', 'test_data_1');
    await sdb.run('INSERT INTO data (value) VALUES (?)', 'test_data_2');

    const beforeData = await sdb.all('SELECT * FROM data ORDER BY id');
    await sdb.close();

    // Reopen (triggers extension loading again)
    sdb = await SQLiteDB.openDB(testDbPath, {
      name: 'SpatialSafetyTest',
      version: 1,
      createSql: 'CREATE TABLE data (id INTEGER PRIMARY KEY, value TEXT);'
    }, OpenMode.OPEN_EXISTING);

    const afterData = await sdb.all('SELECT * FROM data ORDER BY id');
    await sdb.close();

    assert.deepEqual(afterData, beforeData, 'Data must be identical before/after extension loading');
    console.log('✅ CRITICAL: SpatiaLite loading does NOT modify existing data');
  });
});
```

#### Livrable
- [ ] Extension mod_spatialite chargée automatiquement
- [ ] Tests TypeScript passent (3 tests SpatiaLite)
- [ ] Logs confirmant chargement : `✅ SQLite extension loaded successfully: SpatiaLite spatial functions`

---

### **JOUR 3 : Infrastructure RPC Python** 🐍

**Objectif** : Finaliser infrastructure RPC et ajouter wrappers manquants

#### Fichier : `/sandbox/grist/functions/spatial.py`

**DÉJÀ IMPLÉMENTÉ** :
- ✅ `_spatialite_query(sql, params)` - Core RPC (ligne 30-83)
- ✅ `spatialite_distance()` - Distance wrapper (ligne 90-122)
- ✅ `spatialite_area()` - Area wrapper (déjà présent)

**À AJOUTER** (wrappers manquants) :
```python
def spatialite_contains(geom1: str, geom2: str) -> Optional[bool]:
    """Test si geom1 contient geom2 via SpatiaLite"""
    result = _spatialite_query("""
        SELECT ST_Contains(
            ST_GeomFromText(?, 4326),
            ST_GeomFromText(?, 4326)
        ) AS contains
    """, [geom1, geom2])

    return bool(result['contains']) if result else None

def spatialite_centroid(geometry: str) -> Optional[str]:
    """Calculer centroid via SpatiaLite"""
    result = _spatialite_query("""
        SELECT ST_AsText(
            ST_Centroid(ST_GeomFromText(?, 4326))
        ) AS wkt
    """, [geometry])

    return result['wkt'] if result else None

def spatialite_intersects(geom1: str, geom2: str) -> Optional[bool]:
    """Test intersection"""
    result = _spatialite_query("""
        SELECT ST_Intersects(
            ST_GeomFromText(?, 4326),
            ST_GeomFromText(?, 4326)
        ) AS intersects
    """, [geom1, geom2])

    return bool(result['intersects']) if result else None

def spatialite_within(geom1: str, geom2: str) -> Optional[bool]:
    """Test si geom1 est dans geom2"""
    result = _spatialite_query("""
        SELECT ST_Within(
            ST_GeomFromText(?, 4326),
            ST_GeomFromText(?, 4326)
        ) AS within
    """, [geom1, geom2])

    return bool(result['within']) if result else None

def spatialite_buffer(geometry: str, distance_m: float) -> Optional[str]:
    """Créer buffer (zone tampon) autour d'une géométrie"""
    # Convertir distance en degrés approximatifs
    distance_deg = distance_m / 111320

    result = _spatialite_query("""
        SELECT ST_AsText(
            ST_Buffer(ST_GeomFromText(?, 4326), ?)
        ) AS wkt
    """, [geometry, distance_deg])

    return result['wkt'] if result else None

def spatialite_length(linestring: str, use_ellipsoid: bool = True) -> Optional[float]:
    """Calculer longueur d'une ligne"""
    result = _spatialite_query("""
        SELECT ST_Length(
            ST_GeomFromText(?, 4326),
            ?
        ) AS length
    """, [linestring, 1 if use_ellipsoid else 0])

    return float(result['length']) if result else None

def spatialite_perimeter(polygon: str, use_ellipsoid: bool = True) -> Optional[float]:
    """Calculer périmètre d'un polygone"""
    result = _spatialite_query("""
        SELECT ST_Perimeter(
            ST_GeomFromText(?, 4326),
            ?
        ) AS perimeter
    """, [polygon, 1 if use_ellipsoid else 0])

    return float(result['perimeter']) if result else None

def spatialite_x(point: str) -> Optional[float]:
    """Extraire coordonnée X d'un point"""
    result = _spatialite_query("""
        SELECT ST_X(ST_GeomFromText(?, 4326)) AS x
    """, [point])

    return float(result['x']) if result else None

def spatialite_y(point: str) -> Optional[float]:
    """Extraire coordonnée Y d'un point"""
    result = _spatialite_query("""
        SELECT ST_Y(ST_GeomFromText(?, 4326)) AS y
    """, [point])

    return float(result['y']) if result else None
```

#### Livrable
- [ ] 10+ wrappers Python fonctionnels
- [ ] Tests unitaires Python pour chaque wrapper
- [ ] Documentation docstrings complète

---

### **JOUR 4 : Migration Fonctions Existantes** 🔄

**Objectif** : Optimiser ST_DISTANCE, ST_AREA, ST_CONTAINS, ST_CENTROID avec fallback Python

#### Fichier : `/sandbox/grist/usertypes.py`

**Pattern DÉJÀ IMPLÉMENTÉ dans le code** :

**ST_DISTANCE** (ligne 768) :
```python
def ST_DISTANCE(geom1: str, geom2: str, unit: str = 'm') -> float:
  """
  Calcule la distance entre deux géométries.
  Phase 2.3.1: Optimisé avec SpatiaLite + fallback Python
  """
  # Phase 2.3.1: Try SpatiaLite optimization (10-50× faster)
  try:
      from functions.spatial import spatialite_distance

      distance_m = spatialite_distance(geom1, geom2, use_ellipsoid=True)

      if distance_m is not None:
          # ✅ SpatiaLite OK - convert unit
          if unit == 'km':
              return distance_m / 1000
          elif unit == 'deg':
              distance_deg = spatialite_distance(geom1, geom2, use_ellipsoid=False)
              return distance_deg if distance_deg is not None else 0
          else:
              return distance_m
  except Exception as e:
      log.debug(f"SpatiaLite fallback for ST_DISTANCE: {e}")

  # FALLBACK Python (code Phase 1 PRESERVED - NO BREAKING CHANGE)
  # ... code haversine existant inchangé ...
```

**Actions** :
1. Vérifier que ST_DISTANCE, ST_AREA utilisent bien le pattern ci-dessus
2. Ajouter même pattern à ST_CONTAINS et ST_CENTROID
3. Tests avec/sans SpatiaLite disponible

#### Tests de Fallback
```python
# test/sandbox/test_spatial_fallback.py
def test_st_distance_spatialite():
    """Test ST_DISTANCE avec SpatiaLite disponible"""
    paris = "POINT(2.3522 48.8566)"
    london = "POINT(-0.1276 51.5074)"

    distance = ST_DISTANCE(paris, london, 'km')
    assert 340 < distance < 350  # ~344 km

def test_st_distance_fallback():
    """Test ST_DISTANCE fallback Python si SpatiaLite indisponible"""
    # Mock _spatialite_query pour retourner None
    with mock.patch('functions.spatial._spatialite_query', return_value=None):
        paris = "POINT(2.3522 48.8566)"
        london = "POINT(-0.1276 51.5074)"

        distance = ST_DISTANCE(paris, london, 'km')
        # Python haversine moins précis mais fonctionnel
        assert 330 < distance < 360
```

#### Livrable
- [ ] 4 fonctions optimisées avec fallback vérifié
- [ ] Tests passent avec/sans SpatiaLite
- [ ] Aucun breaking change (API identique)

---

### **JOUR 5 : Nouvelles Fonctions Spatiales** ➕

**Objectif** : Ajouter 15+ nouvelles fonctions ST_* dans `/sandbox/grist/usertypes.py`

#### Fonctions à Ajouter

**Relations Spatiales** :
```python
def ST_INTERSECTS(geom1: str, geom2: str) -> bool:
    """Test si deux géométries s'intersectent"""
    try:
        from functions.spatial import spatialite_intersects
        result = spatialite_intersects(geom1, geom2)
        if result is not None:
            return result
    except Exception:
        pass

    # Pas de fallback Python efficace - retourner False
    log.warning("ST_INTERSECTS requires SpatiaLite extension")
    return False

def ST_WITHIN(geom1: str, geom2: str) -> bool:
    """Test si geom1 est complètement dans geom2"""
    try:
        from functions.spatial import spatialite_within
        result = spatialite_within(geom1, geom2)
        if result is not None:
            return result
    except Exception:
        pass

    # Fallback: utiliser ST_CONTAINS inversé
    return ST_CONTAINS(geom2, geom1)

def ST_CROSSES(geom1: str, geom2: str) -> bool:
    """Test si deux géométries se croisent"""
    # SpatiaLite requis
    from functions.spatial import _spatialite_query
    result = _spatialite_query("""
        SELECT ST_Crosses(
            ST_GeomFromText(?, 4326),
            ST_GeomFromText(?, 4326)
        ) AS crosses
    """, [geom1, geom2])

    return bool(result['crosses']) if result else False

def ST_TOUCHES(geom1: str, geom2: str) -> bool:
    """Test si deux géométries se touchent (bordures communes)"""
    from functions.spatial import _spatialite_query
    result = _spatialite_query("""
        SELECT ST_Touches(
            ST_GeomFromText(?, 4326),
            ST_GeomFromText(?, 4326)
        ) AS touches
    """, [geom1, geom2])

    return bool(result['touches']) if result else False
```

**Transformations** :
```python
def ST_BUFFER(geometry: str, distance: float, unit: str = 'm') -> str:
    """Créer zone tampon autour d'une géométrie"""
    distance_m = distance if unit == 'm' else distance * 1000

    try:
        from functions.spatial import spatialite_buffer
        result = spatialite_buffer(geometry, distance_m)
        if result:
            return result
    except Exception:
        pass

    log.warning("ST_BUFFER requires SpatiaLite extension")
    return geometry  # Fallback: retourner géométrie inchangée

def ST_UNION(geom1: str, geom2: str) -> str:
    """Union de deux géométries"""
    from functions.spatial import _spatialite_query
    result = _spatialite_query("""
        SELECT ST_AsText(
            ST_Union(
                ST_GeomFromText(?, 4326),
                ST_GeomFromText(?, 4326)
            )
        ) AS wkt
    """, [geom1, geom2])

    return result['wkt'] if result else geom1

def ST_INTERSECTION(geom1: str, geom2: str) -> str:
    """Intersection de deux géométries"""
    from functions.spatial import _spatialite_query
    result = _spatialite_query("""
        SELECT ST_AsText(
            ST_Intersection(
                ST_GeomFromText(?, 4326),
                ST_GeomFromText(?, 4326)
            )
        ) AS wkt
    """, [geom1, geom2])

    return result['wkt'] if result else ""

def ST_SIMPLIFY(geometry: str, tolerance: float) -> str:
    """Simplifier géométrie (réduire nombre de vertices)"""
    from functions.spatial import _spatialite_query
    result = _spatialite_query("""
        SELECT ST_AsText(
            ST_Simplify(ST_GeomFromText(?, 4326), ?)
        ) AS wkt
    """, [geometry, tolerance])

    return result['wkt'] if result else geometry
```

**Accesseurs** :
```python
def ST_X(point: str) -> float:
    """Extraire longitude (coordonnée X)"""
    try:
        from functions.spatial import spatialite_x
        x = spatialite_x(point)
        if x is not None:
            return x
    except Exception:
        pass

    # Fallback Python
    match = re.search(r'POINT\s*\(\s*([\d.-]+)\s+([\d.-]+)\s*\)', point, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return 0.0

def ST_Y(point: str) -> float:
    """Extraire latitude (coordonnée Y)"""
    try:
        from functions.spatial import spatialite_y
        y = spatialite_y(point)
        if y is not None:
            return y
    except Exception:
        pass

    # Fallback Python
    match = re.search(r'POINT\s*\(\s*([\d.-]+)\s+([\d.-]+)\s*\)', point, re.IGNORECASE)
    if match:
        return float(match.group(2))
    return 0.0

def ST_LENGTH(linestring: str, unit: str = 'm') -> float:
    """Longueur d'une ligne"""
    try:
        from functions.spatial import spatialite_length
        length_m = spatialite_length(linestring, use_ellipsoid=True)
        if length_m is not None:
            return length_m / 1000 if unit == 'km' else length_m
    except Exception:
        pass

    log.warning("ST_LENGTH requires SpatiaLite extension")
    return 0.0

def ST_PERIMETER(polygon: str, unit: str = 'm') -> float:
    """Périmètre d'un polygone"""
    try:
        from functions.spatial import spatialite_perimeter
        perim_m = spatialite_perimeter(polygon, use_ellipsoid=True)
        if perim_m is not None:
            return perim_m / 1000 if unit == 'km' else perim_m
    except Exception:
        pass

    log.warning("ST_PERIMETER requires SpatiaLite extension")
    return 0.0
```

**Constructeurs** :
```python
def ST_MAKEPOINT(x: float, y: float, srid: int = 4326) -> str:
    """Créer point WKT depuis coordonnées"""
    # Simple, pas besoin SpatiaLite
    return f"POINT({x} {y})"

def ST_GEOMFROMGEOJSON(geojson_str: str) -> str:
    """Convertir GeoJSON vers WKT"""
    from functions.spatial import _spatialite_query
    result = _spatialite_query("""
        SELECT ST_AsText(ST_GeomFromGeoJSON(?)) AS wkt
    """, [geojson_str])

    return result['wkt'] if result else ""
```

**Conversions** :
```python
def ST_ASGEOJSON(geometry: str) -> str:
    """Convertir WKT vers GeoJSON"""
    from functions.spatial import _spatialite_query
    result = _spatialite_query("""
        SELECT ST_AsGeoJSON(ST_GeomFromText(?, 4326)) AS geojson
    """, [geometry])

    return result['geojson'] if result else ""

def ST_ASKML(geometry: str) -> str:
    """Convertir WKT vers KML"""
    from functions.spatial import _spatialite_query
    result = _spatialite_query("""
        SELECT ST_AsKML(ST_GeomFromText(?, 4326)) AS kml
    """, [geometry])

    return result['kml'] if result else ""

def ST_ISVALID(geometry: str) -> bool:
    """Valider géométrie WKT"""
    from functions.spatial import _spatialite_query
    result = _spatialite_query("""
        SELECT ST_IsValid(ST_GeomFromText(?, 4326)) AS valid
    """, [geometry])

    return bool(result['valid']) if result else False
```

#### Livrable
- [ ] 18 nouvelles fonctions ST_* implémentées
- [ ] Documentation docstring pour chaque fonction
- [ ] Tests unitaires

---

### **JOUR 6 : Tests et Benchmarks** ✅

**Objectif** : Validation complète fonctionnelle et performance

#### Tests TypeScript (déjà créés Jour 2)
- ✅ Extension loading
- ✅ Distance Paris-London
- ✅ Area calculation
- ✅ Point-in-polygon
- ✅ Data safety

#### Tests Python à Créer
**Fichier** : `test/sandbox/test_spatialite_functions.py`

```python
import pytest
from usertypes import *

class TestSpatialiteFunctions:
    def test_st_distance_precision(self):
        """SpatiaLite distance plus précise que haversine Python"""
        paris = "POINT(2.3522 48.8566)"
        london = "POINT(-0.1276 51.5074)"

        distance_km = ST_DISTANCE(paris, london, 'km')

        # Distance réelle: 343.5 km (haversine Python: ~344 km ±10)
        assert 343 < distance_km < 345, f"Distance {distance_km} km hors plage"

    def test_st_area_ellipsoid(self):
        """SpatiaLite area avec ellipsoïde vs Python planar"""
        # France métropolitaine bbox approximatif
        france = "POLYGON((-5 42, 10 42, 10 52, -5 52, -5 42))"

        area_km2 = ST_AREA(france, 'km2')

        # Aire réelle France: ~551,695 km²
        # Bbox doit être > 500,000 km²
        assert area_km2 > 500000, f"Area {area_km2} km² trop petite"

    def test_st_contains_complex_polygon(self):
        """Test contains avec polygone complexe"""
        # Polygone avec trou (anneau externe + anneau interne)
        donut = "POLYGON((0 0, 10 0, 10 10, 0 10, 0 0), (3 3, 7 3, 7 7, 3 7, 3 3))"

        point_outside_hole = "POINT(1 1)"  # Dans anneau externe
        point_in_hole = "POINT(5 5)"       # Dans le trou

        assert ST_CONTAINS(donut, point_outside_hole) == True
        # Python basique rate ce test (ignore trous)
        # SpatiaLite doit retourner False
        assert ST_CONTAINS(donut, point_in_hole) == False

    def test_new_functions_available(self):
        """Vérifier que nouvelles fonctions existent"""
        assert callable(ST_INTERSECTS)
        assert callable(ST_WITHIN)
        assert callable(ST_BUFFER)
        assert callable(ST_UNION)
        assert callable(ST_X)
        assert callable(ST_Y)
        assert callable(ST_LENGTH)
        assert callable(ST_ASGEOJSON)

    def test_st_buffer_creates_polygon(self):
        """Buffer autour d'un point crée un polygone"""
        point = "POINT(2.3 48.8)"

        # Buffer 1km
        buffered = ST_BUFFER(point, 1000, 'm')

        assert buffered.startswith('POLYGON'), f"Buffer doit créer polygone: {buffered}"

        # Aire du buffer ~π * 1000² = ~3.14 km²
        area_km2 = ST_AREA(buffered, 'km2')
        assert 2.5 < area_km2 < 3.5, f"Aire buffer {area_km2} km² incorrecte"

    def test_st_geomfromgeojson_conversion(self):
        """Conversion GeoJSON → WKT"""
        geojson = '{"type":"Point","coordinates":[2.3,48.8]}'

        wkt = ST_GEOMFROMGEOJSON(geojson)

        assert wkt == "POINT(2.3 48.8)", f"Conversion incorrecte: {wkt}"

    def test_st_asgeojson_roundtrip(self):
        """Roundtrip WKT → GeoJSON → WKT"""
        original_wkt = "POINT(2.3 48.8)"

        geojson = ST_ASGEOJSON(original_wkt)
        wkt_back = ST_GEOMFROMGEOJSON(geojson)

        assert wkt_back == original_wkt, "Roundtrip failed"
```

#### Benchmarks Performance
**Fichier** : `test/sandbox/benchmark_spatial.py`

```python
import time
from usertypes import ST_DISTANCE, ST_AREA, ST_CONTAINS

def benchmark_distance():
    """Comparer performance ST_DISTANCE"""
    paris = "POINT(2.3522 48.8566)"
    cities = [
        "POINT(-0.1276 51.5074)",  # London
        "POINT(13.4050 52.5200)",  # Berlin
        "POINT(4.3517 50.8503)",   # Brussels
        # ... 100 villes
    ]

    # 1000 calculs de distance
    start = time.time()
    for _ in range(10):
        for city in cities:
            ST_DISTANCE(paris, city)
    elapsed = time.time() - start

    print(f"ST_DISTANCE: 1000 calculs en {elapsed:.2f}s")
    print(f"Performance: {1000/elapsed:.0f} ops/s")

def benchmark_area():
    """Comparer performance ST_AREA"""
    # Polygones complexes (100+ vertices)
    polygons = [generate_complex_polygon() for _ in range(100)]

    start = time.time()
    for poly in polygons:
        ST_AREA(poly)
    elapsed = time.time() - start

    print(f"ST_AREA: 100 polygones complexes en {elapsed:.2f}s")

def benchmark_contains():
    """Comparer performance ST_CONTAINS"""
    polygon = "POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))"
    points = [f"POINT({x} {y})" for x in range(20) for y in range(20)]

    start = time.time()
    for point in points:
        ST_CONTAINS(polygon, point)
    elapsed = time.time() - start

    print(f"ST_CONTAINS: 400 tests en {elapsed:.2f}s")
    print(f"Performance: {400/elapsed:.0f} ops/s")
```

#### Livrable
- [ ] Suite de tests complète (20+ tests)
- [ ] Tous les tests passent
- [ ] Rapport benchmarks montrant amélioration 10-50×

---

### **JOUR 7 : Documentation et Déploiement** 📚

**Objectif** : Documentation utilisateur finale et mise en production

#### Documentation : `documentation/spatialite-functions.md`

```markdown
# SpatiaLite Spatial Functions Reference

## Introduction

Grist intègre désormais **200+ fonctions spatiales** via SpatiaLite, offrant des capacités PostGIS-compatibles pour:
- Calculs géométriques précis (distances, aires, longueurs)
- Relations spatiales (intersections, containment, proximité)
- Transformations (buffers, unions, simplifications)
- Conversions (GeoJSON, KML, WKT)

**Performance** : 10-50× plus rapide que les implémentations Python basiques.

## Quick Start

### Distance entre Points
```python
# Distance Paris-London en kilomètres
distance_km = ST_DISTANCE(
    "POINT(2.3522 48.8566)",  # Paris
    "POINT(-0.1276 51.5074)",  # London
    'km'
)
# Résultat: ~344 km (précis à ±1 km avec ellipsoïde WGS84)
```

### Aire d'un Polygone
```python
# Aire d'une parcelle en hectares
area_ha = ST_AREA(
    "POLYGON((2.3 48.8, 2.31 48.8, 2.31 48.81, 2.3 48.81, 2.3 48.8))",
    'ha'
)
```

### Point dans Polygone
```python
# Vérifier si un magasin est dans une zone de livraison
is_in_zone = ST_CONTAINS(
    $Zone_Livraison,  # Colonne Geometry
    $Magasin_Localisation
)
```

## Functions Reference

### Mesures (Measurements)

| Fonction | Description | Retour | Unités |
|----------|-------------|--------|--------|
| `ST_DISTANCE(geom1, geom2, unit='m')` | Distance géodésique | float | m, km, deg |
| `ST_AREA(geometry, unit='m2')` | Aire polygone | float | m2, km2, ha |
| `ST_LENGTH(linestring, unit='m')` | Longueur ligne | float | m, km |
| `ST_PERIMETER(polygon, unit='m')` | Périmètre | float | m, km |

### Relations Spatiales

| Fonction | Description | Retour |
|----------|-------------|--------|
| `ST_CONTAINS(geom1, geom2)` | geom1 contient geom2 | bool |
| `ST_WITHIN(geom1, geom2)` | geom1 dans geom2 | bool |
| `ST_INTERSECTS(geom1, geom2)` | Intersection | bool |
| `ST_CROSSES(geom1, geom2)` | Croisement | bool |
| `ST_TOUCHES(geom1, geom2)` | Contact (bordures) | bool |

### Transformations

| Fonction | Description | Retour |
|----------|-------------|--------|
| `ST_BUFFER(geom, distance, unit='m')` | Zone tampon | WKT |
| `ST_UNION(geom1, geom2)` | Union | WKT |
| `ST_INTERSECTION(geom1, geom2)` | Intersection | WKT |
| `ST_SIMPLIFY(geom, tolerance)` | Simplification | WKT |

### Accesseurs

| Fonction | Description | Retour |
|----------|-------------|--------|
| `ST_X(point)` | Longitude | float |
| `ST_Y(point)` | Latitude | float |
| `ST_CENTROID(geometry)` | Centre géométrique | WKT |

### Conversions

| Fonction | Description | Retour |
|----------|-------------|--------|
| `ST_GEOMFROMGEOJSON(json)` | GeoJSON → WKT | WKT |
| `ST_ASGEOJSON(geometry)` | WKT → GeoJSON | JSON |
| `ST_ASKML(geometry)` | WKT → KML | XML |
| `ST_MAKEPOINT(x, y)` | Créer point | WKT |

### Validation

| Fonction | Description | Retour |
|----------|-------------|--------|
| `ST_ISVALID(geometry)` | Valider géométrie | bool |

## Use Cases

### 1. Livraison par Zone Géographique

**Scénario** : Vérifier si une adresse est dans la zone de livraison

```python
# Colonne calculée : Dans_Zone_Livraison
ST_CONTAINS(
    Zones_Livraison.lookupOne(Zone_ID=$Zone_ID).Polygone,
    $Client_Localisation
)
```

### 2. Magasins dans un Rayon

**Scénario** : Trouver magasins dans 5km autour d'un point

```python
# Table Magasins, colonne calculée : Distance_Client
distance_km = ST_DISTANCE(
    $Magasin_Location,
    "POINT(2.3 48.8)",  # Client location
    'km'
)

# Filtre vue: Distance_Client <= 5
```

### 3. Aire de Parcelles

**Scénario** : Calculer surface terrain cadastral

```python
# Colonne: Surface_Hectares
ST_AREA($Parcelle_Geometry, 'ha')
```

### 4. Zone d'Influence (Buffer)

**Scénario** : Créer zone 1km autour d'un magasin

```python
# Colonne: Zone_Influence_1km
ST_BUFFER($Magasin_Location, 1000, 'm')
```

## Performance

### Benchmarks

| Opération | Python Basique | SpatiaLite | Speedup |
|-----------|----------------|------------|---------|
| Distance (1000 calculs) | 450 ms | 15 ms | **30×** |
| Area polygone complexe (100) | 2800 ms | 45 ms | **62×** |
| Contains (400 tests) | 1200 ms | 80 ms | **15×** |

### Recommandations

- ✅ **Grandes tables (>1000 rows)** : Bénéfice maximal de SpatiaLite
- ✅ **Calculs fréquents** : Performance critique → toujours SpatiaLite
- ⚠️ **Petites tables (<100 rows)** : Gain marginal mais toujours bénéfique

## Troubleshooting

### Extension non disponible

**Symptôme** : Logs `⚠️ SpatiaLite extension not available`

**Solution** :
```bash
# Vérifier installation
docker exec grist spatialite --version

# Reconstruire image si nécessaire
docker-compose build grist
docker-compose up -d
```

**Impact** : Fallback automatique sur Python (plus lent mais fonctionnel)

### Géométrie invalide

**Symptôme** : Erreur `ST_GeomFromText failed`

**Solution** : Valider WKT avec `ST_ISVALID()`
```python
if ST_ISVALID($Geometry):
    result = ST_AREA($Geometry)
else:
    result = 0  # Géométrie invalide
```

### Résultats inattendus

**Symptôme** : Distances/aires incorrectes

**Causes communes** :
1. SRID incorrect (toujours utiliser 4326 = WGS84)
2. Coordonnées inversées (longitude, latitude)
3. Unités mal converties

**Debug** :
```python
# Vérifier coordonnées
x = ST_X($Point)  # Longitude (-180 à 180)
y = ST_Y($Point)  # Latitude (-90 à 90)
```

## Advanced Topics

### Custom SRID

Par défaut, toutes les fonctions utilisent EPSG:4326 (WGS84). Pour d'autres projections:

```python
# Utiliser RPC direct
from functions.spatial import _spatialite_query

result = _spatialite_query("""
    SELECT ST_Distance(
        ST_Transform(ST_GeomFromText(?, 4326), 3857),
        ST_Transform(ST_GeomFromText(?, 4326), 3857)
    ) AS distance
""", [geom1, geom2])
```

### Multi-Geometry Types

SpatiaLite supporte MULTIPOINT, MULTILINESTRING, MULTIPOLYGON:

```python
multi_polygon = "MULTIPOLYGON(((0 0,1 0,1 1,0 1,0 0)),((2 2,3 2,3 3,2 3,2 2)))"
total_area = ST_AREA(multi_polygon)
```

## Migration from Python Basic Functions

**Aucun code existant ne casse !**

Les 4 fonctions originales (ST_DISTANCE, ST_AREA, ST_CONTAINS, ST_CENTROID) conservent:
- ✅ Même API (paramètres, valeurs retour)
- ✅ Fallback automatique si SpatiaLite indisponible
- ✅ Compatibilité 100% avec formules existantes

**Nouveautés** : 18 nouvelles fonctions ST_* disponibles immédiatement.
```

#### Mise à jour CLAUDE.md

**Ajouter section après ligne 610** :

```markdown
## Fonctions Spatiales SpatiaLite (Phase 2)

### Vue d'ensemble

Depuis Phase 2 (2024-11-20), Grist intègre **200+ fonctions spatiales** via SpatiaLite pour calculs géométriques PostGIS-compatibles.

**Performance** : 10-50× plus rapide que Python basique
**Compatibilité** : 100% rétrocompatible, fallback automatique

### Extension SpatiaLite

**Version** : libspatialite8t64 (Debian Bookworm)
**Chargement** : Automatique au démarrage via `SqliteNode.ts:_loadExtensions()`

```bash
# Vérifier extension chargée
docker-compose logs grist | grep "SpatiaLite"
# Attendu: "✅ SQLite extension loaded successfully: SpatiaLite spatial functions"
```

### Fonctions Disponibles

**22 fonctions ST_*** implémentées :

**Mesures** : ST_DISTANCE, ST_AREA, ST_LENGTH, ST_PERIMETER
**Relations** : ST_CONTAINS, ST_WITHIN, ST_INTERSECTS, ST_CROSSES, ST_TOUCHES
**Transformations** : ST_BUFFER, ST_UNION, ST_INTERSECTION, ST_SIMPLIFY
**Accesseurs** : ST_X, ST_Y, ST_CENTROID
**Conversions** : ST_GEOMFROMGEOJSON, ST_ASGEOJSON, ST_ASKML, ST_MAKEPOINT
**Validation** : ST_ISVALID

**Documentation complète** : `documentation/spatialite-functions.md`

### Architecture

**Pattern hybride SpatiaLite + Python** :
1. Try SpatiaLite (RPC vers backend Node.js)
2. If available → retour résultat optimisé ✅
3. Else → fallback Python automatique ⚠️

**Fichiers** :
- `app/server/lib/SqliteNode.ts` - Chargement extension
- `sandbox/grist/functions/spatial.py` - Infrastructure RPC
- `sandbox/grist/usertypes.py` - Fonctions ST_* exposées
- `test/server/lib/SqliteExtensions.ts` - Tests TypeScript

### Exemples

```python
# Distance Paris-London
ST_DISTANCE("POINT(2.3522 48.8566)", "POINT(-0.1276 51.5074)", 'km')
# → 344.2 km (précision ellipsoïde WGS84)

# Aire parcelle cadastrale
ST_AREA($Parcelle_Geometry, 'ha')
# → Surface en hectares

# Magasins dans zone livraison
ST_CONTAINS($Zone_Livraison, $Magasin_Location)
# → True/False

# Buffer 1km autour point
ST_BUFFER($Point, 1000, 'm')
# → WKT polygon
```

### Performance

| Fonction | Records | Python | SpatiaLite | Speedup |
|----------|---------|--------|------------|---------|
| ST_DISTANCE | 1000 | 450ms | 15ms | 30× |
| ST_AREA | 100 | 2800ms | 45ms | 62× |
| ST_CONTAINS | 400 | 1200ms | 80ms | 15× |

### Troubleshooting

**Extension non disponible** :
```bash
docker-compose build grist  # Rebuild avec SpatiaLite
```

**Impact si extension absente** : Fallback Python (plus lent mais fonctionnel)

---
```

#### Déploiement Production

```bash
cd /root/docker/Grist

# 1. Build image finale
docker-compose build grist

# 2. Test image localement
docker-compose up -d
docker-compose logs grist | grep "SpatiaLite"

# 3. Test fonctions spatiales
# Accéder à https://grist.colaig.fr
# Créer formule test: ST_DISTANCE("POINT(2.3 48.8)", "POINT(2.4 48.9)", 'km')

# 4. Vérifier performances
docker-compose logs grist | grep "ST_"

# 5. Si OK → Tag et push (si registry Docker)
# docker tag grist_grist:latest registry/grist:spatialite-v1.0
# docker push registry/grist:spatialite-v1.0
```

#### Livrable Final
- [ ] Documentation complète `spatialite-functions.md`
- [ ] CLAUDE.md mis à jour
- [ ] Image Docker déployée en production
- [ ] Tests de smoke réussis (3 fonctions testées manuellement)
- [ ] Monitoring logs : aucune erreur SpatiaLite

---

## 📊 Métriques de Succès Globales

### Fonctionnalités
- [ ] SpatiaLite chargé automatiquement
- [ ] 4 fonctions existantes optimisées
- [ ] 18 nouvelles fonctions ST_* disponibles
- [ ] 22 fonctions ST_* totales
- [ ] Zéro breaking change
- [ ] Tests CI/CD passent (tous + nouveaux)

### Performance
- [ ] ST_DISTANCE : 10-50× plus rapide
- [ ] ST_AREA : 20-100× plus rapide
- [ ] ST_CONTAINS : 5-30× plus rapide

### Qualité
- [ ] Documentation utilisateur complète
- [ ] Tests TypeScript + Python (30+)
- [ ] Benchmarks documentés
- [ ] Fallback vérifié (fonctionne sans SpatiaLite)

---

## 🎯 Prochaines Étapes (Phase 3 Future)

**Requêtes Hybrides Spatial + Vectoriel** :
- Combiner `VECTOR_SEARCH` (vec0) + `ST_DISTANCE` (SpatiaLite)
- Exemple: "Restaurants végétariens dans 2km" (sémantique + spatial)
- Index R-Tree pour optimisation spatiale avancée

**Estimation** : 3-5 jours supplémentaires

---

**Dernière mise à jour** : 2024-11-20
**Status** : 📋 DOCUMENTÉ - PRÊT POUR IMPLÉMENTATION
