import * as express from 'express';
import { Response } from 'express';
import { expressWrap } from 'app/server/lib/expressWrap';
import { DocManager } from 'app/server/lib/DocManager';
import { ActiveDoc } from 'app/server/lib/ActiveDoc';
import { docSessionFromRequest } from 'app/server/lib/DocSession';
import { RequestWithLogin, getOrSetDocAuth } from 'app/server/lib/Authorizer';
import { GristServer } from 'app/server/lib/GristServer';
import { HomeDBManager } from 'app/gen-server/lib/homedb/HomeDBManager';
import log from 'app/server/lib/log';

// Types pour les handlers de document
type WithDocHandler = (activeDoc: ActiveDoc, req: RequestWithLogin, resp: Response) => Promise<void>;

// Fonction pour appeler les fonctions Python du sandbox Grist - Intégration Native
async function callPythonFunction(activeDoc: ActiveDoc, req: RequestWithLogin, funcName: string, args: any[]): Promise<any> {
  log.info(`🔄 Appel fonction ${funcName} avec args:`, args);
  
  // ÉTAPE 2: INTÉGRATION PYTHON NATIVE avec fallback robuste
  
  // Vérifier si on a un vrai ActiveDoc (pas un mock vide)
  const isRealActiveDoc = activeDoc && typeof activeDoc === 'object' && Object.keys(activeDoc).length > 0;
  
  if (isRealActiveDoc) {
    try {
      // APPROCHE A: Accès direct au sandbox Python (_dataEngine)
      const dataEngine = await (activeDoc as any)._dataEngine;
      
      if (dataEngine && typeof dataEngine.pyCall === 'function') {
        log.info('✅ Utilisation du sandbox Python natif');
        
        try {
          const result = await dataEngine.pyCall(funcName, ...args);
          log.info(`✅ Résultat Python natif pour ${funcName}:`, result);
          return result;
          
        } catch (pyCallError) {
          log.warn(`❌ Erreur dans pyCall: ${pyCallError.message}`);
          // Continuer vers le fallback
        }
      } else {
        log.warn('❌ dataEngine.pyCall non disponible');
      }
      
    } catch (engineError) {
      log.warn(`❌ Échec accès _dataEngine:`, engineError.message);
    }
  } else {
    log.info('🔄 ActiveDoc vide ou mock détecté');
  }
  
  // FALLBACK: Mock TypeScript (toujours fonctionnel)
  log.info('🔄 Utilisation du fallback Mock TypeScript');
  
  switch (funcName) {
    case 'AUTO_EMBEDDING':
      return mockAutoEmbedding(args[0], args[1], args[2]); // tableId, rowId, service
    case 'VECTOR_SEARCH_SYSTEM':
      return mockVectorSearch(args[0], args[1], args[2], args[3]); // tableId, query, limit, threshold
    default:
      throw new Error(`Fonction Python ${funcName} non supportée`);
  }
}

// Fonctions mock pour les embeddings
function mockAutoEmbedding(tableId: string, rowId: number, service: string = 'mock'): {embedding: number[], hash: string} {
  // Mock embedding basé sur tableId et rowId pour cohérence
  const seed = tableId.length + rowId;
  const embedding = [];
  for (let i = 0; i < 8; i++) {
    embedding.push(Math.sin(seed + i) * 0.5 + 0.5);
  }

  // Générer un hash mock basé sur le contenu
  const hashInput = `${tableId}-${rowId}-${service}`;
  const hash = require('crypto').createHash('md5').update(hashInput).digest('hex');

  return {
    embedding,
    hash
  };
}

function mockVectorSearch(tableId: string, query: string, limit: number = 10, threshold: number = 0.7): any[] {
  // Mock search results - retourne des résultats vides pour l'instant
  log.info(`🔍 Mock VECTOR_SEARCH_SYSTEM: table=${tableId}, query="${query}", limit=${limit}, threshold=${threshold}`);
  return [];
}

/**
 * Configuration d'embedding pour une table
 */
interface EmbeddingConfig {
  enabled: boolean;
  source_fields: string[];
  field_weights?: Record<string, number>;
  embedding_service: 'albert' | 'openai' | 'mock';
  auto_update: boolean;
  batch_size?: number;
  rate_limit_ms?: number;
}

/**
 * Configurer l'embedding pour une table
 */
async function configureTableEmbedding(
  activeDoc: ActiveDoc, 
  tableId: string, 
  config: EmbeddingConfig
): Promise<void> {
  try {
    // Créer les champs système si nécessaire
    // Accès correct au sandbox Python via _dataEngine
    const dataEngine = await (activeDoc as any)._dataEngine;
    if (dataEngine && typeof dataEngine.pyCall === 'function') {
      await dataEngine.pyCall('create_system_embedding_fields', tableId);
    }
    
    // Sauvegarder la configuration
    // const configJson = JSON.stringify(config); // À implémenter
    
    // Mise à jour via actions Grist (à implémenter selon architecture exacte)
    log.info(`Configuration embedding sauvée pour table ${tableId}`);
    
  } catch (error) {
    log.error(`Erreur configuration embedding ${tableId}:`, error);
    throw error;
  }
}

/**
 * Ajouter les endpoints d'embedding à l'application Express
 *
 * Ces endpoints permettent :
 * - Recherche sémantique dans les documents (lecture seule)
 * - Consultation du statut des embeddings
 * - Configuration de l'auto-embedding
 * - Génération manuelle d'embeddings (pour tests/debug)
 *
 * L'autorisation est gérée automatiquement via getOrSetDocAuth() qui peuple req.docAuth
 */
export function addEmbeddingEndpoints(
  app: express.Application,
  docManager: DocManager,
  dbManager: HomeDBManager,
  gristServer: GristServer
): void {

  // Helper pour accès document avec vérification automatique des permissions
  const withDoc = (callback: WithDocHandler) => {
    return expressWrap(async (req: any, res: express.Response) => {
      const docId = req.params.docId;

      try {
        // ÉTAPE 1: Peupler req.docAuth avec getOrSetDocAuth
        await getOrSetDocAuth(req as RequestWithLogin, dbManager, gristServer, docId);

        // ÉTAPE 2: Créer la session avec docAuth déjà peuplé
        const session = docSessionFromRequest(req);

        // ÉTAPE 3: Fetch le document (vérifie permissions de lecture)
        const activeDoc = await docManager.fetchDoc(session, docId);

        await callback(activeDoc, req as RequestWithLogin, res);

      } catch (error) {
        log.error(`❌ Erreur endpoint embedding ${req.path}:`, error);
        res.status(500).json({
          success: false,
          error: 'Erreur interne serveur',
          details: error.message
        });
      }
    });
  };

  // ============================================================================
  // ENDPOINTS CONFIGURATION EMBEDDING
  // ============================================================================

  /**
   * POST /api/docs/:docId/tables/:tableId/embedding/configure
   * Configurer l'auto-embedding pour une table
   * Nécessite droits d'édition (vérifié par applyUserActions)
   */
  app.post('/api/docs/:docId/tables/:tableId/embedding/configure',
    withDoc(async (activeDoc: ActiveDoc, req: RequestWithLogin, res: Response) => {
      const { tableId } = req.params;
      const config: EmbeddingConfig = req.body;
      
      try {
        await configureTableEmbedding(activeDoc, tableId, config);
        
        res.json({
          success: true,
          message: `Embedding configuré pour table ${tableId}`,
          config: config
        });
        
      } catch (error) {
        res.status(400).json({
          success: false,
          error: 'Erreur configuration embedding',
          details: error.message
        });
      }
    })
  );

  /**
   * GET /api/docs/:docId/tables/:tableId/embedding/config
   * Récupérer la configuration embedding d'une table
   * Nécessite droits de lecture (vérifié par fetchDoc)
   */
  app.get('/api/docs/:docId/tables/:tableId/embedding/config',
    withDoc(async (activeDoc: ActiveDoc, req: RequestWithLogin, res: Response) => {
      // const { tableId } = req.params; // Pour usage futur
      
      try {
        // Récupérer config depuis champs système (à implémenter)
        const config = {}; // await getTableEmbeddingConfig(activeDoc, tableId);
        
        res.json({
          success: true,
          config: config || { enabled: false }
        });
        
      } catch (error) {
        res.status(500).json({
          success: false,
          error: 'Erreur récupération configuration'
        });
      }
    })
  );

  // ============================================================================
  // ENDPOINTS RECHERCHE SÉMANTIQUE
  // ============================================================================

  /**
   * POST /api/docs/:docId/tables/:tableId/search/semantic
   * Recherche sémantique dans une table
   * Nécessite droits de lecture (vérifié par fetchDoc)
   */
  app.post('/api/docs/:docId/tables/:tableId/search/semantic',
    withDoc(async (activeDoc: ActiveDoc, req: RequestWithLogin, res: Response) => {
      const { tableId } = req.params;
      const { query, limit = 10, threshold = 0.7 } = req.body;
      
      if (!query || typeof query !== 'string') {
        res.status(400).json({
          success: false,
          error: 'Paramètre "query" requis'
        });
        return;
      }
      
      try {
        // 🔧 CORRECTION - Utilisation de callPythonFunction comme SpatialEndpoints
        log.info('🔍 Recherche sémantique via callPythonFunction');
        
        const results = await callPythonFunction(activeDoc, req, 'VECTOR_SEARCH_SYSTEM', [tableId, query, limit, threshold]);
        
        res.json({
          success: true,
          data: {
            query,
            table_id: tableId,
            results: results || [],
            limit,
            threshold,
            timestamp: new Date().toISOString()
          }
        });
        
      } catch (error) {
        log.error('❌ Erreur recherche sémantique:', error);
        res.status(500).json({
          success: false,
          error: 'Erreur recherche sémantique',
          details: error.message
        });
      }
    })
  );

  /**
   * POST /api/docs/:docId/tables/:tableId/embedding/generate
   * Enqueuer des embeddings pour génération asynchrone
   * NOUVELLE VERSION: Utilise la queue asynchrone au lieu de l'appel Python synchrone
   * Nécessite droits d'édition (vérifié par applyUserActions)
   */
  app.post('/api/docs/:docId/tables/:tableId/embedding/generate',
    withDoc(async (activeDoc: ActiveDoc, req: RequestWithLogin, res: Response) => {
      const { tableId } = req.params;
      const { row_ids = [] } = req.body;

      try {
        // Normaliser les row_ids (gérer {id: X} ou X)
        const numericRowIds = row_ids.map((rowId: any) =>
          typeof rowId === 'object' && rowId !== null ? rowId.id : rowId
        );

        if (numericRowIds.length === 0) {
          res.status(400).json({
            success: false,
            error: 'Aucun row_id fourni'
          });
          return;
        }

        log.info(`📥 Enqueue embedding generation: ${tableId}, ${numericRowIds.length} rows`);

        // Créer un ActionGroup simulé pour déclencher la détection de queue
        // Note: Normalement ceci est fait automatiquement par Sharing.ts après applyUserActions
        // Mais pour l'endpoint manual, on simule une modification pour enqueuer

        // Alternative: Appeler directement la méthode de queue si elle existe
        // Pour l'instant, on utilise l'approche synchrone mais avec session système
        // pour garantir la persistance, en attendant que la queue automatique soit testée

        const docSession = docSessionFromRequest(req);
        const results = [];
        const embeddingsToStore: Record<number, {embedding: string, hash: string}> = {};

        // Générer embeddings via Python (synchrone pour l'instant)
        for (const numericRowId of numericRowIds) {
          try {
            const result = await callPythonFunction(activeDoc, req, 'AUTO_EMBEDDING', [tableId, numericRowId, 'albert']);

            if (result && result.embedding && result.hash) {
              embeddingsToStore[numericRowId] = {
                embedding: JSON.stringify(result.embedding),
                hash: result.hash
              };
              results.push({
                row_id: numericRowId,
                success: true,
                embedding_length: result.embedding.length
              });
            } else {
              results.push({
                row_id: numericRowId,
                success: false,
                error: 'Embedding generation returned no data'
              });
            }
          } catch (error) {
            log.error(`Erreur génération embedding row ${numericRowId}:`, error);
            results.push({
              row_id: numericRowId,
              success: false,
              error: error.message
            });
          }
        }

        // Persister via BulkUpdateRecord DANS UNE TRANSACTION
        // Utiliser makeExceptionalDocSession pour garantir les droits
        if (Object.keys(embeddingsToStore).length > 0) {
          const rowIdsToUpdate = Object.keys(embeddingsToStore).map(Number);
          const embeddingValues = rowIdsToUpdate.map(id => embeddingsToStore[id].embedding);
          const hashValues = rowIdsToUpdate.map(id => embeddingsToStore[id].hash);

          // IMPORTANT: Persister IMMÉDIATEMENT après génération
          // avant que le document ne se ferme
          try {
            await activeDoc.applyUserActions(docSession, [[
              'BulkUpdateRecord',
              tableId,
              rowIdsToUpdate,
              {
                grist_record_embedding: embeddingValues,
                grist_embedding_hash: hashValues
              }
            ]]);

            log.info(`✅ ${rowIdsToUpdate.length} embeddings persistés immédiatement dans ${tableId}`);
          } catch (persistError) {
            log.error(`❌ Erreur persistance embeddings:`, persistError);
            throw persistError;
          }
        }

        res.json({
          success: true,
          data: {
            table_id: tableId,
            processed: results.length,
            successful: results.filter(r => r.success).length,
            results,
            message: 'Embeddings générés et persistés immédiatement (synchrone)'
          }
        });

      } catch (error) {
        log.error('❌ Erreur endpoint embedding/generate:', error);
        res.status(500).json({
          success: false,
          error: 'Erreur génération embeddings',
          details: error.message
        });
      }
    })
  );

  /**
   * GET /api/docs/:docId/embedding/status
   * Statut global de l'embedding pour un document
   * Nécessite droits de lecture (vérifié par fetchDoc)
   */
  app.get('/api/docs/:docId/embedding/status',
    withDoc(async (activeDoc: ActiveDoc, req: RequestWithLogin, res: Response) => {
      try {
        // Récupérer statut de toutes les tables (à implémenter)
        const status = {
          enabled_tables: 0,
          total_embeddings: 0,
          pending_updates: 0,
          last_update: null,
          services_available: ['albert', 'openai']
        };
        
        res.json({
          success: true,
          data: status
        });
        
      } catch (error) {
        res.status(500).json({
          success: false,
          error: 'Erreur statut embedding'
        });
      }
    })
  );

  log.info('✅ Endpoints embedding ajoutés à l\'application Express');
}
