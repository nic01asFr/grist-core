/**
 * API native pour les fonctionnalités spatiales et vectorielles intégrées dans Grist
 * Endpoints REST pour l'intégration complète PostGIS + pgvector + Albert API
 */

import * as express from 'express';
import { ApiError } from 'app/common/ApiError';
import { SpatialColumnTypes, Geometry, VectorEmbedding, SimilarityResult } from 'app/common/SpatialTypes';
import { spatialVectorService } from 'app/server/lib/SpatialVectorService';
import * as NativeFunctions from 'app/server/lib/NativeSpatialFunctions';
import { expressWrap } from 'app/server/lib/expressWrap';
import { DocManager } from 'app/server/lib/DocManager';
import { IDocWorkerMap } from 'app/server/lib/DocWorkerMap';
import { log } from 'app/server/lib/log';
import { GristServer } from 'app/server/lib/GristServer';

export function addNativeSpatialEndpoints(
  app: express.Application, 
  server: GristServer,
  docWorkerMap: IDocWorkerMap
): void {

  // ============================================================================
  // ENDPOINTS POUR LES FONCTIONS VECTORIELLES
  // ============================================================================

  /**
   * POST /api/docs/:docId/spatial/embedding
   * Génère un embedding pour un texte donné
   */
  app.post('/api/docs/:docId/spatial/embedding', 
    expressWrap(async (req: express.Request, res: express.Response) => {
      const { text } = req.body;
      
      if (!text || typeof text !== 'string') {
        throw new ApiError('Le paramètre "text" est requis et doit être une chaîne', 400);
      }
      
      try {
        const embedding = await NativeFunctions.GENERATE_EMBEDDING(text);
        
        res.json({
          success: true,
          data: {
            text: text,
            embedding: embedding,
            dimensions: embedding.length,
            model: process.env.ALBERT_MODEL_EMBEDDING || 'embeddings-small',
            timestamp: new Date().toISOString()
          }
        });
      } catch (error) {
        log.error('Erreur génération embedding:', error);
        throw new ApiError(`Erreur génération embedding: ${error.message}`, 500);
      }
    })
  );

  /**
   * POST /api/docs/:docId/spatial/similarity/search
   * Recherche de similarité vectorielle
   */
  app.post('/api/docs/:docId/spatial/similarity/search',
    expressWrap(async (req: express.Request, res: express.Response) => {
      const { queryText, threshold = 0.7, limit = 10 } = req.body;
      
      if (!queryText || typeof queryText !== 'string') {
        throw new ApiError('Le paramètre "queryText" est requis', 400);
      }
      
      try {
        const results = await NativeFunctions.SEARCH_SIMILAR(queryText, threshold, limit);
        
        res.json({
          success: true,
          data: {
            query: queryText,
            threshold: threshold,
            results: results,
            count: results.length,
            timestamp: new Date().toISOString()
          }
        });
      } catch (error) {
        log.error('Erreur recherche similarité:', error);
        throw new ApiError(`Erreur recherche similarité: ${error.message}`, 500);
      }
    })
  );

  /**
   * POST /api/docs/:docId/spatial/similarity/compare
   * Compare la similarité entre deux textes
   */
  app.post('/api/docs/:docId/spatial/similarity/compare',
    expressWrap(async (req: express.Request, res: express.Response) => {
      const { text1, text2 } = req.body;
      
      if (!text1 || !text2 || typeof text1 !== 'string' || typeof text2 !== 'string') {
        throw new ApiError('Les paramètres "text1" et "text2" sont requis', 400);
      }
      
      try {
        const similarity = await NativeFunctions.TEXT_SIMILARITY(text1, text2);
        
        res.json({
          success: true,
          data: {
            text1: text1,
            text2: text2,
            similarity: similarity,
            interpretation: getSimilarityInterpretation(similarity),
            timestamp: new Date().toISOString()
          }
        });
      } catch (error) {
        log.error('Erreur comparaison similarité:', error);
        throw new ApiError(`Erreur comparaison similarité: ${error.message}`, 500);
      }
    })
  );

  // ============================================================================
  // ENDPOINTS POUR LES FONCTIONS SPATIALES
  // ============================================================================

  /**
   * POST /api/docs/:docId/spatial/geometry/distance
   * Calcule la distance entre deux points géographiques
   */
  app.post('/api/docs/:docId/spatial/geometry/distance',
    expressWrap(async (req: express.Request, res: express.Response) => {
      const { point1, point2, unit = 'meters' } = req.body;
      
      if (!point1 || !point2) {
        throw new ApiError('Les paramètres "point1" et "point2" sont requis', 400);
      }
      
      try {
        const distanceMeters = await NativeFunctions.GEO_DISTANCE(point1, point2);
        
        res.json({
          success: true,
          data: {
            point1: point1,
            point2: point2,
            distance: {
              meters: distanceMeters,
              kilometers: distanceMeters / 1000,
              miles: distanceMeters / 1609.344,
              nauticalMiles: distanceMeters / 1852
            },
            timestamp: new Date().toISOString()
          }
        });
      } catch (error) {
        log.error('Erreur calcul distance:', error);
        throw new ApiError(`Erreur calcul distance: ${error.message}`, 500);
      }
    })
  );

  /**
   * POST /api/docs/:docId/spatial/geometry/area
   * Calcule l'aire d'un polygone
   */
  app.post('/api/docs/:docId/spatial/geometry/area',
    expressWrap(async (req: express.Request, res: express.Response) => {
      const { polygon } = req.body;
      
      if (!polygon || polygon.type !== 'Polygon') {
        throw new ApiError('Le paramètre "polygon" doit être un objet Polygon valide', 400);
      }
      
      try {
        const areaM2 = NativeFunctions.GEO_AREA(polygon);
        
        res.json({
          success: true,
          data: {
            polygon: polygon,
            area: {
              squareMeters: areaM2,
              squareKilometers: areaM2 / 1000000,
              hectares: areaM2 / 10000,
              acres: areaM2 / 4046.856
            },
            timestamp: new Date().toISOString()
          }
        });
      } catch (error) {
        log.error('Erreur calcul aire:', error);
        throw new ApiError(`Erreur calcul aire: ${error.message}`, 500);
      }
    })
  );

  /**
   * POST /api/docs/:docId/spatial/geometry/contains
   * Vérifie si un point est dans un polygone
   */
  app.post('/api/docs/:docId/spatial/geometry/contains',
    expressWrap(async (req: express.Request, res: express.Response) => {
      const { polygon, point } = req.body;
      
      if (!polygon || !point) {
        throw new ApiError('Les paramètres "polygon" et "point" sont requis', 400);
      }
      
      try {
        const contains = NativeFunctions.GEO_CONTAINS(polygon, point);
        
        res.json({
          success: true,
          data: {
            polygon: polygon,
            point: point,
            contains: contains,
            timestamp: new Date().toISOString()
          }
        });
      } catch (error) {
        log.error('Erreur test containment:', error);
        throw new ApiError(`Erreur test containment: ${error.message}`, 500);
      }
    })
  );

  /**
   * POST /api/docs/:docId/spatial/geometry/nearby
   * Recherche de proximité géographique
   */
  app.post('/api/docs/:docId/spatial/geometry/nearby',
    expressWrap(async (req: express.Request, res: express.Response) => {
      const { center, radius, limit = 10 } = req.body;
      
      if (!center || typeof radius !== 'number') {
        throw new ApiError('Les paramètres "center" et "radius" sont requis', 400);
      }
      
      try {
        const results = await NativeFunctions.GEO_SEARCH_NEARBY(center, radius, limit);
        
        res.json({
          success: true,
          data: {
            center: center,
            radius: radius,
            results: results,
            count: results.length,
            timestamp: new Date().toISOString()
          }
        });
      } catch (error) {
        log.error('Erreur recherche proximité:', error);
        throw new ApiError(`Erreur recherche proximité: ${error.message}`, 500);
      }
    })
  );

  // ============================================================================
  // ENDPOINTS HYBRIDES
  // ============================================================================

  /**
   * POST /api/docs/:docId/spatial/hybrid/search
   * Recherche hybride spatiale + vectorielle
   */
  app.post('/api/docs/:docId/spatial/hybrid/search',
    expressWrap(async (req: express.Request, res: express.Response) => {
      const { 
        queryText, 
        center, 
        radius, 
        textThreshold = 0.7, 
        limit = 10 
      } = req.body;
      
      if (!queryText || !center || typeof radius !== 'number') {
        throw new ApiError('Les paramètres "queryText", "center" et "radius" sont requis', 400);
      }
      
      try {
        const results = await NativeFunctions.HYBRID_SEARCH(
          queryText, 
          center, 
          radius, 
          textThreshold, 
          limit
        );
        
        res.json({
          success: true,
          data: {
            query: {
              text: queryText,
              center: center,
              radius: radius,
              textThreshold: textThreshold
            },
            results: results,
            count: results.length,
            timestamp: new Date().toISOString()
          }
        });
      } catch (error) {
        log.error('Erreur recherche hybride:', error);
        throw new ApiError(`Erreur recherche hybride: ${error.message}`, 500);
      }
    })
  );

  // ============================================================================
  // ENDPOINTS DE GESTION ET STATISTIQUES
  // ============================================================================

  /**
   * GET /api/docs/:docId/spatial/stats
   * Statistiques du service spatial/vectoriel
   */
  app.get('/api/docs/:docId/spatial/stats',
    expressWrap(async (req: express.Request, res: express.Response) => {
      try {
        const stats = await NativeFunctions.SPATIAL_STATS();
        
        res.json({
          success: true,
          data: {
            ...stats,
            capabilities: {
              spatial: true,
              vector: true,
              albert_api: process.env.ALBERT_API_TOKEN !== 'test-token',
              postgis: true,
              pgvector: true
            },
            configuration: {
              albert_api_url: process.env.ALBERT_API_URL,
              albert_model: process.env.ALBERT_MODEL_EMBEDDING,
              embedding_dimensions: process.env.EMBEDDING_DIMENSION,
              database_type: 'PostgreSQL + PostGIS + pgvector'
            }
          }
        });
      } catch (error) {
        log.error('Erreur récupération statistiques:', error);
        throw new ApiError(`Erreur récupération statistiques: ${error.message}`, 500);
      }
    })
  );

  /**
   * GET /api/docs/:docId/spatial/health
   * Check de santé du service spatial/vectoriel
   */
  app.get('/api/docs/:docId/spatial/health',
    expressWrap(async (req: express.Request, res: express.Response) => {
      try {
        // Test simple des capacités
        const testPoint = NativeFunctions.GEO_POINT(2.3522, 48.8566);
        const testEmbedding = await NativeFunctions.GENERATE_EMBEDDING('test');
        
        res.json({
          success: true,
          data: {
            status: 'healthy',
            services: {
              spatial_functions: 'operational',
              vector_functions: 'operational',
              albert_api: testEmbedding.length > 0 ? 'operational' : 'degraded',
              database: 'connected'
            },
            timestamp: new Date().toISOString(),
            test_results: {
              point_creation: !!testPoint,
              embedding_generation: testEmbedding.length > 0,
              embedding_dimensions: testEmbedding.length
            }
          }
        });
      } catch (error) {
        log.error('Erreur health check:', error);
        res.status(503).json({
          success: false,
          error: 'Service spatial/vectoriel indisponible',
          details: error.message,
          timestamp: new Date().toISOString()
        });
      }
    })
  );

  // ============================================================================
  // ENDPOINTS UTILITAIRES
  // ============================================================================

  /**
   * POST /api/docs/:docId/spatial/convert/coordinates
   * Conversion de coordonnées
   */
  app.post('/api/docs/:docId/spatial/convert/coordinates',
    expressWrap(async (req: express.Request, res: express.Response) => {
      const { coordinate, format } = req.body;
      
      if (typeof coordinate !== 'number' || !format) {
        throw new ApiError('Les paramètres "coordinate" (number) et "format" sont requis', 400);
      }
      
      try {
        const result = NativeFunctions.GEO_CONVERT_COORDS(coordinate, format);
        
        res.json({
          success: true,
          data: {
            input: coordinate,
            format: format,
            result: result,
            timestamp: new Date().toISOString()
          }
        });
      } catch (error) {
        log.error('Erreur conversion coordonnées:', error);
        throw new ApiError(`Erreur conversion coordonnées: ${error.message}`, 500);
      }
    })
  );

  /**
   * GET /api/docs/:docId/spatial/capabilities
   * Liste des capacités et fonctions disponibles
   */
  app.get('/api/docs/:docId/spatial/capabilities',
    expressWrap(async (req: express.Request, res: express.Response) => {
      res.json({
        success: true,
        data: {
          version: '1.0.0',
          features: {
            vector_functions: [
              'GENERATE_EMBEDDING',
              'SEARCH_SIMILAR', 
              'TEXT_SIMILARITY'
            ],
            spatial_functions: [
              'GEO_POINT',
              'GEO_DISTANCE',
              'GEO_POLYGON',
              'GEO_AREA',
              'GEO_CONTAINS',
              'GEO_SEARCH_NEARBY',
              'GEO_CONVERT_COORDS'
            ],
            hybrid_functions: [
              'HYBRID_SEARCH'
            ],
            utility_functions: [
              'SPATIAL_STATS'
            ]
          },
          column_types: Object.values(SpatialColumnTypes),
          supported_formats: {
            input: ['GeoJSON', 'WKT', 'coordinates', 'DMS'],
            output: ['GeoJSON', 'WKT', 'formatted']
          },
          integrations: {
            postgis: true,
            pgvector: true,
            albert_api: true
          },
          timestamp: new Date().toISOString()
        }
      });
    })
  );

  log.info('🎯 Endpoints Spatial/Vector natifs ajoutés à Grist');
}

// ============================================================================
// FONCTIONS UTILITAIRES
// ============================================================================

function getSimilarityInterpretation(similarity: number): string {
  if (similarity >= 0.9) return 'Très similaire';
  if (similarity >= 0.8) return 'Similaire';
  if (similarity >= 0.7) return 'Assez similaire';
  if (similarity >= 0.6) return 'Peu similaire';
  if (similarity >= 0.5) return 'Faiblement similaire';
  return 'Très différent';
}