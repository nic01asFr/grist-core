// API REST spatiale et vectorielle pour Grist - Version JavaScript
const { SpatialVectorService } = require('./SpatialVectorService');

// Instance globale du service
const spatialService = new SpatialVectorService();

// Routes API spatiales
function setupSpatialRoutes(app) {
  
  // POST /api/docs/:docId/spatial/embedding - Générer embedding
  app.post('/api/docs/:docId/spatial/embedding', async (req, res) => {
    try {
      const { text } = req.body;
      if (!text) {
        return res.status(400).json({ error: 'Paramètre text requis' });
      }

      const embedding = await spatialService.generateEmbedding(text);
      res.json({
        success: true,
        embedding: embedding,
        dimensions: embedding.length,
        model: spatialService.simulationMode ? 'simulation' : 'multilingual-e5-large'
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // POST /api/docs/:docId/spatial/similarity/search - Recherche vectorielle
  app.post('/api/docs/:docId/spatial/similarity/search', async (req, res) => {
    try {
      const { query, data, limit = 5 } = req.body;
      if (!query || !data) {
        return res.status(400).json({ error: 'Paramètres query et data requis' });
      }

      let queryVector;
      if (typeof query === 'string') {
        queryVector = await spatialService.generateEmbedding(query);
      } else {
        queryVector = query;
      }

      const results = spatialService.searchSimilar(queryVector, data, limit);
      res.json({
        success: true,
        results: results,
        query: query,
        count: results.length
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // POST /api/docs/:docId/spatial/distance - Distance géographique
  app.post('/api/docs/:docId/spatial/distance', async (req, res) => {
    try {
      const { point1, point2 } = req.body;
      if (!point1 || !point2) {
        return res.status(400).json({ error: 'Paramètres point1 et point2 requis' });
      }

      const geom1 = spatialService.parseWKT(point1);
      const geom2 = spatialService.parseWKT(point2);
      
      if (geom1.type !== 'Point' || geom2.type !== 'Point') {
        return res.status(400).json({ error: 'Seuls les points sont supportés' });
      }

      const distance = spatialService.calculateGeoDistance(
        geom1.coordinates[1], geom1.coordinates[0],
        geom2.coordinates[1], geom2.coordinates[0]
      );

      res.json({
        success: true,
        distance: distance,
        unit: 'meters',
        point1: geom1,
        point2: geom2
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // POST /api/docs/:docId/spatial/area - Calcul d'aire
  app.post('/api/docs/:docId/spatial/area', async (req, res) => {
    try {
      const { geometry } = req.body;
      if (!geometry) {
        return res.status(400).json({ error: 'Paramètre geometry requis' });
      }

      const geom = spatialService.parseWKT(geometry);
      const area = spatialService.calculateGeoArea(geom);

      res.json({
        success: true,
        area: area,
        unit: 'square_meters',
        geometry: geom
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // POST /api/docs/:docId/spatial/contains - Test de containment
  app.post('/api/docs/:docId/spatial/contains', async (req, res) => {
    try {
      const { geometry1, geometry2 } = req.body;
      if (!geometry1 || !geometry2) {
        return res.status(400).json({ error: 'Paramètres geometry1 et geometry2 requis' });
      }

      const geom1 = spatialService.parseWKT(geometry1);
      const geom2 = spatialService.parseWKT(geometry2);
      const contains = spatialService.checkGeoContains(geom1, geom2);

      res.json({
        success: true,
        contains: contains,
        geometry1: geom1,
        geometry2: geom2
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // POST /api/docs/:docId/spatial/hybrid/search - Recherche hybride
  app.post('/api/docs/:docId/spatial/hybrid/search', async (req, res) => {
    try {
      const { query, data, geoFilter = null, radius = null, limit = 5 } = req.body;
      if (!query || !data) {
        return res.status(400).json({ error: 'Paramètres query et data requis' });
      }

      // Génération embedding pour la recherche
      const queryEmbedding = await spatialService.generateEmbedding(query);
      
      // Recherche vectorielle
      let results = spatialService.searchSimilar(queryEmbedding, data, limit * 2);
      
      // Filtrage spatial si spécifié
      if (geoFilter && radius) {
        const geoPoint = spatialService.parseWKT(geoFilter);
        results = results.filter(result => {
          // Implémentation du filtrage spatial
          // Pour l'instant, retourne tous les résultats
          return true;
        }).slice(0, limit);
      } else {
        results = results.slice(0, limit);
      }

      res.json({
        success: true,
        results: results,
        query: query,
        geoFilter: geoFilter,
        count: results.length
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });

  // GET /api/docs/:docId/spatial/config - Configuration spatiale
  app.get('/api/docs/:docId/spatial/config', (req, res) => {
    res.json({
      success: true,
      spatialEnabled: process.env.GRIST_SPATIAL_ENABLED === 'true',
      vectorEnabled: process.env.GRIST_VECTOR_ENABLED === 'true',
      albertApiConfigured: !!spatialService.albertApiToken,
      simulationMode: spatialService.simulationMode,
      albertApiUrl: spatialService.albertApiUrl
    });
  });

  // POST /api/docs/:docId/spatial/test - Test des fonctionnalités
  app.post('/api/docs/:docId/spatial/test', async (req, res) => {
    try {
      const results = {
        embedding: await spatialService.generateEmbedding('Test embedding'),
        distance: spatialService.calculateGeoDistance(48.8566, 2.3522, 48.8534, 2.3488),
        similarity: spatialService.calculateCosineSimilarity([1, 0, 0], [0.5, 0.5, 0]),
        wktParsing: spatialService.parseWKT('POINT(2.3522 48.8566)')
      };

      res.json({
        success: true,
        tests: results,
        serviceStatus: 'operational'
      });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  });
}

module.exports = { setupSpatialRoutes };