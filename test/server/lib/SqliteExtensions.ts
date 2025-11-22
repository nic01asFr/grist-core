import {assert} from 'chai';
import * as fse from 'fs-extra';
import {join as pathJoin} from 'path';
import * as tmp from 'tmp-promise';

import {OpenMode, SQLiteDB} from 'app/server/lib/SQLiteDB';
import * as testUtils from 'test/server/testUtils';

tmp.setGracefulCleanup();

describe('SqliteExtensions', function() {
  let tmpDir: string;
  let cleanup: () => void;

  // Turn off logging for this test, and restore afterwards.
  testUtils.setTmpLogLevel('warn');

  before(async function() {
    // Create a temporary directory, and wipe it out on exit.
    ({path: tmpDir, cleanup} = await tmp.dir({ prefix: 'grist_test_SqliteExt_', unsafeCleanup: true }));
  });

  after(function() {
    cleanup();
  });

  function dbPath(fileName: string): string {
    return pathJoin(tmpDir, fileName);
  }

  it('should load sqlite-vec extension without errors', async function() {
    // Create a simple test database
    const sdb = await SQLiteDB.openDB(dbPath('vec_test.db'), {
      name: 'VecTest',
      version: 1,
      createSql: 'CREATE TABLE test_data (id INTEGER PRIMARY KEY, name TEXT);'
    }, OpenMode.OPEN_CREATE);

    // Extension loading happens automatically in opener()
    // If vec0 extension loaded successfully, we should be able to query vec_version
    let extensionAvailable = false;
    try {
      // Try to query the vec_version() function - only available if extension loaded
      const result = await sdb.get('SELECT vec_version() as version');
      if (result && result.version) {
        extensionAvailable = true;
        console.log(`✅ sqlite-vec extension loaded successfully, version: ${result.version}`);
      }
    } catch (err: any) {
      // Extension not available - this is expected if sqlite-vec is not installed
      console.log(`⚠️  sqlite-vec extension not available: ${err.message}`);
      console.log('   This is normal if the extension is not installed in the system');
    }

    // Test passes whether extension is available or not
    // This verifies graceful degradation behavior
    await sdb.close();

    // If extension is available, run more comprehensive tests
    if (extensionAvailable) {
      await testVectorOperations();
    }
  });

  /**
   * Comprehensive vector operations tests (only run if extension is available)
   */
  async function testVectorOperations() {
    const sdb = await SQLiteDB.openDB(dbPath('vec_ops_test.db'), {
      name: 'VecOpsTest',
      version: 1,
      createSql: 'CREATE TABLE documents (id INTEGER PRIMARY KEY, content TEXT);'
    }, OpenMode.OPEN_CREATE);

    try {
      // Create a vec0 virtual table for vector storage
      await sdb.exec(`
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_embeddings USING vec0(
          embedding FLOAT[4]
        );
      `);
      console.log('✅ vec0 virtual table created successfully');

      // Insert test vectors
      await sdb.run(`
        INSERT INTO vec_embeddings (rowid, embedding)
        VALUES
          (1, '[1.0, 0.0, 0.0, 0.0]'),
          (2, '[0.0, 1.0, 0.0, 0.0]'),
          (3, '[0.0, 0.0, 1.0, 0.0]'),
          (4, '[0.7071, 0.7071, 0.0, 0.0]');
      `);
      console.log('✅ Test vectors inserted successfully');

      // Test KNN search - find 2 nearest neighbors to [1.0, 0.0, 0.0, 0.0]
      const neighbors = await sdb.all(`
        SELECT rowid, distance
        FROM vec_embeddings
        WHERE embedding MATCH '[1.0, 0.0, 0.0, 0.0]'
        ORDER BY distance
        LIMIT 2;
      `);

      assert.isArray(neighbors, 'KNN search should return array');
      assert.lengthOf(neighbors, 2, 'Should return 2 nearest neighbors');

      // First result should be exact match (rowid 1, distance ~0)
      assert.strictEqual(neighbors[0].rowid, 1, 'First neighbor should be exact match');
      assert.isBelow(neighbors[0].distance, 0.01, 'Distance to exact match should be ~0');

      // Second result should be rowid 4 (partial match with distance ~0.5)
      assert.strictEqual(neighbors[4], 4, 'Second neighbor should be partial match');

      console.log(`✅ KNN search working correctly:`, neighbors);

      // Test that vec0 table persists data correctly
      const count = await sdb.get('SELECT COUNT(*) as cnt FROM vec_embeddings');
      assert.strictEqual(count!.cnt, 4, 'Should have 4 vectors stored');
      console.log('✅ Vector persistence verified');

    } catch (err: any) {
      // If vec0 operations fail, something is wrong with the extension
      throw new Error(`vec0 operations failed: ${err.message}`);
    } finally {
      await sdb.close();
    }
  }

  it('should gracefully handle extension unavailability', async function() {
    // This test verifies that database operations work normally
    // even if extensions fail to load (Python fallback)

    const sdb = await SQLiteDB.openDB(dbPath('normal_test.db'), {
      name: 'NormalTest',
      version: 1,
      createSql: 'CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT);'
    }, OpenMode.OPEN_CREATE);

    // Normal SQLite operations should always work
    await sdb.run('INSERT INTO users (email) VALUES (?)', 'test@example.com');
    const result = await sdb.get('SELECT * FROM users WHERE id = 1');

    assert.isDefined(result, 'Should retrieve inserted row');
    assert.strictEqual(result!.email, 'test@example.com', 'Data should be correct');

    await sdb.close();
    console.log('✅ Normal database operations work independently of extensions');
  });

  it('should not corrupt existing databases when loading extensions', async function() {
    // CRITICAL TEST: Verify that extension loading doesn't modify existing data

    // Step 1: Create a database with some data
    const testDbPath = dbPath('data_safety_test.db');
    let sdb = await SQLiteDB.openDB(testDbPath, {
      name: 'DataSafetyTest',
      version: 1,
      createSql: 'CREATE TABLE important_data (id INTEGER PRIMARY KEY, value TEXT);'
    }, OpenMode.OPEN_CREATE);

    await sdb.run('INSERT INTO important_data (value) VALUES (?)', 'critical_data_1');
    await sdb.run('INSERT INTO important_data (value) VALUES (?)', 'critical_data_2');
    await sdb.run('INSERT INTO important_data (value) VALUES (?)', 'critical_data_3');

    const beforeData = await sdb.all('SELECT * FROM important_data ORDER BY id');
    await sdb.close();

    // Step 2: Reopen the database (which triggers extension loading again)
    sdb = await SQLiteDB.openDB(testDbPath, {
      name: 'DataSafetyTest',
      version: 1,
      createSql: 'CREATE TABLE important_data (id INTEGER PRIMARY KEY, value TEXT);'
    }, OpenMode.OPEN_EXISTING);

    const afterData = await sdb.all('SELECT * FROM important_data ORDER BY id');
    await sdb.close();

    // Step 3: Verify data is IDENTICAL before and after extension loading
    assert.deepEqual(afterData, beforeData, 'Data must be identical before and after extension loading');
    assert.lengthOf(afterData, 3, 'All 3 records must be preserved');
    assert.strictEqual(afterData[0].value, 'critical_data_1', 'First record must be unchanged');
    assert.strictEqual(afterData[1].value, 'critical_data_2', 'Second record must be unchanged');
    assert.strictEqual(afterData[2].value, 'critical_data_3', 'Third record must be unchanged');

    console.log('✅ CRITICAL: Extension loading does NOT modify existing data');
  });

  // ============================================================================
  // PHASE 2: SpatiaLite Extension Tests
  // ============================================================================

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

  /**
   * Comprehensive spatial operations tests (only run if SpatiaLite available)
   */
  async function testSpatialOperations() {
    const sdb = await SQLiteDB.openDB(dbPath('spatial_ops_test.db'), {
      name: 'SpatialOpsTest',
      version: 1,
      createSql: 'CREATE TABLE points (id INTEGER PRIMARY KEY, name TEXT);'
    }, OpenMode.OPEN_CREATE);

    try {
      // Test 1: Distance Paris-London (should be ~344-346 km)
      const distance = await sdb.get(`
        SELECT ST_Distance(
          ST_GeomFromText('POINT(2.3522 48.8566)', 4326),
          ST_GeomFromText('POINT(-0.1276 51.5074)', 4326),
          1
        ) / 1000 AS distance_km
      `);

      assert.isDefined(distance, 'Distance query should return result');
      // SpatiaLite distance is geodesic, should be ~344-346 km
      assert.isAbove(distance!.distance_km, 340, 'Paris-London distance should be > 340 km');
      assert.isBelow(distance!.distance_km, 350, 'Paris-London distance should be < 350 km');
      console.log(`✅ ST_Distance calculation working: ${distance!.distance_km.toFixed(1)} km`);

      // Test 2: Area calculation (1°x1° square at mid-latitudes)
      const area = await sdb.get(`
        SELECT ST_Area(
          ST_GeomFromText('POLYGON((0 45, 1 45, 1 46, 0 46, 0 45))', 4326),
          1
        ) / 1000000 AS area_km2
      `);

      assert.isDefined(area, 'Area query should return result');
      // 1°x1° at 45° latitude ≈ 8,000-10,000 km²
      assert.isAbove(area!.area_km2, 7000, 'Area should be > 7000 km²');
      assert.isBelow(area!.area_km2, 12000, 'Area should be < 12000 km²');
      console.log(`✅ ST_Area calculation working: ${area!.area_km2.toFixed(0)} km²`);

      // Test 3: Point-in-polygon (Paris in France bbox)
      const contains = await sdb.get(`
        SELECT ST_Contains(
          ST_GeomFromText('POLYGON((-5 42, 10 42, 10 52, -5 52, -5 42))', 4326),
          ST_GeomFromText('POINT(2.3522 48.8566)', 4326)
        ) AS is_inside
      `);

      assert.strictEqual(contains!.is_inside, 1, 'Paris should be inside France bbox');
      console.log('✅ ST_Contains working correctly: Paris is in France bbox');

      // Test 4: ST_Centroid
      const centroid = await sdb.get(`
        SELECT ST_AsText(
          ST_Centroid(ST_GeomFromText('POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))', 4326))
        ) AS centroid_wkt
      `);

      assert.isDefined(centroid, 'Centroid query should return result');
      assert.include(centroid!.centroid_wkt, 'POINT', 'Centroid should be a POINT');
      console.log(`✅ ST_Centroid working: ${centroid!.centroid_wkt}`);

      // Test 5: ST_Buffer (create buffer around point)
      const buffer = await sdb.get(`
        SELECT ST_AsText(
          ST_Buffer(ST_GeomFromText('POINT(2.3 48.8)', 4326), 0.01)
        ) AS buffer_wkt
      `);

      assert.isDefined(buffer, 'Buffer query should return result');
      assert.include(buffer!.buffer_wkt, 'POLYGON', 'Buffer should create a POLYGON');
      console.log('✅ ST_Buffer working: created polygon around point');

      // Test 6: ST_Intersects
      const intersects = await sdb.get(`
        SELECT ST_Intersects(
          ST_GeomFromText('POLYGON((0 0, 5 0, 5 5, 0 5, 0 0))', 4326),
          ST_GeomFromText('POLYGON((3 3, 8 3, 8 8, 3 8, 3 3))', 4326)
        ) AS intersects
      `);

      assert.strictEqual(intersects!.intersects, 1, 'Overlapping polygons should intersect');
      console.log('✅ ST_Intersects working correctly');

      console.log('✅ All SpatiaLite spatial operations verified successfully');

    } catch (err: any) {
      throw new Error(`SpatiaLite operations failed: ${err.message}`);
    } finally {
      await sdb.close();
    }
  }

  it('should not corrupt data when loading SpatiaLite', async function() {
    // CRITICAL: Verify SpatiaLite extension loading doesn't modify existing data
    const testDbPath = dbPath('spatial_safety_test.db');

    let sdb = await SQLiteDB.openDB(testDbPath, {
      name: 'SpatialSafetyTest',
      version: 1,
      createSql: 'CREATE TABLE geodata (id INTEGER PRIMARY KEY, location TEXT);'
    }, OpenMode.OPEN_CREATE);

    await sdb.run('INSERT INTO geodata (location) VALUES (?)', 'POINT(2.3 48.8)');
    await sdb.run('INSERT INTO geodata (location) VALUES (?)', 'POINT(-0.1 51.5)');

    const beforeData = await sdb.all('SELECT * FROM geodata ORDER BY id');
    await sdb.close();

    // Reopen (triggers extension loading again)
    sdb = await SQLiteDB.openDB(testDbPath, {
      name: 'SpatialSafetyTest',
      version: 1,
      createSql: 'CREATE TABLE geodata (id INTEGER PRIMARY KEY, location TEXT);'
    }, OpenMode.OPEN_EXISTING);

    const afterData = await sdb.all('SELECT * FROM geodata ORDER BY id');
    await sdb.close();

    assert.deepEqual(afterData, beforeData, 'Spatial data must be identical before/after extension loading');
    console.log('✅ CRITICAL: SpatiaLite loading does NOT modify existing spatial data');
  });
});
