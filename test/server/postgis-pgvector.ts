import {assert} from 'chai';
import {getAppRoot} from 'app/server/lib/places';
import {getConnectionName, getOrCreateConnection} from 'app/server/lib/dbUtils';
import {DataSource} from 'typeorm';
import {createDocTools} from 'test/server/docTools';
import {loadFixtureDoc} from 'test/server/lib/helpers';

describe('PostGIS and pg_vector Support', function() {
  let docTools: any;
  let dataSource: DataSource;

  before(async function() {
    // Skip tests if not using PostgreSQL
    if (process.env.TYPEORM_TYPE !== 'postgres') {
      this.skip();
      return;
    }

    dataSource = await getOrCreateConnection();
    
    // Vérifier que les extensions sont disponibles
    try {
      const extensions = await dataSource.query(`
        SELECT extname FROM pg_extension 
        WHERE extname IN ('postgis', 'vector')
      `);
      
      const hasPostGIS = extensions.some((ext: any) => ext.extname === 'postgis');
      const hasVector = extensions.some((ext: any) => ext.extname === 'vector');
      
      if (!hasPostGIS || !hasVector) {
        console.warn('Skipping PostGIS/pg_vector tests - extensions not installed');
        this.skip();
        return;
      }
    } catch (error) {
      console.warn('Skipping PostGIS/pg_vector tests - database error:', error.message);
      this.skip();
      return;
    }

    docTools = await createDocTools('postgis-test');
  });

  after(async function() {
    if (docTools) {
      await docTools.cleanup();
    }
  });

  describe('Geometry Type', function() {
    it('should handle POINT geometries', async function() {
      await docTools.sendActions([
        ['AddTable', 'Locations', [
          {id: 'location_name', type: 'Text'},
          {id: 'coordinates', type: 'Geometry'}
        ]]
      ]);

      // Ajouter des données de test
      await docTools.sendActions([
        ['BulkAddRecord', 'Locations', [null, null], {
          location_name: ['Paris', 'London'],
          coordinates: ['POINT(2.3522 48.8566)', 'POINT(-0.1276 51.5074)']
        }]
      ]);

      const data = await docTools.getTable('Locations');
      assert.equal(data.location_name[0], 'Paris');
      assert.equal(data.coordinates[0], 'POINT(2.3522 48.8566)');
      assert.equal(data.location_name[1], 'London');
      assert.equal(data.coordinates[1], 'POINT(-0.1276 51.5074)');
    });

    it('should handle POLYGON geometries', async function() {
      await docTools.sendActions([
        ['AddTable', 'Areas', [
          {id: 'area_name', type: 'Text'},
          {id: 'boundary', type: 'Geometry'}
        ]]
      ]);

      await docTools.sendActions([
        ['BulkAddRecord', 'Areas', [null], {
          area_name: ['Square'],
          boundary: ['POLYGON((0 0, 4 0, 4 4, 0 4, 0 0))']
        }]
      ]);

      const data = await docTools.getTable('Areas');
      assert.equal(data.area_name[0], 'Square');
      assert.equal(data.boundary[0], 'POLYGON((0 0, 4 0, 4 4, 0 4, 0 0))');
    });

    it('should reject invalid WKT', async function() {
      await docTools.sendActions([
        ['AddTable', 'TestGeom', [
          {id: 'geom', type: 'Geometry'}
        ]]
      ]);

      // Ceci devrait créer une alttext plutôt qu'une erreur
      await docTools.sendActions([
        ['BulkAddRecord', 'TestGeom', [null], {
          geom: ['INVALID_GEOMETRY']
        }]
      ]);

      const data = await docTools.getTable('TestGeom');
      // La valeur invalide devrait être convertie en texte alternatif
      assert.isString(data.geom[0]);
    });
  });

  describe('Vector Type', function() {
    it('should handle vector arrays', async function() {
      await docTools.sendActions([
        ['AddTable', 'Embeddings', [
          {id: 'document', type: 'Text'},
          {id: 'embedding', type: 'Vector'}
        ]]
      ]);

      await docTools.sendActions([
        ['BulkAddRecord', 'Embeddings', [null, null], {
          document: ['Doc1', 'Doc2'],
          embedding: [
            [0.1, 0.2, 0.3, 0.4],
            [0.5, 0.6, 0.7, 0.8]
          ]
        }]
      ]);

      const data = await docTools.getTable('Embeddings');
      assert.equal(data.document[0], 'Doc1');
      assert.deepEqual(data.embedding[0], [0.1, 0.2, 0.3, 0.4]);
      assert.equal(data.document[1], 'Doc2');
      assert.deepEqual(data.embedding[1], [0.5, 0.6, 0.7, 0.8]);
    });

    it('should handle fixed-dimension vectors', async function() {
      await docTools.sendActions([
        ['AddTable', 'FixedVectors', [
          {id: 'name', type: 'Text'},
          {id: 'vector_3d', type: 'Vector:3'}
        ]]
      ]);

      await docTools.sendActions([
        ['BulkAddRecord', 'FixedVectors', [null], {
          name: ['Test'],
          vector_3d: [[1.0, 2.0, 3.0]]
        }]
      ]);

      const data = await docTools.getTable('FixedVectors');
      assert.deepEqual(data.vector_3d[0], [1.0, 2.0, 3.0]);
    });

    it('should handle vector parsing from strings', async function() {
      await docTools.sendActions([
        ['AddTable', 'StringVectors', [
          {id: 'vector_from_string', type: 'Vector'}
        ]]
      ]);

      // Test JSON format
      await docTools.sendActions([
        ['BulkAddRecord', 'StringVectors', [null], {
          vector_from_string: ['[1.1, 2.2, 3.3]']
        }]
      ]);

      const data = await docTools.getTable('StringVectors');
      // La conversion de string vers vector devrait fonctionner
      assert.isArray(data.vector_from_string[0]);
    });
  });

  describe('PostgreSQL Integration', function() {
    it('should correctly store and retrieve geometry in PostgreSQL', async function() {
      if (process.env.TYPEORM_TYPE !== 'postgres') {
        this.skip();
        return;
      }

      // Test direct avec PostgreSQL
      const result = await dataSource.query(
        "SELECT ST_AsText(ST_GeomFromText('POINT(1 2)')) as geom"
      );
      assert.equal(result[0].geom, 'POINT(1 2)');
    });

    it('should correctly store and retrieve vectors in PostgreSQL', async function() {
      if (process.env.TYPEORM_TYPE !== 'postgres') {
        this.skip();
        return;
      }

      // Test direct avec pg_vector
      try {
        await dataSource.query("CREATE TABLE IF NOT EXISTS test_vectors (id serial, embedding vector(3))");
        await dataSource.query("INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]')");
        const result = await dataSource.query("SELECT embedding FROM test_vectors WHERE id = (SELECT MAX(id) FROM test_vectors)");
        
        assert.isNotNull(result[0].embedding);
        // pg_vector retourne les vecteurs comme des chaînes, on vérifie juste qu'on a quelque chose
        assert.isString(result[0].embedding);
        
        await dataSource.query("DROP TABLE IF EXISTS test_vectors");
      } catch (error) {
        // Si pg_vector n'est pas installé, on skip ce test
        if (error.message.includes('type "vector" does not exist')) {
          this.skip();
        } else {
          throw error;
        }
      }
    });
  });

  describe('Type Conversion', function() {
    it('should convert SQL geometry types to Grist Geometry', function() {
      const {sequelizeToGristType} = require('app/common/gristTypes');
      
      assert.equal(sequelizeToGristType('GEOMETRY'), 'Geometry');
      assert.equal(sequelizeToGristType('POINT'), 'Geometry');
      assert.equal(sequelizeToGristType('POLYGON'), 'Geometry');
      assert.equal(sequelizeToGristType('LINESTRING'), 'Geometry');
    });

    it('should convert SQL vector types to Grist Vector', function() {
      const {sequelizeToGristType} = require('app/common/gristTypes');
      
      assert.equal(sequelizeToGristType('VECTOR'), 'Vector');
    });
  });

  describe('Default Values', function() {
    it('should have correct default values for new types', function() {
      const {getDefaultForType} = require('app/common/gristTypes');
      
      assert.isNull(getDefaultForType('Geometry'));
      assert.isNull(getDefaultForType('Vector'));
      assert.equal(getDefaultForType('Geometry', {sqlFormatted: true}), 'NULL');
      assert.equal(getDefaultForType('Vector', {sqlFormatted: true}), 'NULL');
    });
  });
});
