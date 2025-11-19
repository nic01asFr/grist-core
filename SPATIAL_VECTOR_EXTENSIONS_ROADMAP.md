# Roadmap Technique : Extensions Spatiales & Vectorielles pour Grist

**Date de création** : 2025-01-19
**Auteur** : Claude Code
**Objectif** : Documentation technique complète pour l'ajout de sqlite-vec et SpatiaLite à Grist

---

## 📋 Table des Matières

1. [Architecture Actuelle Grist](#architecture-actuelle-grist)
2. [État des Lieux : Fonctions Spatiales & Vectorielles](#état-des-lieux)
3. [Extensions Ciblées](#extensions-ciblées)
4. [Système de Chargement d'Extensions SQLite](#système-de-chargement-dextensions-sqlite)
5. [Feuille de Route en 3 Phases](#feuille-de-route-en-3-phases)
6. [Points Critiques & Risques](#points-critiques--risques)
7. [Tests & Validation](#tests--validation)

---

## 1. Architecture Actuelle Grist

### 1.1 Stack Technique

```
┌──────────────────────────────────────────────┐
│  LAYER 1: Frontend (TypeScript/React)       │
│  /app/client/                                │
│  - Widgets pour affichage colonnes          │
│  - UserType.ts : Définition types UI        │
└──────────────────────────────────────────────┘
                    ↕ HTTP API
┌──────────────────────────────────────────────┐
│  LAYER 2: Backend (TypeScript/Node.js)      │
│  /app/server/                                │
│  - FlexServer.ts : Routes HTTP              │
│  - DocManager : Gestion documents           │
│  - ActiveDoc : Document actif en mémoire    │
│  - SQLiteDB.ts : Wrapper SQLite             │
└──────────────────────────────────────────────┘
                    ↕ IPC
┌──────────────────────────────────────────────┐
│  LAYER 3: Data Engine (Python Sandbox)      │
│  /sandbox/grist/                             │
│  - usertypes.py : Types de colonnes         │
│  - functions/*.py : Fonctions formules      │
│  - embedding_manager.py : Gestion vecteurs  │
└──────────────────────────────────────────────┘
                    ↕ SQL
┌──────────────────────────────────────────────┐
│  LAYER 4: Storage (SQLite)                  │
│  /persist/docs/*.grist                       │
│  - 1 fichier SQLite par document            │
│  - Métadonnées : /persist/home.sqlite3      │
└──────────────────────────────────────────────┘
```

### 1.2 Bibliothèque SQLite Utilisée

**Package** : `@gristlabs/sqlite3` v5.1.4-grist.8
**Base** : Fork de `node-sqlite3`
**Modifications Grist** :
- Ajout `allMarshal()` pour sérialisation Grist custom
- Version personnalisée avec patches

**Localisation code** :
- Wrapper TypeScript : `/app/server/lib/SqliteNode.ts`
- Interface abstraite : `/app/server/lib/SqliteCommon.ts`
- Classe principale : `/app/server/lib/SQLiteDB.ts`

**Support extensions** :
```typescript
// @gristlabs/sqlite3 hérite de node-sqlite3
// Méthode disponible (non utilisée actuellement) :
database.loadExtension(path, callback)
```

### 1.3 Cycle de Vie d'un Document Grist

```typescript
// 1. Ouverture document
DocManager.fetchDoc(docName)
  → ActiveDoc.loadDoc(docPath)
    → SQLiteDB.openDB(path, schemaInfo)
      → sqlite3.Database(path, mode)

// 2. Migrations automatiques
SQLiteDB._migrate(currentVersion, targetVersion)
  → Execute migration functions sequentially
  → Update PRAGMA user_version

// 3. Sandbox Python
ActiveDoc._startPythonSandbox()
  → NSandbox.create()
    → Spawn Python process
    → Load grist modules (usertypes, functions, etc.)

// 4. Requêtes formules
User types formula → Python eval
  → Peut appeler fonctions SQL via DocStorage
    → SQLiteDB.exec(sql) / all(sql) / run(sql)
```

---

## 2. État des Lieux

### 2.1 Fonctions Spatiales Actuelles

**Implémentation** : Python natif dans `/sandbox/grist/usertypes.py`

| Fonction | Type | Implémentation | Limitations |
|----------|------|----------------|-------------|
| `ST_DISTANCE` | Mesure | Haversine Python | ❌ Approx., SRID 4326 uniqu. |
| `ST_AREA` | Mesure | Shoelace formula | ❌ Conversion deg→m² imprécise |
| `ST_CONTAINS` | Relation | Ray casting | ❌ Ignore trous polygones |
| `ST_CENTROID` | Accesseur | Moyenne coords | ✅ OK |

**Parseurs géométriques** :
- `_extract_point_coords()` : POINT uniquement
- `_extract_polygon_coords()` : POLYGON (anneau externe seul)
- ❌ Pas de parser pour LINESTRING, MULTI*, GEOMETRYCOLLECTION

**Stockage** : WKT en TEXT (colonne type `Geometry`)

### 2.2 Fonctions Vectorielles Actuelles

**Implémentation** : Hybride TypeScript + Python + API externe

| Fonction | Localisation | Backend | Performance |
|----------|--------------|---------|-------------|
| `CREATE_VECTOR` | usertypes.py | API Albert | ✅ Async, cache MD5 |
| `VECTOR_SEARCH` | usertypes.py | Python O(n) | ❌ Lent > 10K records |
| `VECTOR_SIMILARITY` | usertypes.py | NumPy/SciPy | ✅ Rapide |
| `AUTO_EMBEDDING` | embedding_manager.py | API Albert | ✅ Auto-détection colonnes |

**Stockage** : JSON array en TEXT
**API** : Albert (https://albert.api.etalab.gouv.fr/v1)
**Dimensions** : 1024 (embeddings-small)

**Recherche actuelle** :
```python
# Algorithme brute-force O(n)
for record in all_records:
    similarity = 1 - cosine(query_vector, record_vector)
    if similarity >= threshold:
        results.append(record.id)
```

---

## 3. Extensions Ciblées

### 3.1 sqlite-vec

**Source** : https://github.com/asg017/sqlite-vec
**Version** : v0.1.x (pre-v1, active développement)
**Auteur** : Alex Garcia (@asg017)
**Sponsors** : Mozilla Builders, Fly.io, Turso

**Caractéristiques** :
- ✅ Pure C, zéro dépendance
- ✅ Portable (Linux/macOS/Windows/WASM/Raspberry Pi)
- ✅ Types: `float`, `int8`, `binary`
- ✅ Installation: `pip install sqlite-vec`
- ✅ SIMD optimisé (AVX, NEON)
- ⚠️ Brute-force uniquement (pas d'index IVFFlat/HNSW comme pgvector)

**API SQL** :
```sql
-- Charger extension
SELECT load_extension('vec0');

-- Créer table virtuelle
CREATE VIRTUAL TABLE vec_embeddings USING vec0(
    embedding float[1024]
);

-- Insertion
INSERT INTO vec_embeddings(rowid, embedding)
VALUES (1, '[0.1, 0.2, 0.3, ...]');

-- KNN Search
SELECT rowid, distance
FROM vec_embeddings
WHERE embedding MATCH '[0.5, 0.6, ...]'
  AND k = 10
ORDER BY distance
LIMIT 10;
```

**Performance** (benchmarks auteur) :
- 10K vecteurs (384D) : ~5ms
- 100K vecteurs (384D) : ~17ms
- 500K vecteurs (768D) : ~52ms
- 1M vecteurs (1536D) : ~87ms

**Installation Linux** :
```bash
# Via pip (installe .so compiled)
pip install sqlite-vec

# Location typique
/usr/local/lib/python3.x/site-packages/sqlite_vec/vec0.so
```

### 3.2 SpatiaLite

**Source** : https://www.gaia-gis.it/fossil/libspatialite/
**Version** : 5.1.0 (2023-08-04)
**Licence** : MPL 1.1 / GPL v2+ / LGPL v2.1+ (tri-licence)

**Caractéristiques** :
- ✅ 200+ fonctions spatiales
- ✅ Conforme OGC-SFS
- ✅ Support SRID multiples (transformations projections)
- ✅ Index R-Tree pour requêtes spatiales
- ✅ Import/Export : Shapefile, GeoJSON, KML, WKT, WKB

**Dépendances système** :
- libspatialite7
- libgeos (géométrie computationnelle)
- libproj (transformations coordonnées)
- libsqlite3

**API SQL** :
```sql
-- Charger extension
SELECT load_extension('mod_spatialite');

-- Initialiser metadata
SELECT InitSpatialMetadata(1);

-- Créer colonne géométrique
SELECT AddGeometryColumn('locations', 'geom', 4326, 'POINT', 2);

-- Fonctions spatiales
SELECT ST_Distance(
    ST_GeomFromText('POINT(2.3 48.8)', 4326),
    ST_GeomFromText('POINT(-0.1 51.5)', 4326)
) / 1000 AS distance_km;

SELECT ST_Area(
    ST_GeomFromText('POLYGON((...))', 4326)
) AS area_m2;

SELECT ST_Intersects(geom1, geom2);
SELECT ST_Buffer(geom, 1000); -- 1km buffer
```

**Installation Ubuntu/Debian** :
```bash
apt-get install -y \
    libspatialite7 \
    libspatialite-dev \
    spatialite-bin
```

**Fichier extension** :
```
/usr/lib/x86_64-linux-gnu/mod_spatialite.so
```

---

## 4. Système de Chargement d'Extensions SQLite

### 4.1 Méthode node-sqlite3

```typescript
// API node-sqlite3 standard
import * as sqlite3 from 'sqlite3';

const db = new sqlite3.Database('/path/to/db.sqlite');

db.loadExtension('/path/to/extension.so', (err) => {
    if (err) {
        console.error('Failed to load extension:', err);
    } else {
        console.log('Extension loaded successfully');
    }
});
```

### 4.2 Intégration dans Grist

**Point d'entrée** : `/app/server/lib/SqliteNode.ts`

```typescript
export class NodeSqlite3DatabaseAdapter implements MinDB {
  public static async opener(dbPath: string, mode: OpenMode): Promise<any> {
    const sqliteMode = /* ... */;
    let _db: sqlite3.Database;
    await fromCallback(cb => {
        _db = new sqlite3.Database(dbPath, sqliteMode, cb);
    });
    const result = new NodeSqlite3DatabaseAdapter(_db!);

    // 🎯 POINT D'INJECTION : Charger extensions ici
    await result._loadExtensions();

    await result.limitAttach(0);
    return result;
  }

  // ✅ NOUVELLE MÉTHODE À AJOUTER
  private async _loadExtensions(): Promise<void> {
    try {
      // sqlite-vec
      await fromCallback(cb =>
        this._db.loadExtension('vec0', cb)
      );
      log.info('sqlite-vec loaded');

      // SpatiaLite
      await fromCallback(cb =>
        this._db.loadExtension('mod_spatialite', cb)
      );
      await this.exec("SELECT InitSpatialMetadata(1)");
      log.info('SpatiaLite loaded');

    } catch (err) {
      log.warn('Extensions not available:', err);
      // Continuer sans extensions (graceful degradation)
    }
  }
}
```

### 4.3 Configuration Paths Extensions

**Option A** : Variables d'environnement
```bash
# .env ou docker-compose.yml
SQLITE_VEC_PATH=/usr/local/lib/python3.x/site-packages/sqlite_vec/vec0.so
SPATIALITE_PATH=/usr/lib/x86_64-linux-gnu/mod_spatialite.so
```

**Option B** : Auto-détection
```typescript
private _findExtension(name: string): string | null {
  const searchPaths = [
    `/usr/local/lib/python3.x/site-packages/sqlite_vec/${name}.so`,
    `/usr/lib/x86_64-linux-gnu/${name}.so`,
    `/usr/lib/${name}.so`,
    `./extensions/${name}.so`,
  ];

  for (const path of searchPaths) {
    if (fs.existsSync(path)) {
      return path;
    }
  }
  return null;
}
```

**Option C** : Nom court (si dans LD_LIBRARY_PATH)
```typescript
// SQLite cherche dans :
// - LD_LIBRARY_PATH
// - /usr/lib, /usr/local/lib
// - Dossier du binaire sqlite3

await this._db.loadExtension('vec0');  // Cherche vec0.so
await this._db.loadExtension('mod_spatialite');
```

---

## 5. Feuille de Route en 3 Phases

### Phase 1 : sqlite-vec (Vecteurs Optimisés)

**Durée estimée** : 5-7 jours
**Objectif** : Remplacer recherche Python O(n) par index SQLite natif

#### 5.1.1 Préparation (Jour 1)

**Dockerfile** :
```dockerfile
# Ajouter à /root/docker/Grist/Dockerfile

# Installation sqlite-vec
RUN pip install sqlite-vec==0.1.0

# Vérifier installation
RUN python3 -c "import sqlite_vec; print('sqlite-vec installed:', sqlite_vec.__version__)"
```

**Build et test** :
```bash
cd /root/docker/Grist
docker-compose build grist
docker-compose up -d
docker-compose logs grist | grep -i "sqlite-vec"
```

#### 5.1.2 Intégration Backend (Jours 2-3)

**Fichier** : `/app/server/lib/SqliteNode.ts`

```typescript
// Ajouter après ligne 41
private async _loadExtensions(): Promise<void> {
  const extensions = [
    { name: 'vec0', init: null },
  ];

  for (const ext of extensions) {
    try {
      await fromCallback(cb => this._db.loadExtension(ext.name, cb));
      if (ext.init) {
        await this.exec(ext.init);
      }
      log.info(`Extension ${ext.name} loaded successfully`);
    } catch (err) {
      log.warn(`Extension ${ext.name} not available:`, err.message);
    }
  }
}

// Modifier opener() ligne 32
public static async opener(dbPath: string, mode: OpenMode): Promise<any> {
  // ... code existant ...
  const result = new NodeSqlite3DatabaseAdapter(_db!);
  await result._loadExtensions();  // ✅ AJOUT
  await result.limitAttach(0);
  return result;
}
```

**Tests** :
```typescript
// test/server/lib/sqlite-vec.ts
import { SQLiteDB } from 'app/server/lib/SQLiteDB';

describe('sqlite-vec integration', () => {
  it('should load vec0 extension', async () => {
    const db = await SQLiteDB.openDB(':memory:', schemaInfo);

    // Test création table virtuelle
    await db.exec(`
      CREATE VIRTUAL TABLE test_vec USING vec0(
        embedding float[8]
      )
    `);

    // Test insertion
    await db.run(`
      INSERT INTO test_vec(rowid, embedding)
      VALUES (1, '[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]')
    `);

    // Test recherche KNN
    const results = await db.all(`
      SELECT rowid, distance
      FROM test_vec
      WHERE embedding MATCH '[0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]'
        AND k = 1
      LIMIT 1
    `);

    assert.equal(results.length, 1);
    await db.close();
  });
});
```

#### 5.1.3 Migration Données (Jour 4)

**Stratégie** : Créer tables vec0 parallèles aux tables existantes

```python
# sandbox/grist/embedding_manager.py

def migrate_to_vec0(table_id: str, doc_storage):
    """
    Migrer embeddings JSON → table vec0
    """
    # 1. Créer table virtuelle vec0
    doc_storage.exec(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_{table_id}
        USING vec0(embedding float[1024])
    """)

    # 2. Migrer données existantes
    records = doc_storage.all(f"""
        SELECT id, grist_record_embedding
        FROM {table_id}
        WHERE grist_record_embedding IS NOT NULL
    """)

    for record in records:
        embedding_json = record['grist_record_embedding']
        doc_storage.run(f"""
            INSERT INTO vec_{table_id}(rowid, embedding)
            VALUES (?, ?)
        """, record['id'], embedding_json)

    log.info(f"Migrated {len(records)} embeddings to vec_{table_id}")
```

**Trigger auto-sync** :
```sql
-- Garder JSON et vec0 synchronisés
CREATE TRIGGER IF NOT EXISTS sync_vec_{table_id}
AFTER INSERT ON {table_id}
FOR EACH ROW
WHEN NEW.grist_record_embedding IS NOT NULL
BEGIN
    INSERT OR REPLACE INTO vec_{table_id}(rowid, embedding)
    VALUES (NEW.id, NEW.grist_record_embedding);
END;
```

#### 5.1.4 Adaptation Fonctions Python (Jour 5)

**Fichier** : `/sandbox/grist/usertypes.py`

```python
def VECTOR_SEARCH(table, query: str, threshold: float = 0.75, limit: int = 20, embedding_column: str = None):
    """
    Version optimisée avec sqlite-vec
    """
    try:
        from embedding_manager import VECTOR_SEARCH_VEC0

        # Extraire table_id
        table_id = table.table.table_id if hasattr(table, 'table') else None
        if not table_id:
            raise ValueError("Invalid table parameter")

        # Appeler version optimisée
        results = VECTOR_SEARCH_VEC0(
            table_id,
            query,
            limit=limit,
            threshold=threshold,
            embedding_column=embedding_column
        )

        return [r['row_id'] for r in results]

    except Exception as e:
        log.error(f"VECTOR_SEARCH error: {e}")
        return []
```

```python
# embedding_manager.py

def VECTOR_SEARCH_VEC0(table_id: str, query: str, limit: int, threshold: float, embedding_column: str):
    """
    Recherche vectorielle optimisée via sqlite-vec
    """
    # 1. Générer embedding requête
    query_embedding = generate_embedding(query, 'albert')
    if not query_embedding:
        return []

    # 2. Requête KNN via vec0
    vec_table = f"vec_{table_id}"

    results = execute_sql(f"""
        SELECT rowid, distance
        FROM {vec_table}
        WHERE embedding MATCH ?
          AND k = ?
        ORDER BY distance
        LIMIT ?
    """, [json.dumps(query_embedding), limit * 2, limit * 2])

    # 3. Filtrer par threshold
    # Note: distance cosinus dans vec0, convertir en similarité
    filtered = [
        {'row_id': r['rowid'], 'score': 1 - r['distance']}
        for r in results
        if (1 - r['distance']) >= threshold
    ]

    return filtered[:limit]
```

#### 5.1.5 Tests & Validation (Jours 6-7)

**Benchmarks performance** :
```python
# test_vector_search_performance.py

import time

def benchmark_vector_search():
    # Créer table test avec 50K embeddings
    create_test_data(50000)

    # Test 1: Python O(n) actuel
    start = time.time()
    results_python = VECTOR_SEARCH_PYTHON(table, query)
    time_python = time.time() - start

    # Test 2: sqlite-vec
    start = time.time()
    results_vec0 = VECTOR_SEARCH_VEC0(table, query)
    time_vec0 = time.time() - start

    print(f"Python O(n): {time_python:.2f}s")
    print(f"sqlite-vec: {time_vec0:.2f}s")
    print(f"Speedup: {time_python / time_vec0:.1f}x")

    # Vérifier résultats identiques
    assert set(results_python) == set(results_vec0)
```

**Tests fonctionnels** :
- ✅ Insertion embedding → sync automatique vec0
- ✅ UPDATE embedding → mise à jour vec0
- ✅ DELETE record → suppression vec0
- ✅ VECTOR_SEARCH retourne résultats identiques
- ✅ Performance amélioration mesurable

---

### Phase 2 : SpatiaLite (Fonctions Spatiales)

**Durée estimée** : 7-10 jours
**Objectif** : Ajouter 200+ fonctions spatiales natives

#### 5.2.1 Installation Système (Jour 1)

**Dockerfile** :
```dockerfile
# Dépendances SpatiaLite
RUN apt-get update && apt-get install -y \
    libspatialite7 \
    libspatialite-dev \
    spatialite-bin \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Vérifier installation
RUN spatialite -version
RUN find /usr/lib -name "mod_spatialite.so"
```

#### 5.2.2 Chargement Extension (Jour 2)

**Fichier** : `/app/server/lib/SqliteNode.ts`

```typescript
private async _loadExtensions(): Promise<void> {
  const extensions = [
    { name: 'vec0', init: null },
    {
      name: 'mod_spatialite',
      init: 'SELECT InitSpatialMetadata(1)'
    },
  ];

  for (const ext of extensions) {
    try {
      await fromCallback(cb => this._db.loadExtension(ext.name, cb));

      if (ext.init) {
        await this.exec(ext.init);
      }

      log.info(`✅ Extension ${ext.name} loaded`);
    } catch (err) {
      log.warn(`⚠️ Extension ${ext.name} not available:`, err.message);
    }
  }
}
```

**Tests** :
```typescript
it('should load SpatiaLite extension', async () => {
  const db = await SQLiteDB.openDB(':memory:', schemaInfo);

  // Test fonction spatiale
  const result = await db.get(`
    SELECT ST_Distance(
      ST_GeomFromText('POINT(2.3 48.8)', 4326),
      ST_GeomFromText('POINT(-0.1 51.5)', 4326)
    ) AS distance
  `);

  assert.ok(result.distance > 0);
  await db.close();
});
```

#### 5.2.3 Wrapper Python (Jours 3-6)

**Créer** : `/sandbox/grist/functions/spatial.py`

```python
"""
Fonctions spatiales natives via SpatiaLite
Remplace implémentations Python par délégation SQL
"""

import logging
log = logging.getLogger(__name__)

def _execute_spatial_sql(sql: str, *params):
    """
    Exécuter requête SQL spatiale sur document courant
    """
    from grist import get_doc_storage
    doc = get_doc_storage()
    return doc.fetchQuery(sql, params)

# ============================================================================
# CONSTRUCTEURS
# ============================================================================

def ST_MakePoint(x: float, y: float, srid: int = 4326) -> str:
    """Créer point WKT depuis coordonnées"""
    result = _execute_spatial_sql(
        "SELECT ST_AsText(ST_SetSRID(ST_MakePoint(?, ?), ?)) AS wkt",
        x, y, srid
    )
    return result[0]['wkt'] if result else None

def ST_GeomFromGeoJSON(geojson_str: str) -> str:
    """Convertir GeoJSON vers WKT"""
    result = _execute_spatial_sql(
        "SELECT ST_AsText(ST_GeomFromGeoJSON(?)) AS wkt",
        geojson_str
    )
    return result[0]['wkt'] if result else None

# ============================================================================
# MESURES
# ============================================================================

def ST_Distance(geom1: str, geom2: str, unit: str = 'm') -> float:
    """
    Distance géodésique entre géométries
    """
    # Utiliser geography pour calcul précis
    result = _execute_spatial_sql("""
        SELECT ST_Distance(
            CastToXY(ST_GeomFromText(?)),
            CastToXY(ST_GeomFromText(?))
        ) AS distance
    """, geom1, geom2)

    distance_m = result[0]['distance'] if result else 0

    if unit == 'km':
        return distance_m / 1000
    elif unit == 'deg':
        return distance_m / 111320  # Approx
    return distance_m

def ST_Length(linestring: str, unit: str = 'm') -> float:
    """Longueur ligne géodésique"""
    result = _execute_spatial_sql("""
        SELECT ST_Length(
            CastToXY(ST_GeomFromText(?))
        ) AS length
    """, linestring)

    length_m = result[0]['length'] if result else 0

    if unit == 'km':
        return length_m / 1000
    return length_m

def ST_Area(geometry: str, unit: str = 'm2') -> float:
    """Aire polygone géodésique"""
    result = _execute_spatial_sql("""
        SELECT ST_Area(
            CastToXY(ST_GeomFromText(?))
        ) AS area
    """, geometry)

    area_m2 = result[0]['area'] if result else 0

    if unit == 'km2':
        return area_m2 / 1_000_000
    elif unit == 'ha':
        return area_m2 / 10_000
    return area_m2

def ST_Perimeter(geometry: str, unit: str = 'm') -> float:
    """Périmètre polygone"""
    result = _execute_spatial_sql("""
        SELECT ST_Perimeter(
            CastToXY(ST_GeomFromText(?))
        ) AS perimeter
    """, geometry)

    perim_m = result[0]['perimeter'] if result else 0

    if unit == 'km':
        return perim_m / 1000
    return perim_m

# ============================================================================
# RELATIONS SPATIALES
# ============================================================================

def ST_Intersects(geom1: str, geom2: str) -> bool:
    """Tester intersection"""
    result = _execute_spatial_sql("""
        SELECT ST_Intersects(
            ST_GeomFromText(?),
            ST_GeomFromText(?)
        ) AS intersects
    """, geom1, geom2)

    return bool(result[0]['intersects']) if result else False

def ST_Within(geom1: str, geom2: str) -> bool:
    """geom1 dans geom2"""
    result = _execute_spatial_sql("""
        SELECT ST_Within(
            ST_GeomFromText(?),
            ST_GeomFromText(?)
        ) AS within
    """, geom1, geom2)

    return bool(result[0]['within']) if result else False

def ST_Contains(geom1: str, geom2: str) -> bool:
    """geom1 contient geom2"""
    result = _execute_spatial_sql("""
        SELECT ST_Contains(
            ST_GeomFromText(?),
            ST_GeomFromText(?)
        ) AS contains
    """, geom1, geom2)

    return bool(result[0]['contains']) if result else False

def ST_Crosses(geom1: str, geom2: str) -> bool:
    """Tester croisement"""
    result = _execute_spatial_sql("""
        SELECT ST_Crosses(
            ST_GeomFromText(?),
            ST_GeomFromText(?)
        ) AS crosses
    """, geom1, geom2)

    return bool(result[0]['crosses']) if result else False

def ST_Overlaps(geom1: str, geom2: str) -> bool:
    """Tester chevauchement"""
    result = _execute_spatial_sql("""
        SELECT ST_Overlaps(
            ST_GeomFromText(?),
            ST_GeomFromText(?)
        ) AS overlaps
    """, geom1, geom2)

    return bool(result[0]['overlaps']) if result else False

def ST_Touches(geom1: str, geom2: str) -> bool:
    """Tester contact"""
    result = _execute_spatial_sql("""
        SELECT ST_Touches(
            ST_GeomFromText(?),
            ST_GeomFromText(?)
        ) AS touches
    """, geom1, geom2)

    return bool(result[0]['touches']) if result else False

def ST_Disjoint(geom1: str, geom2: str) -> bool:
    """Tester disjonction"""
    result = _execute_spatial_sql("""
        SELECT ST_Disjoint(
            ST_GeomFromText(?),
            ST_GeomFromText(?)
        ) AS disjoint
    """, geom1, geom2)

    return bool(result[0]['disjoint']) if result else False

# ============================================================================
# TRANSFORMATIONS
# ============================================================================

def ST_Buffer(geometry: str, distance: float, unit: str = 'm') -> str:
    """Zone tampon"""
    # Convertir distance en unité géométrique
    if unit == 'km':
        distance = distance * 1000
    distance_deg = distance / 111320

    result = _execute_spatial_sql("""
        SELECT ST_AsText(
            ST_Buffer(ST_GeomFromText(?), ?)
        ) AS wkt
    """, geometry, distance_deg)

    return result[0]['wkt'] if result else None

def ST_Union(geom1: str, geom2: str) -> str:
    """Union géométries"""
    result = _execute_spatial_sql("""
        SELECT ST_AsText(
            ST_Union(
                ST_GeomFromText(?),
                ST_GeomFromText(?)
            )
        ) AS wkt
    """, geom1, geom2)

    return result[0]['wkt'] if result else None

def ST_Intersection(geom1: str, geom2: str) -> str:
    """Intersection géométries"""
    result = _execute_spatial_sql("""
        SELECT ST_AsText(
            ST_Intersection(
                ST_GeomFromText(?),
                ST_GeomFromText(?)
            )
        ) AS wkt
    """, geom1, geom2)

    return result[0]['wkt'] if result else None

def ST_Difference(geom1: str, geom2: str) -> str:
    """Différence géométrique"""
    result = _execute_spatial_sql("""
        SELECT ST_AsText(
            ST_Difference(
                ST_GeomFromText(?),
                ST_GeomFromText(?)
            )
        ) AS wkt
    """, geom1, geom2)

    return result[0]['wkt'] if result else None

def ST_Simplify(geometry: str, tolerance: float) -> str:
    """Simplifier géométrie"""
    result = _execute_spatial_sql("""
        SELECT ST_AsText(
            ST_Simplify(ST_GeomFromText(?), ?)
        ) AS wkt
    """, geometry, tolerance)

    return result[0]['wkt'] if result else None

def ST_ConvexHull(geometry: str) -> str:
    """Enveloppe convexe"""
    result = _execute_spatial_sql("""
        SELECT ST_AsText(
            ST_ConvexHull(ST_GeomFromText(?))
        ) AS wkt
    """, geometry)

    return result[0]['wkt'] if result else None

# ============================================================================
# ACCESSEURS
# ============================================================================

def ST_X(point: str) -> float:
    """Coordonnée X"""
    result = _execute_spatial_sql("""
        SELECT ST_X(ST_GeomFromText(?)) AS x
    """, point)

    return result[0]['x'] if result else None

def ST_Y(point: str) -> float:
    """Coordonnée Y"""
    result = _execute_spatial_sql("""
        SELECT ST_Y(ST_GeomFromText(?)) AS y
    """, point)

    return result[0]['y'] if result else None

def ST_NumPoints(geometry: str) -> int:
    """Nombre de points"""
    result = _execute_spatial_sql("""
        SELECT ST_NumPoints(ST_GeomFromText(?)) AS count
    """, geometry)

    return result[0]['count'] if result else 0

def ST_StartPoint(linestring: str) -> str:
    """Point départ ligne"""
    result = _execute_spatial_sql("""
        SELECT ST_AsText(
            ST_StartPoint(ST_GeomFromText(?))
        ) AS wkt
    """, linestring)

    return result[0]['wkt'] if result else None

def ST_EndPoint(linestring: str) -> str:
    """Point fin ligne"""
    result = _execute_spatial_sql("""
        SELECT ST_AsText(
            ST_EndPoint(ST_GeomFromText(?))
        ) AS wkt
    """, linestring)

    return result[0]['wkt'] if result else None

def ST_Centroid(geometry: str) -> str:
    """Centre géométrique"""
    result = _execute_spatial_sql("""
        SELECT ST_AsText(
            ST_Centroid(ST_GeomFromText(?))
        ) AS wkt
    """, geometry)

    return result[0]['wkt'] if result else None

def ST_Boundary(geometry: str) -> str:
    """Frontière géométrie"""
    result = _execute_spatial_sql("""
        SELECT ST_AsText(
            ST_Boundary(ST_GeomFromText(?))
        ) AS wkt
    """, geometry)

    return result[0]['wkt'] if result else None

def ST_Envelope(geometry: str) -> str:
    """Boîte englobante"""
    result = _execute_spatial_sql("""
        SELECT ST_AsText(
            ST_Envelope(ST_GeomFromText(?))
        ) AS wkt
    """, geometry)

    return result[0]['wkt'] if result else None

# ============================================================================
# CONVERSIONS
# ============================================================================

def ST_AsGeoJSON(geometry: str) -> str:
    """Convertir WKT → GeoJSON"""
    result = _execute_spatial_sql("""
        SELECT ST_AsGeoJSON(ST_GeomFromText(?)) AS geojson
    """, geometry)

    return result[0]['geojson'] if result else None

def ST_AsKML(geometry: str) -> str:
    """Convertir WKT → KML"""
    result = _execute_spatial_sql("""
        SELECT ST_AsKML(ST_GeomFromText(?)) AS kml
    """, geometry)

    return result[0]['kml'] if result else None

def ST_AsText(geometry: str) -> str:
    """Alias (déjà WKT)"""
    return geometry

# ============================================================================
# VALIDATION
# ============================================================================

def ST_IsValid(geometry: str) -> bool:
    """Valider géométrie"""
    result = _execute_spatial_sql("""
        SELECT ST_IsValid(ST_GeomFromText(?)) AS valid
    """, geometry)

    return bool(result[0]['valid']) if result else False

def ST_IsSimple(geometry: str) -> bool:
    """Test simplicité"""
    result = _execute_spatial_sql("""
        SELECT ST_IsSimple(ST_GeomFromText(?)) AS simple
    """, geometry)

    return bool(result[0]['simple']) if result else False

def ST_IsEmpty(geometry: str) -> bool:
    """Test vacuité"""
    result = _execute_spatial_sql("""
        SELECT ST_IsEmpty(ST_GeomFromText(?)) AS empty
    """, geometry)

    return bool(result[0]['empty']) if result else True
```

#### 5.2.4 Import Module (Jour 7)

**Fichier** : `/sandbox/grist/functions/__init__.py`

```python
# Ajouter import spatial
from .date import *
from .info import *
from .logical import *
from .lookup import *
from .math import *
from .stats import *
from .text import *
from .schedule import *
from .prevnext import *
from .spatial import *  # ✅ NOUVEAU

# Export
__all__ = [k for k in dir() if not k.startswith('_') and k.isupper()]
```

#### 5.2.5 Tests & Benchmarks (Jours 8-10)

**Tests fonctionnels** :
```python
# test/server/spatialite.test.py

def test_st_distance():
    paris = "POINT(2.3522 48.8566)"
    london = "POINT(-0.1276 51.5074)"

    distance_km = ST_Distance(paris, london, 'km')

    # Distance réelle Paris-Londres ≈ 344 km
    assert 340 < distance_km < 350

def test_st_area():
    # Carré 1°×1° à Paris
    square = "POLYGON((2 48, 3 48, 3 49, 2 49, 2 48))"

    area_km2 = ST_Area(square, 'km2')

    # Environ 7400 km² (dépend latitude)
    assert 7000 < area_km2 < 8000

def test_st_buffer():
    point = "POINT(2.3 48.8)"

    # Buffer 1km
    buffered = ST_Buffer(point, 1000, 'm')

    assert buffered.startswith('POLYGON')
    assert ST_Area(buffered, 'm2') > 3_000_000  # Environ π×1000²

def test_all_spatial_functions():
    # Tester TOUTES les fonctions
    functions = [
        'ST_Distance', 'ST_Area', 'ST_Length', 'ST_Perimeter',
        'ST_Intersects', 'ST_Within', 'ST_Contains', 'ST_Crosses',
        'ST_Buffer', 'ST_Union', 'ST_Intersection',
        'ST_X', 'ST_Y', 'ST_Centroid',
        'ST_AsGeoJSON', 'ST_IsValid'
    ]

    for func_name in functions:
        func = globals()[func_name]
        assert callable(func), f"{func_name} not found"
```

**Benchmarks performance** :
```python
def benchmark_spatial_functions():
    # Python natif vs SpatiaLite

    # ST_Distance
    start = time.time()
    for _ in range(1000):
        ST_Distance_Python(p1, p2)
    time_python = time.time() - start

    start = time.time()
    for _ in range(1000):
        ST_Distance(p1, p2)  # SpatiaLite
    time_spatial = time.time() - start

    print(f"Distance: Python={time_python:.2f}s, SpatiaLite={time_spatial:.2f}s")
    print(f"Speedup: {time_python / time_spatial:.1f}x")
```

---

### Phase 3 : Intégration Hybride & Optimisations

**Durée estimée** : 3-5 jours
**Objectif** : Requêtes combinées spatial + sémantique

#### 5.3.1 Requêtes Hybrides (Jours 1-2)

**Exemple cas d'usage** : "Restaurants végétariens dans 2km"

```python
# Nouvelle fonction sandbox/grist/functions/hybrid.py

def SPATIAL_VECTOR_SEARCH(
    table,
    query: str,
    location: str,
    radius: float = 5000,
    threshold: float = 0.75,
    limit: int = 10
):
    """
    Recherche combinée sémantique + spatiale

    Args:
        table: Table Grist
        query: Requête texte sémantique
        location: Point WKT ou "USER_LOCATION"
        radius: Rayon en mètres
        threshold: Seuil similarité (0-1)
        limit: Nombre max résultats

    Returns:
        list[int]: IDs records matchant les 2 critères

    Example:
        # Trouver restaurants végétariens proches
        SPATIAL_VECTOR_SEARCH(
            Restaurants,
            "végétarien bio",
            "POINT(2.3 48.8)",  # Paris
            radius=2000,  # 2km
            threshold=0.8
        )
    """
    table_id = table.table.table_id

    # 1. Recherche sémantique via vec0
    semantic_results = VECTOR_SEARCH_VEC0(
        table_id, query, limit=limit*2, threshold=threshold
    )
    semantic_ids = [r['row_id'] for r in semantic_results]

    if not semantic_ids:
        return []

    # 2. Filtrage spatial via SpatiaLite
    # Récupérer nom colonne géométrique
    geom_column = _find_geometry_column(table_id)
    if not geom_column:
        return semantic_ids  # Pas de filtre spatial

    # Requête SQL hybride
    spatial_filtered = execute_sql(f"""
        SELECT id
        FROM {table_id}
        WHERE id IN ({','.join(['?']*len(semantic_ids))})
          AND ST_Distance(
              ST_GeomFromText({geom_column}),
              ST_GeomFromText(?)
          ) <= ?
    """, *semantic_ids, location, radius)

    return [r['id'] for r in spatial_filtered]
```

**Frontend Widget** : Map + Search

```typescript
// app/client/widgets/SpatialVectorWidget.ts

export class SpatialVectorWidget extends BaseWidget {
  // Afficher carte interactive + barre recherche
  // Résultats avec pins géolocalisés + scores sémantiques
}
```

#### 5.3.2 Index R-Tree Spatial (Jour 3)

**Optimisation requêtes spatiales** :

```python
def create_spatial_index(table_id: str, geom_column: str):
    """
    Créer index R-Tree pour colonne géométrique
    """
    execute_sql(f"""
        SELECT CreateSpatialIndex('{table_id}', '{geom_column}')
    """)

    log.info(f"Created R-Tree index on {table_id}.{geom_column}")
```

**Performance attendue** :
- Sans index : O(n) scan complet
- Avec R-Tree : O(log n) recherche spatiale

#### 5.3.3 Documentation Utilisateur (Jours 4-5)

**Fichier** : `/documentation/spatial-vector-guide.md`

Contenu :
- Guide démarrage rapide
- Liste complète fonctions (50+ fonctions ST_*)
- Exemples cas d'usage
- Benchmarks performance
- FAQ / Troubleshooting

---

## 6. Points Critiques & Risques

### 6.1 Risques Techniques

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| **Extensions non chargeables** | ⭐⭐⭐ Bloquant | Faible | Tests sur environnements multiples, fallback gracieux |
| **Conflit versions SQLite** | ⭐⭐ Moyen | Moyenne | Utiliser @gristlabs/sqlite3 v5.1.4+ |
| **Performance dégradée** | ⭐⭐⭐ Moyen | Faible | Benchmarks avant/après, optimisation requêtes |
| **Migration données existantes** | ⭐⭐ Moyen | Moyenne | Script migration incrémentale, rollback possible |
| **Compatibilité Python sandbox** | ⭐⭐ Moyen | Faible | IPC bien défini, tests unitaires |

### 6.2 Points d'Attention

1. **Paths Extensions** : Varient selon OS/distribution
   - Solution : Auto-détection + config env vars

2. **Overhead Mémoire** : SpatiaLite ~10-20 MB
   - Solution : Acceptable pour les gains fonctionnels

3. **Breaking Changes** : sqlite-vec pre-v1
   - Solution : Pin version exacte, suivi releases

4. **Permissions Fichiers** : Extensions .so nécessitent droits lecture
   - Solution : Dockerfile COPY avec chmod approprié

---

## 7. Tests & Validation

### 7.1 Stratégie de Tests

**Niveaux** :
1. ✅ **Unitaires** : Chaque fonction ST_* isolément
2. ✅ **Intégration** : Chargement extensions + requêtes SQL
3. ✅ **End-to-End** : Formules Grist → résultats corrects
4. ✅ **Performance** : Benchmarks avant/après
5. ✅ **Régression** : Tests existants ne cassent pas

### 7.2 Checklist Pre-Release

**Phase 1 (sqlite-vec)** :
- [ ] Extension charge sans erreur (Linux/Docker)
- [ ] Tables vec0 créées avec succès
- [ ] KNN search retourne résultats cohérents
- [ ] Performance 10-50× meilleure que Python O(n)
- [ ] Migration données existantes sans perte
- [ ] Tests CI/CD passent

**Phase 2 (SpatiaLite)** :
- [ ] Extension charge sans erreur
- [ ] 50+ fonctions ST_* fonctionnelles
- [ ] Calculs géométriques précis (vs Python)
- [ ] Support LINESTRING, MULTIPOINT, etc.
- [ ] Import/Export GeoJSON opérationnel
- [ ] Tests CI/CD passent

**Phase 3 (Hybride)** :
- [ ] Requêtes spatial+vector combinées
- [ ] Index R-Tree améliore performance
- [ ] Documentation utilisateur complète
- [ ] Exemples cas d'usage validés
- [ ] Tests CI/CD passent

---

## 8. Prochaines Étapes

### Immédiat (Cette Session)

1. ✅ Valider architecture documentée
2. ✅ Confirmer approche technique
3. 🔄 **Démarrer Phase 1.1** : Modifier Dockerfile

### Session Suivante

1. 🔄 Continuer Phase 1.2 : Intégration backend
2. 🔄 Tests sqlite-vec basiques
3. 🔄 Premier benchmark performance

---

## 9. Références

**Extensions** :
- sqlite-vec: https://github.com/asg017/sqlite-vec
- SpatiaLite: https://www.gaia-gis.it/fossil/libspatialite/

**Grist** :
- Architecture: https://github.com/gristlabs/grist-core
- Types: `/app/common/gristTypes.ts`
- SQLite wrapper: `/app/server/lib/SQLiteDB.ts`

**SQLite** :
- node-sqlite3: https://github.com/TryGhost/node-sqlite3
- @gristlabs/sqlite3: https://github.com/gristlabs/node-sqlite3
- Extension loading: https://www.sqlite.org/loadext.html

---

**Dernière mise à jour** : 2025-01-19 19:45 UTC
**Status** : 📚 Documentation complète, prêt pour implémentation
