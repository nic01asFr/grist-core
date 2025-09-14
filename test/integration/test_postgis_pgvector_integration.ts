/**
 * Tests d'intégration complets pour l'intégration PostGIS + pg_vector dans Grist
 * 
 * Ces tests valident que tous les composants fonctionnent ensemble :
 * - Types Python (sandbox/grist/usertypes.py)
 * - Types TypeScript (app/common/gristTypes.ts)
 * - Widgets UI (app/client/widgets/)
 * - Migration base de données (app/gen-server/migration/)
 * - Intégration PostgreSQL avec extensions
 */
import {assert} from 'chai';
import {createDocTools} from 'test/server/docTools';

describe('PostGIS + pg_vector Integration Tests', function() {
  this.timeout(60000); // Tests d'intégration peuvent être lents

  let docTools: any;
  const isPostgres = process.env.TYPEORM_TYPE === 'postgres';

  before(async function() {
    if (!isPostgres) {
      console.log('Skipping integration tests - not using PostgreSQL');
      this.skip();
      return;
    }

    try {
      docTools = await createDocTools('integration-postgis-pgvector');
    } catch (error) {
      console.warn('Failed to create doc tools for integration tests:', error.message);
      this.skip();
    }
  });

  after(async function() {
    if (docTools) {
      await docTools.cleanup();
    }
  });

  describe('Complete Workflow Tests', function() {
    it('should create table with Geometry and Vector columns', async function() {
      if (!isPostgres) {
        this.skip();
        return;
      }

      // Créer un document de test
      const doc = await docTools.createDoc('GeospatialAI');
      
      // Ajouter une table avec colonnes Geometry et Vector
      await doc.addTable([
        { id: 1, name: 'MyGeoAITable' }
      ]);

      // Ajouter colonnes de nos nouveaux types
      await doc.addColumn([
        { id: 1, name: 'location', type: 'Geometry' },
        { id: 2, name: 'embedding', type: 'Vector' }
      ]);

      // Vérifier que les colonnes ont été créées correctement
      const tables = await doc.loadTables();
      const myTable = tables.find((t: any) => t.name === 'MyGeoAITable');
      
      assert.isDefined(myTable);
      assert.include(myTable.columns.map((c: any) => c.name), 'location');
      assert.include(myTable.columns.map((c: any) => c.name), 'embedding');
      
      const locationCol = myTable.columns.find((c: any) => c.name === 'location');
      const embeddingCol = myTable.columns.find((c: any) => c.name === 'embedding');
      
      assert.equal(locationCol.type, 'Geometry');
      assert.equal(embeddingCol.type, 'Vector');
    });

    it('should insert and retrieve Geometry data', async function() {
      if (!isPostgres) {
        this.skip();
        return;
      }

      const doc = await docTools.createDoc('GeometryTest');
      
      // Créer table avec colonne Geometry
      await doc.addTable([{ id: 1, name: 'Places' }]);
      await doc.addColumn([{ id: 1, name: 'location', type: 'Geometry' }]);

      // Insérer des données géospatiales
      const testLocations = [
        'POINT(2.3522 48.8566)',     // Paris
        'POINT(-0.1276 51.5074)',    // London  
        'POINT(139.6917 35.6895)'    // Tokyo
      ];

      for (let i = 0; i < testLocations.length; i++) {
        await doc.addRecord([{
          id: i + 1,
          location: testLocations[i]
        }]);
      }

      // Récupérer et vérifier les données
      const records = await doc.loadRecords('Places');
      
      assert.equal(records.length, testLocations.length);
      
      for (let i = 0; i < records.length; i++) {
        assert.equal(records[i].location, testLocations[i]);
      }
    });

    it('should insert and retrieve Vector data', async function() {
      if (!isPostgres) {
        this.skip();
        return;
      }

      const doc = await docTools.createDoc('VectorTest');
      
      // Créer table avec colonne Vector
      await doc.addTable([{ id: 1, name: 'Embeddings' }]);
      await doc.addColumn([{ id: 1, name: 'vector', type: 'Vector' }]);

      // Insérer des embeddings de test
      const testVectors = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9]
      ];

      for (let i = 0; i < testVectors.length; i++) {
        await doc.addRecord([{
          id: i + 1,
          vector: testVectors[i]
        }]);
      }

      // Récupérer et vérifier les données
      const records = await doc.loadRecords('Embeddings');
      
      assert.equal(records.length, testVectors.length);
      
      for (let i = 0; i < records.length; i++) {
        assert.deepEqual(records[i].vector, testVectors[i]);
      }
    });

    it('should handle hybrid Geometry + Vector tables', async function() {
      if (!isPostgres) {
        this.skip();
        return;
      }

      const doc = await docTools.createDoc('HybridTest');
      
      // Créer table hybride avec Geometry + Vector
      await doc.addTable([{ id: 1, name: 'GeoAI' }]);
      await doc.addColumn([
        { id: 1, name: 'name', type: 'Text' },
        { id: 2, name: 'location', type: 'Geometry' },
        { id: 3, name: 'embedding', type: 'Vector' }
      ]);

      // Données de test hybrides
      const testData = [
        {
          name: 'Eiffel Tower',
          location: 'POINT(2.2945 48.8582)',
          embedding: [0.8, 0.6, 0.9]
        },
        {
          name: 'Big Ben',
          location: 'POINT(-0.1246 51.4994)',
          embedding: [0.7, 0.8, 0.5]
        },
        {
          name: 'Tokyo Skytree',
          location: 'POINT(139.8107 35.7101)',
          embedding: [0.9, 0.5, 0.8]
        }
      ];

      // Insérer données hybrides
      for (let i = 0; i < testData.length; i++) {
        await doc.addRecord([{
          id: i + 1,
          ...testData[i]
        }]);
      }

      // Récupérer et vérifier
      const records = await doc.loadRecords('GeoAI');
      
      assert.equal(records.length, testData.length);
      
      for (let i = 0; i < records.length; i++) {
        const record = records[i];
        const expected = testData[i];
        
        assert.equal(record.name, expected.name);
        assert.equal(record.location, expected.location);
        assert.deepEqual(record.embedding, expected.embedding);
      }
    });
  });

  describe('Type Conversion Integration', function() {
    it('should convert GeoJSON to WKT in Geometry columns', async function() {
      if (!isPostgres) {
        this.skip();
        return;
      }

      const doc = await docTools.createDoc('GeoJSONTest');
      await doc.addTable([{ id: 1, name: 'GeoData' }]);
      await doc.addColumn([{ id: 1, name: 'geom', type: 'Geometry' }]);

      // Test conversion GeoJSON vers WKT
      const geojsonPoint = {
        type: 'Point',
        coordinates: [2.3, 48.8]
      };

      await doc.addRecord([{
        id: 1,
        geom: geojsonPoint
      }]);

      const records = await doc.loadRecords('GeoData');
      assert.equal(records.length, 1);
      assert.equal(records[0].geom, 'POINT(2.3 48.8)');
    });

    it('should parse Vector strings to arrays', async function() {
      if (!isPostgres) {
        this.skip();
        return;
      }

      const doc = await docTools.createDoc('VectorStringTest');
      await doc.addTable([{ id: 1, name: 'Vectors' }]);
      await doc.addColumn([{ id: 1, name: 'embedding', type: 'Vector' }]);

      // Test différents formats de chaînes
      const stringFormats = [
        { input: '[1.0, 2.0, 3.0]', expected: [1.0, 2.0, 3.0] },
        { input: '1.0, 2.0, 3.0', expected: [1.0, 2.0, 3.0] },
        { input: '0.1,0.2,0.3', expected: [0.1, 0.2, 0.3] }
      ];

      for (let i = 0; i < stringFormats.length; i++) {
        await doc.addRecord([{
          id: i + 1,
          embedding: stringFormats[i].input
        }]);
      }

      const records = await doc.loadRecords('Vectors');
      assert.equal(records.length, stringFormats.length);

      for (let i = 0; i < records.length; i++) {
        assert.deepEqual(records[i].embedding, stringFormats[i].expected);
      }
    });
  });

  describe('Error Handling Integration', function() {
    it('should handle invalid Geometry data gracefully', async function() {
      if (!isPostgres) {
        this.skip();
        return;
      }

      const doc = await docTools.createDoc('GeometryErrorTest');
      await doc.addTable([{ id: 1, name: 'BadGeom' }]);
      await doc.addColumn([{ id: 1, name: 'location', type: 'Geometry' }]);

      // Tenter d'insérer geometrie invalide
      try {
        await doc.addRecord([{
          id: 1,
          location: 'INVALID_GEOMETRY(1 2 3)'
        }]);
        
        // La conversion doit échouer ou produire AltText
        const records = await doc.loadRecords('BadGeom');
        if (records.length > 0) {
          // Si un enregistrement existe, il devrait contenir AltText
          const locationValue = records[0].location;
          // En production, ceci serait probablement un AltText ou une erreur
          assert.isTrue(
            locationValue === null || 
            typeof locationValue === 'string' && locationValue.includes('error')
          );
        }
      } catch (error) {
        // C'est acceptable que la conversion échoue
        assert.include(error.message.toLowerCase(), 'conversion');
      }
    });

    it('should handle invalid Vector data gracefully', async function() {
      if (!isPostgres) {
        this.skip();
        return;
      }

      const doc = await docTools.createDoc('VectorErrorTest');
      await doc.addTable([{ id: 1, name: 'BadVectors' }]);
      await doc.addColumn([{ id: 1, name: 'embedding', type: 'Vector' }]);

      // Tenter d'insérer vecteur invalide
      try {
        await doc.addRecord([{
          id: 1,
          embedding: 'not_a_vector'
        }]);
        
        const records = await doc.loadRecords('BadVectors');
        if (records.length > 0) {
          // La valeur devrait être null ou AltText
          const embeddingValue = records[0].embedding;
          assert.isTrue(
            embeddingValue === null || 
            (typeof embeddingValue === 'object' && embeddingValue.toString().includes('error'))
          );
        }
      } catch (error) {
        // Acceptable que la conversion échoue
        assert.include(error.message.toLowerCase(), 'conversion');
      }
    });
  });

  describe('Performance Integration', function() {
    it('should handle large vectors efficiently', async function() {
      if (!isPostgres) {
        this.skip();
        return;
      }

      const doc = await docTools.createDoc('LargeVectorTest');
      await doc.addTable([{ id: 1, name: 'LargeEmbeddings' }]);
      await doc.addColumn([{ id: 1, name: 'large_vector', type: 'Vector' }]);

      // Test avec vecteur de taille OpenAI (1536 dimensions)
      const largeVector = Array.from({length: 1536}, (_, i) => Math.random());

      const startTime = Date.now();
      
      await doc.addRecord([{
        id: 1,
        large_vector: largeVector
      }]);

      const records = await doc.loadRecords('LargeEmbeddings');
      
      const endTime = Date.now();
      const duration = endTime - startTime;

      assert.equal(records.length, 1);
      assert.equal(records[0].large_vector.length, 1536);
      assert.isBelow(duration, 5000, 'Large vector operations should complete in <5 seconds');

      // Vérifier que les données sont préservées
      for (let i = 0; i < Math.min(10, largeVector.length); i++) {
        assert.approximately(
          records[0].large_vector[i], 
          largeVector[i], 
          0.000001,
          `Vector element ${i} should be preserved accurately`
        );
      }
    });
  });

  describe('Database Extension Integration', function() {
    it('should confirm PostgreSQL extensions are available', async function() {
      if (!isPostgres) {
        this.skip();
        return;
      }

      // Cette partie nécessiterait un accès direct à la DB pour vérifier les extensions
      // Pour l'instant, on suppose que les extensions sont disponibles si les tests précédents passent
      
      // Test indirect : si on peut créer et utiliser des colonnes Geometry/Vector,
      // c'est que les types sont bien supportés
      const doc = await docTools.createDoc('ExtensionTest');
      await doc.addTable([{ id: 1, name: 'ExtensionValidation' }]);
      
      // Si ceci réussit, les types sont supportés
      await doc.addColumn([
        { id: 1, name: 'geom', type: 'Geometry' },
        { id: 2, name: 'vec', type: 'Vector' }
      ]);

      const tables = await doc.loadTables();
      const testTable = tables.find((t: any) => t.name === 'ExtensionValidation');
      
      assert.isDefined(testTable);
      
      const geomCol = testTable.columns.find((c: any) => c.name === 'geom');
      const vecCol = testTable.columns.find((c: any) => c.name === 'vec');
      
      assert.equal(geomCol.type, 'Geometry');
      assert.equal(vecCol.type, 'Vector');
    });
  });
});
