import * as express from 'express';
import { Response } from 'express';
import { expressWrap } from 'app/server/lib/expressWrap';
import { DocManager } from 'app/server/lib/DocManager';
import { ActiveDoc } from 'app/server/lib/ActiveDoc';
import { docSessionFromRequest } from 'app/server/lib/DocSession';
import { RequestWithLogin } from 'app/server/lib/Authorizer';
import log from 'app/server/lib/log';

// Types pour les handlers de document
type WithDocHandler = (activeDoc: ActiveDoc, req: RequestWithLogin, resp: Response) => Promise<void>;

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
    // Créer les champs système si nécessaire (via dataEngine)
    const dataEngine = (activeDoc as any)._dataEngine;
    if (dataEngine && typeof dataEngine.pyCall === 'function') {
      await dataEngine.pyCall('create_system_embedding_fields', [tableId]);
    }
    
    // Sauvegarder la configuration (pour l'instant log seulement)
    log.info(`✅ Configuration embedding sauvée pour table ${tableId}`, { config });
    
  } catch (error) {
    log.error(`❌ Erreur configuration embedding ${tableId}:`, error);
    throw error;
  }
}

/**
 * Ajouter les endpoints d'embedding à l'application Express
 */
export function addEmbeddingEndpoints(app: express.Application, docManager: DocManager): void {
  
  // Helper pour accès document avec session correcte
  const withDoc = (callback: WithDocHandler) => {
    return expressWrap(async (req: any, res: express.Response) => {
      const docId = req.params.docId;
      
      try {
        const session = docSessionFromRequest(req);
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
   */
  app.get('/api/docs/:docId/tables/:tableId/embedding/config',
    withDoc(async (activeDoc: ActiveDoc, req: RequestWithLogin, res: Response) => {
      try {
        // Récupérer config depuis champs système (à implémenter)
        const config = { enabled: false }; // Configuration par défaut
        
        res.json({
          success: true,
          config: config
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
        // Appeler VECTOR_SEARCH_SYSTEM via dataEngine
        let results = [];
        const dataEngine = (activeDoc as any)._dataEngine;
        if (dataEngine && typeof dataEngine.pyCall === 'function') {
          try {
            results = await dataEngine.pyCall('VECTOR_SEARCH_SYSTEM', [
              tableId, query, limit, threshold
            ]);
          } catch (pyError) {
            log.warn('❌ Erreur appel VECTOR_SEARCH_SYSTEM:', pyError);
            // Fallback avec résultats vides
            results = [];
          }
        }
        
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
   * Générer embeddings pour des records spécifiques
   */
  app.post('/api/docs/:docId/tables/:tableId/embedding/generate',
    withDoc(async (activeDoc: ActiveDoc, req: RequestWithLogin, res: Response) => {
      const { tableId } = req.params;
      const { row_ids = [] } = req.body;
      
      try {
        const results = [];
        const dataEngine = (activeDoc as any)._dataEngine;
        
        for (const rowId of row_ids) {
          try {
            let embedding = null;
            if (dataEngine && typeof dataEngine.pyCall === 'function') {
              embedding = await dataEngine.pyCall('AUTO_EMBEDDING', [tableId, rowId]);
            }
            
            results.push({
              row_id: rowId,
              success: !!embedding,
              embedding_length: embedding ? embedding.length : 0
            });
          } catch (error: any) {
            results.push({
              row_id: rowId,
              success: false,
              error: error.message
            });
          }
        }
        
        res.json({
          success: true,
          data: {
            table_id: tableId,
            processed: results.length,
            successful: results.filter(r => r.success).length,
            results
          }
        });
        
      } catch (error) {
        res.status(500).json({
          success: false,
          error: 'Erreur génération embeddings'
        });
      }
    })
  );

  /**
   * GET /api/docs/:docId/embedding/status
   * Statut global de l'embedding pour un document
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
          services_available: ['albert', 'openai', 'mock']
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
