/**
 * EmbeddingManager: Gestionnaire asynchrone pour auto-embedding des records Grist
 *
 * Architecture inspirée de DocTriggers (webhooks async):
 * - Queue in-memory pour performance
 * - Worker loop en arrière-plan
 * - Batching pour optimiser les appels API
 * - Retry avec exponential backoff
 *
 * Pattern: Non-bloquant pour l'utilisateur, traitement async en background
 */

import {ActionGroup} from 'app/common/ActionGroup';
import {BulkColValues} from 'app/common/DocActions';
import {
  EmbeddingConfig,
  EmbeddingRequest,
  EmbeddingResult,
  EmbeddingStats
} from 'app/common/EmbeddingTypes';
import {ActiveDoc} from 'app/server/lib/ActiveDoc';
import {makeExceptionalDocSession} from 'app/server/lib/DocSession';
import * as crypto from 'crypto';
import fetch from 'node-fetch';
import log from 'app/server/lib/log';

// Configuration via variables d'environnement
const ALBERT_API_URL = process.env.ALBERT_API_URL || 'https://albert.api.etalab.gouv.fr/v1';
const ALBERT_API_TOKEN = process.env.ALBERT_API_TOKEN || '';
const ALBERT_MODEL = process.env.ALBERT_MODEL_EMBEDDING || 'embeddings-small';

const OPENAI_API_URL = 'https://api.openai.com/v1/embeddings';
const OPENAI_API_TOKEN = process.env.OPENAI_API_TOKEN || '';
const OPENAI_MODEL = 'text-embedding-ada-002';

// Configuration du worker
const BATCH_SIZE = parseInt(process.env.EMBEDDING_BATCH_SIZE || '10', 10);
const MAX_QUEUE_SIZE = parseInt(process.env.EMBEDDING_MAX_QUEUE_SIZE || '10000', 10);
const MAX_RETRIES = parseInt(process.env.EMBEDDING_MAX_RETRIES || '3', 10);
const LOOP_DELAY_MS = parseInt(process.env.EMBEDDING_LOOP_DELAY_MS || '5000', 10);
const PARALLEL_REQUESTS = parseInt(process.env.EMBEDDING_PARALLEL_REQUESTS || '10', 10);

/**
 * Gestionnaire principal pour l'auto-embedding
 */
export class EmbeddingManager {
  private _embeddingQueue: EmbeddingRequest[] = [];
  private _isProcessing: boolean = false;
  private _loopTimeout: NodeJS.Timeout | null = null;
  private _stats = {
    totalProcessed: 0,
    totalFailed: 0,
    processingTimes: [] as number[],
    lastProcessedAt: undefined as number | undefined,
  };

  constructor(private _activeDoc: ActiveDoc) {
    this._log('EmbeddingManager initialized');
  }

  /**
   * Démarrer le worker loop
   */
  public start(): void {
    if (this._loopTimeout) {
      return; // Déjà démarré
    }
    this._scheduleLoop();
    this._log('EmbeddingManager worker started');

    // Initialiser les colonnes système pour toutes les tables au démarrage
    // Délai pour laisser le sandbox Python s'initialiser complètement
    setTimeout(() => {
      this._initializeAllTables().catch(err => {
        this._log(`Error initializing tables: ${err}`, 'error');
      });
    }, 5000);
  }

  /**
   * Arrêter le worker et attendre la fin du traitement en cours
   */
  public async shutdown(): Promise<void> {
    this._log('EmbeddingManager shutting down...');

    if (this._loopTimeout) {
      clearTimeout(this._loopTimeout);
      this._loopTimeout = null;
    }

    // Attendre fin du traitement en cours (max 30s)
    const maxWait = 30000;
    const startWait = Date.now();
    while (this._isProcessing && (Date.now() - startWait < maxWait)) {
      await this._delay(100);
    }

    this._log(`EmbeddingManager shutdown complete. Remaining queue: ${this._embeddingQueue.length}`);
  }

  /**
   * Point d'entrée principal: Détecter et enqueuer les embeddings nécessaires
   * Appelé après apply_user_actions via setImmediate() pour être non-bloquant
   */
  public async detectAndQueueEmbeddings(actionGroup: ActionGroup): Promise<void> {
    try {
      this._log(`[DEBUG] detectAndQueueEmbeddings called`);

      // Analyser les actions pour détecter les modifications de données
      const requests = await this._analyzeActions(actionGroup);

      this._log(`[DEBUG] _analyzeActions returned ${requests.length} requests`);

      if (requests.length > 0) {
        this._enqueueRequests(requests);
        this._log(`Queued ${requests.length} embedding requests`);
      }
    } catch (err) {
      this._log(`Error detecting embeddings: ${err}`, 'error');
    }
  }

  /**
   * Obtenir les statistiques du manager
   */
  public getStats(): EmbeddingStats {
    const avgTime = this._stats.processingTimes.length > 0
      ? this._stats.processingTimes.reduce((a, b) => a + b, 0) / this._stats.processingTimes.length
      : 0;

    return {
      queueSize: this._embeddingQueue.length,
      totalProcessed: this._stats.totalProcessed,
      totalFailed: this._stats.totalFailed,
      averageTimeMs: Math.round(avgTime),
      isProcessing: this._isProcessing,
      lastProcessedAt: this._stats.lastProcessedAt,
    };
  }

  // ============================================================================
  // ANALYSE DES ACTIONS
  // ============================================================================

  /**
   * Analyser un ActionGroup pour détecter les records nécessitant un embedding
   * Utilise l'ActionSummary qui contient les informations sur les tables/lignes modifiées
   */
  private async _analyzeActions(actionGroup: ActionGroup): Promise<EmbeddingRequest[]> {
    const requests: EmbeddingRequest[] = [];

    // Utiliser ActionSummary pour identifier les changements
    const summary = actionGroup.actionSummary;
    if (!summary || !summary.tableDeltas) {
      this._log(`[DEBUG] No summary or tableDeltas in actionGroup`);
      return requests;
    }

    this._log(`[DEBUG] Analyzing ${Object.keys(summary.tableDeltas).length} table(s)`);

    // Parcourir chaque table modifiée
    for (const [tableId, tableDelta] of Object.entries(summary.tableDeltas)) {
      this._log(`[DEBUG] Checking table ${tableId}: addRows=${tableDelta.addRows.length}, updateRows=${tableDelta.updateRows.length}`);

      // Ignorer les tables système
      if (tableId.startsWith('_grist_')) {
        this._log(`[DEBUG] Skipping system table ${tableId}`);
        continue;
      }

      // Vérifier si la table a l'embedding activé
      const config = await this._getTableEmbeddingConfig(tableId);
      this._log(`[DEBUG] Config for ${tableId}: enabled=${config?.enabled}, autoGenerate=${config?.autoGenerate}`);

      if (!config || !config.enabled || !config.autoGenerate) {
        this._log(`[DEBUG] Embedding disabled for ${tableId}`);
        continue;
      }

      // Vérifier et créer les colonnes système si nécessaire
      await this._ensureEmbeddingColumns(tableId);

      // Collecter tous les rowIds affectés (ajoutés ou modifiés)
      const affectedRows = new Set<number>();

      // Lignes ajoutées : toujours générer embedding
      for (const rowId of tableDelta.addRows) {
        affectedRows.add(rowId);
      }

      // Lignes modifiées : générer embedding si colonnes texte modifiées
      const sourceColumns = config.sourceColumns || await this._detectTextColumns(tableId);
      const modifiedTextColumns = Object.keys(tableDelta.columnDeltas).filter(col =>
        sourceColumns.includes(col)
      );

      if (modifiedTextColumns.length > 0) {
        for (const rowId of tableDelta.updateRows) {
          affectedRows.add(rowId);
        }
      }

      // Créer des requêtes pour chaque row affectée
      for (const rowId of affectedRows) {
        const request = await this._createEmbeddingRequest(tableId, rowId, config);
        if (request) {
          requests.push(request);
        }
      }
    }

    return requests;
  }

  /**
   * Créer une requête d'embedding pour un record
   */
  private async _createEmbeddingRequest(
    tableId: string,
    rowId: number,
    config: EmbeddingConfig
  ): Promise<EmbeddingRequest | null> {
    try {
      // Extraire le contenu du record
      const content = await this._extractRecordContent(tableId, rowId, config);
      if (!content) {
        return null; // Pas de contenu à embedder
      }

      // Calculer hash du contenu
      const contentHash = this._computeHash(content);

      // Vérifier si l'embedding est déjà à jour (via hash)
      const currentHash = await this._getCurrentHash(tableId, rowId);
      if (currentHash === contentHash) {
        return null; // Déjà à jour
      }

      return {
        tableId,
        rowId,
        content,
        contentHash,
        priority: this._calculatePriority(tableId, rowId),
        queuedAt: Date.now(),
        retryCount: 0,
      };
    } catch (err) {
      this._log(`Error creating embedding request for ${tableId}:${rowId}: ${err}`, 'error');
      return null;
    }
  }

  // ============================================================================
  // EXTRACTION DE CONTENU
  // ============================================================================

  /**
   * Extraire le contenu textuel d'un record pour l'embedding
   */
  private async _extractRecordContent(
    tableId: string,
    rowId: number,
    config: EmbeddingConfig
  ): Promise<string | null> {
    try {
      // Récupérer les données via pyCall
      const tableData = await (this._activeDoc as any)._rawPyCall('fetch_table', tableId, true);

      // Trouver l'index du rowId
      const rowIndex = tableData[2].indexOf(rowId);
      if (rowIndex === -1) {
        return null;
      }

      // Extraire les valeurs des colonnes source
      const sourceColumns = config.sourceColumns || await this._detectTextColumns(tableId);
      const parts: string[] = [];

      for (const colId of sourceColumns) {
        const colValues = tableData[3][colId];
        if (colValues && colValues[rowIndex]) {
          const value = colValues[rowIndex];
          if (typeof value === 'string' && value.trim()) {
            parts.push(`${colId}: ${value.trim()}`);
          }
        }
      }

      return parts.length > 0 ? parts.join(' | ') : null;
    } catch (err) {
      this._log(`Error extracting content for ${tableId}:${rowId}: ${err}`, 'error');
      return null;
    }
  }

  /**
   * Détecter automatiquement les colonnes Text d'une table
   */
  private async _detectTextColumns(tableId: string): Promise<string[]> {
    try {
      const metaTables = await (this._activeDoc as any)._rawPyCall('fetch_meta_tables', false);
      const columnsTable = metaTables._grist_Tables_column;

      const textColumns: string[] = [];
      for (let i = 0; i < columnsTable[2].length; i++) {
        const fields = columnsTable[3];
        // const parentId = fields.parentId[i]; // unused
        const colId = fields.colId[i];
        const type = fields.type[i];
        const isFormula = fields.isFormula[i];

        // Vérifier si c'est une colonne de notre table
        // (nécessite de mapper tableId → table numeric ID, simplifié ici)
        if (type === 'Text' || type === 'Any' || type === 'Choice') {
          // Exclure :
          // - Les formules (isFormula)
          // - Les colonnes système (_grist_*)
          // - manualSort
          // - Les colonnes d'embedding système (grist_record_embedding, grist_embedding_hash)
          if (!isFormula &&
              !colId.startsWith('_grist_') &&
              !colId.startsWith('grist_') &&  // Exclure grist_record_embedding, grist_embedding_hash
              colId !== 'manualSort') {
            textColumns.push(colId);
          }
        }
      }

      return textColumns;
    } catch (err) {
      this._log(`Error detecting text columns for ${tableId}: ${err}`, 'error');
      return [];
    }
  }

  /**
   * Récupérer le hash actuel d'un record
   */
  private async _getCurrentHash(tableId: string, rowId: number): Promise<string | null> {
    try {
      const tableData = await (this._activeDoc as any)._rawPyCall('fetch_table', tableId, false);
      const rowIndex = tableData[2].indexOf(rowId);
      if (rowIndex === -1) {
        return null;
      }

      const hashValues = tableData[3]['grist_embedding_hash'];
      return hashValues ? hashValues[rowIndex] : null;
    } catch (err) {
      return null;
    }
  }

  /**
   * Initialiser toutes les tables au démarrage (créer colonnes système si nécessaire)
   */
  private async _initializeAllTables(): Promise<void> {
    try {
      this._log('[INIT] Initializing embedding columns for all tables...');

      // Récupérer la liste de toutes les tables
      const tables = await (this._activeDoc as any)._rawPyCall('get_table_list');
      this._log(`[INIT] Found ${tables.length} tables to check`);

      for (const tableId of tables) {
        // Ignorer les tables système
        if (tableId.startsWith('_grist_')) {
          continue;
        }

        // Vérifier et créer les colonnes si nécessaire
        await this._ensureEmbeddingColumns(tableId);
      }

      this._log('[INIT] Table initialization complete');
    } catch (err) {
      this._log(`[INIT] Error during table initialization: ${err}`, 'error');
    }
  }

  /**
   * S'assurer que les colonnes système d'embedding existent dans la table
   */
  private async _ensureEmbeddingColumns(tableId: string): Promise<void> {
    try {
      // Récupérer les colonnes existantes
      const tableData = await (this._activeDoc as any)._rawPyCall('fetch_table', tableId, false);
      const existingColumns = Object.keys(tableData[3]);

      const columnsToAdd: Array<[string, any]> = [];

      // Vérifier grist_record_embedding
      if (!existingColumns.includes('grist_record_embedding')) {
        this._log(`[DEBUG] Table ${tableId} missing grist_record_embedding column, will create it`);
        columnsToAdd.push(['grist_record_embedding', {
          type: 'Vector',
          isFormula: false
        }]);
      }

      // Vérifier grist_embedding_hash
      if (!existingColumns.includes('grist_embedding_hash')) {
        this._log(`[DEBUG] Table ${tableId} missing grist_embedding_hash column, will create it`);
        columnsToAdd.push(['grist_embedding_hash', {
          type: 'Text',
          isFormula: false
        }]);
      }

      // Créer les colonnes manquantes
      if (columnsToAdd.length > 0) {
        this._log(`Creating ${columnsToAdd.length} system column(s) for table ${tableId}`);
        const docSession = makeExceptionalDocSession('system');

        for (const [colId, colInfo] of columnsToAdd) {
          await this._activeDoc.applyUserActions(docSession, [
            ['AddColumn', tableId, colId, colInfo]
          ]);
        }

        this._log(`Successfully created system columns for table ${tableId}`);
      }
    } catch (err) {
      this._log(`Error ensuring embedding columns for ${tableId}: ${err}`, 'error');
      // Ne pas bloquer si la création échoue
    }
  }

  /**
   * Récupérer la configuration d'embedding d'une table
   */
  private async _getTableEmbeddingConfig(tableId: string): Promise<EmbeddingConfig | null> {
    // Configuration par défaut: auto-embedding activé pour toutes les tables
    // TODO: Implémenter récupération depuis metadata si nécessaire
    return {
      enabled: true,
      autoGenerate: true,
      provider: ALBERT_API_TOKEN ? 'albert' : 'openai',
      triggerOn: ['insert', 'update'],
      batchSize: BATCH_SIZE,
      maxRetries: MAX_RETRIES,
    };
  }

  // ============================================================================
  // GESTION DE LA QUEUE
  // ============================================================================

  /**
   * Ajouter des requêtes à la queue
   */
  private _enqueueRequests(requests: EmbeddingRequest[]): void {
    for (const request of requests) {
      // Vérifier limite de queue
      if (this._embeddingQueue.length >= MAX_QUEUE_SIZE) {
        this._log('Embedding queue full, dropping request', 'warn');
        continue;
      }

      // Vérifier si déjà en queue (même tableId+rowId)
      const existing = this._embeddingQueue.findIndex(
        r => r.tableId === request.tableId && r.rowId === request.rowId
      );

      if (existing >= 0) {
        // Remplacer avec version plus récente
        this._embeddingQueue[existing] = request;
      } else {
        this._embeddingQueue.push(request);
      }
    }

    // Trier par priorité décroissante
    this._embeddingQueue.sort((a, b) => b.priority - a.priority);
  }

  /**
   * Calculer la priorité d'une requête
   */
  private _calculatePriority(tableId: string, rowId: number): number {
    // Priorité basique pour l'instant
    // TODO: Implémenter logique sophistiquée (taille table, activité user, etc.)
    return 5; // Medium priority
  }

  // ============================================================================
  // WORKER LOOP
  // ============================================================================

  /**
   * Planifier le prochain cycle du loop
   */
  private _scheduleLoop(): void {
    if (this._loopTimeout) {
      return;
    }

    // Ajouter variance pour éviter pics de charge (comme DocTriggers)
    const variance = Math.random() * 1000 - 500; // ±500ms
    const delay = Math.max(100, LOOP_DELAY_MS + variance);

    this._loopTimeout = setTimeout(() => {
      this._loopTimeout = null;
      this._processLoop().catch(err => {
        this._log(`Error in embedding loop: ${err}`, 'error');
      });
    }, delay);
  }

  /**
   * Cycle de traitement principal
   */
  private async _processLoop(): Promise<void> {
    try {
      if (this._isProcessing) {
        // Déjà en traitement, skip
        this._scheduleLoop();
        return;
      }

      if (this._embeddingQueue.length === 0) {
        // Rien à faire
        this._scheduleLoop();
        return;
      }

      this._isProcessing = true;
      const startTime = Date.now();

      // Prendre un batch de requêtes
      const batch = this._embeddingQueue.splice(0, BATCH_SIZE);
      this._log(`Processing batch of ${batch.length} embedding requests`);

      // Traiter en parallèle (limité par PARALLEL_REQUESTS)
      const results = await this._processBatch(batch);

      // Persister les embeddings réussis
      await this._persistEmbeddings(results.filter(r => r.success));

      // Re-enqueuer les échecs avec retry
      const failures = results.filter(r => !r.success);
      this._handleFailures(failures);

      // Statistiques
      const processingTime = Date.now() - startTime;
      this._stats.totalProcessed += results.filter(r => r.success).length;
      this._stats.totalFailed += failures.length;
      this._stats.processingTimes.push(processingTime);
      if (this._stats.processingTimes.length > 100) {
        this._stats.processingTimes.shift(); // Garder les 100 derniers
      }
      this._stats.lastProcessedAt = Date.now();

      this._log(`Batch processed in ${processingTime}ms. Success: ${results.filter(r => r.success).length}, Failed: ${failures.length}`);
    } finally {
      this._isProcessing = false;
      this._scheduleLoop();
    }
  }

  /**
   * Traiter un batch de requêtes en parallèle
   */
  private async _processBatch(batch: EmbeddingRequest[]): Promise<Array<{request: EmbeddingRequest; success: boolean; result?: EmbeddingResult; error?: string}>> {
    const results = [];

    // Traiter par chunks pour limiter parallélisme
    for (let i = 0; i < batch.length; i += PARALLEL_REQUESTS) {
      const chunk = batch.slice(i, i + PARALLEL_REQUESTS);
      const chunkResults = await Promise.all(
        chunk.map(async (request) => {
          try {
            const result = await this._generateEmbedding(request);
            return {request, success: true, result};
          } catch (error) {
            return {request, success: false, error: String(error)};
          }
        })
      );
      results.push(...chunkResults);
    }

    return results;
  }

  /**
   * Générer un embedding via API externe
   */
  private async _generateEmbedding(request: EmbeddingRequest): Promise<EmbeddingResult> {
    const config = await this._getTableEmbeddingConfig(request.tableId);
    const provider = config?.provider || 'albert';

    if (provider === 'albert') {
      return await this._generateAlbertEmbedding(request);
    } else if (provider === 'openai') {
      return await this._generateOpenAIEmbedding(request);
    } else {
      throw new Error(`Unknown embedding provider: ${provider}`);
    }
  }

  /**
   * Générer embedding via Albert API
   */
  private async _generateAlbertEmbedding(request: EmbeddingRequest): Promise<EmbeddingResult> {
    if (!ALBERT_API_TOKEN) {
      throw new Error('ALBERT_API_TOKEN not configured');
    }

    const response = await fetch(`${ALBERT_API_URL}/embeddings`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${ALBERT_API_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input: request.content,
        model: ALBERT_MODEL,
      }),
      timeout: 30000,
    });

    if (!response.ok) {
      throw new Error(`Albert API error: ${response.status} ${await response.text()}`);
    }

    const data = await response.json();
    const embedding = data.data[0].embedding;

    return {
      rowId: request.rowId,
      embedding,
      dimensions: embedding.length,
      contentHash: request.contentHash,
      generatedAt: Date.now(),
      provider: 'albert',
    };
  }

  /**
   * Générer embedding via OpenAI API
   */
  private async _generateOpenAIEmbedding(request: EmbeddingRequest): Promise<EmbeddingResult> {
    if (!OPENAI_API_TOKEN) {
      throw new Error('OPENAI_API_TOKEN not configured');
    }

    const response = await fetch(OPENAI_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENAI_API_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        input: request.content,
        model: OPENAI_MODEL,
      }),
      timeout: 30000,
    });

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.status} ${await response.text()}`);
    }

    const data = await response.json();
    const embedding = data.data[0].embedding;

    return {
      rowId: request.rowId,
      embedding,
      dimensions: embedding.length,
      contentHash: request.contentHash,
      generatedAt: Date.now(),
      provider: 'openai',
    };
  }

  /**
   * Persister les embeddings générés dans Grist
   */
  private async _persistEmbeddings(results: Array<{result?: EmbeddingResult; request: EmbeddingRequest}>): Promise<void> {
    if (results.length === 0) {
      return;
    }

    // Grouper par table
    const byTable = new Map<string, Array<{rowId: number; embedding: number[]; hash: string}>>();
    for (const {result, request} of results) {
      if (!result) continue;

      if (!byTable.has(request.tableId)) {
        byTable.set(request.tableId, []);
      }
      byTable.get(request.tableId)!.push({
        rowId: result.rowId,
        embedding: result.embedding,
        hash: result.contentHash,
      });
    }

    // Persister table par table via BulkUpdateRecord
    for (const [tableId, records] of byTable) {
      try {
        const rowIds = records.map(r => r.rowId);
        const colValues: BulkColValues = {
          grist_record_embedding: records.map(r => JSON.stringify(r.embedding)),
          grist_embedding_hash: records.map(r => r.hash),
        };

        const docSession = makeExceptionalDocSession('system');
        await this._activeDoc.applyUserActions(
          docSession,
          [['BulkUpdateRecord', tableId, rowIds, colValues]]
        );

        this._log(`Persisted ${records.length} embeddings for table ${tableId}`);
      } catch (err) {
        this._log(`Error persisting embeddings for ${tableId}: ${err}`, 'error');
      }
    }
  }

  /**
   * Gérer les échecs avec retry logic
   */
  private _handleFailures(failures: Array<{request: EmbeddingRequest; error?: string}>): void {
    for (const {request, error} of failures) {
      if (request.retryCount < MAX_RETRIES) {
        // Re-enqueuer avec retry count incrémenté
        const retryRequest = {
          ...request,
          retryCount: request.retryCount + 1,
          lastError: error,
        };
        this._embeddingQueue.push(retryRequest);
        this._log(`Retrying ${request.tableId}:${request.rowId} (attempt ${retryRequest.retryCount}/${MAX_RETRIES})`);
      } else {
        // Max retries atteint, abandonner
        this._log(`Max retries reached for ${request.tableId}:${request.rowId}. Error: ${error}`, 'error');
      }
    }
  }

  // ============================================================================
  // HELPERS
  // ============================================================================

  /**
   * Calculer hash MD5 d'un contenu
   */
  private _computeHash(content: string): string {
    return crypto.createHash('md5').update(content).digest('hex');
  }

  /**
   * Delay helper
   */
  private _delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Logging helper
   */
  private _log(message: string, level: 'info' | 'warn' | 'error' = 'info'): void {
    const prefix = `[EmbeddingManager ${this._activeDoc.docName}]`;
    if (level === 'error') {
      log.error(`${prefix} ${message}`);
    } else if (level === 'warn') {
      log.warn(`${prefix} ${message}`);
    } else {
      log.info(`${prefix} ${message}`);
    }
  }
}
