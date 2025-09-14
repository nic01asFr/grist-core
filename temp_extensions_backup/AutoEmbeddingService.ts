import {DataEngine} from 'app/server/lib/DataEngine';
import {DocStorage} from 'app/server/lib/DocStorage';
import {GristDoc} from 'app/server/lib/GristDoc';
import {EmbeddingService} from 'app/server/api/SemanticSearchApi';
import log from 'app/server/lib/log';

/**
 * Service d'auto-génération d'embeddings pour les colonnes Text
 * 
 * Fonctionnalités :
 * - Génération automatique d'embeddings lors de la création/modification de contenu Text
 * - Colonnes shadow pour stocker les embeddings sans encombrer l'interface
 * - Processing batch pour optimiser les performances
 * - Configuration par table/colonne (activé/désactivé)
 * - Différents modèles d'embedding (OpenAI, sentence-transformers, etc.)
 * - Mise à jour incrémentale efficace
 */

export interface AutoEmbeddingConfig {
  enabled: boolean;
  model: 'sentence-transformers' | 'openai' | 'cohere' | 'albert';
  batchSize: number;
  updateThreshold: number;  // Seuil de changement de texte pour déclencher re-embedding
  excludeShortText: number; // Ignorer textes < N caractères
  maxLength: number;        // Tronquer textes > N caractères
}

export interface EmbeddingColumnInfo {
  sourceColumnId: string;
  sourceTableId: string;
  embeddingColumnId: string;
  config: AutoEmbeddingConfig;
  lastProcessed: Date;
  totalProcessed: number;
}

/**
 * Service principal d'auto-embedding
 */
export class AutoEmbeddingService {
  private embeddingService: EmbeddingService;
  private activeColumns: Map<string, EmbeddingColumnInfo> = new Map();
  private processingQueue: Array<{tableId: string, rowId: number, text: string}> = [];
  private isProcessing = false;

  private defaultConfig: AutoEmbeddingConfig = {
    enabled: true,
    model: 'albert',          // Utiliser Albert API par défaut
    batchSize: 50,
    updateThreshold: 10,      // Re-embed si >10 caractères ont changé
    excludeShortText: 20,     // Ignorer si <20 caractères
    maxLength: 5000           // Tronquer à 5000 caractères
  };

  // Configuration Albert API
  private albertConfig = {
    apiUrl: process.env.ALBERT_API_URL || 'https://albert.api.etalab.gouv.fr/v1',
    apiToken: process.env.ALBERT_API_TOKEN || '',
    model: process.env.ALBERT_MODEL || 'albert-large',
    embeddingModel: process.env.ALBERT_MODEL_EMBEDDING || 'embeddings-small',
    dimensions: parseInt(process.env.EMBEDDING_DIMENSION || '1024')
  };

  constructor(
    private gristDoc: GristDoc,
    private docStorage: DocStorage,
    private dataEngine: DataEngine
  ) {
    this.embeddingService = EmbeddingService.getInstance();
    this.initializeAutoEmbedding();
  }

  /**
   * Initialise le service d'auto-embedding
   */
  private async initializeAutoEmbedding(): Promise<void> {
    try {
      // Détecter les colonnes Text existantes et créer les colonnes shadow
      await this.detectAndCreateEmbeddingColumns();
      
      // Configurer les hooks sur les modifications de données
      this.setupDataChangeHooks();
      
      // Traitement initial des données existantes (si nécessaire)
      await this.processExistingData();
      
      log.info(`AutoEmbeddingService initialisé pour ${this.activeColumns.size} colonnes`);
      
    } catch (error) {
      log.error('Erreur initialisation AutoEmbeddingService:', error);
    }
  }

  /**
   * Détecte les colonnes Text et crée les colonnes shadow d'embedding
   */
  private async detectAndCreateEmbeddingColumns(): Promise<void> {
    const docStructure = await this.gristDoc.getDocStructure();
    
    for (const table of docStructure.tables) {
      const textColumns = table.columns.filter(col => 
        col.type === 'Text' && this.shouldAutoEmbed(col)
      );

      for (const textCol of textColumns) {
        await this.createEmbeddingColumn(table.id, textCol.id);
      }
    }
  }

  /**
   * Détermine si une colonne Text doit avoir un auto-embedding
   */
  private shouldAutoEmbed(column: any): boolean {
    // Critères pour activer l'auto-embedding :
    // - Nom de colonne suggestif (description, content, summary, etc.)
    // - Pas déjà une colonne système
    // - Configuration explicite
    
    const embeddingFriendlyNames = [
      'description', 'content', 'summary', 'notes', 'comment', 'text', 
      'title', 'name', 'subject', 'message', 'review', 'feedback'
    ];
    
    const colNameLower = column.id.toLowerCase();
    const isEmbeddingFriendly = embeddingFriendlyNames.some(name => 
      colNameLower.includes(name)
    );
    
    const isSystemColumn = column.id.startsWith('_') || column.system;
    
    // Pour le MVP, activer pour toutes les colonnes Text non-système
    // En production, ceci serait configurable par l'utilisateur
    return !isSystemColumn && (isEmbeddingFriendly || process.env.GRIST_AUTO_EMBED_ALL === 'true');
  }

  /**
   * Crée une colonne shadow pour stocker les embeddings
   */
  private async createEmbeddingColumn(tableId: string, sourceColumnId: string): Promise<void> {
    const embeddingColumnId = `${sourceColumnId}_embedding`;
    
    try {
      // Vérifier si la colonne existe déjà
      const existingColumns = await this.dataEngine.query(
        `SELECT * FROM _grist_Tables_column WHERE tableId = ? AND colId = ?`,
        [tableId, embeddingColumnId]
      );

      if (existingColumns.length > 0) {
        log.info(`Colonne embedding ${embeddingColumnId} existe déjà dans ${tableId}`);
      } else {
        // Créer la colonne shadow
        await this.docStorage.addColumn(tableId, {
          colId: embeddingColumnId,
          type: 'Vector',
          isFormula: false,
          label: `${sourceColumnId} (embedding)`,
          description: `Auto-generated embeddings for ${sourceColumnId}`,
          // Propriétés pour masquer de l'interface utilisateur par défaut
          widgetOptions: JSON.stringify({
            hidden: true,
            system: true
          })
        });

        log.info(`Colonne embedding ${embeddingColumnId} créée dans ${tableId}`);
      }

      // Enregistrer la configuration
      const config: EmbeddingColumnInfo = {
        sourceColumnId,
        sourceTableId: tableId,
        embeddingColumnId,
        config: { ...this.defaultConfig },
        lastProcessed: new Date(),
        totalProcessed: 0
      };
      
      this.activeColumns.set(`${tableId}.${sourceColumnId}`, config);
      
    } catch (error) {
      log.error(`Erreur création colonne embedding ${embeddingColumnId}:`, error);
    }
  }

  /**
   * Configure les hooks pour détecter les modifications de données
   */
  private setupDataChangeHooks(): void {
    // Hook sur les modifications de données
    this.gristDoc.on('data-change', (event: any) => {
      this.handleDataChange(event);
    });
    
    // Hook sur l'ajout de nouvelles lignes
    this.gristDoc.on('record-add', (event: any) => {
      this.handleRecordAdd(event);
    });
    
    // Hook sur la modification de lignes
    this.gristDoc.on('record-update', (event: any) => {
      this.handleRecordUpdate(event);
    });
  }

  /**
   * Gère les changements de données pour déclencher les embeddings
   */
  private async handleDataChange(event: any): Promise<void> {
    try {
      const { tableId, changes } = event;
      
      for (const change of changes) {
        const columnKey = `${tableId}.${change.columnId}`;
        const embeddingInfo = this.activeColumns.get(columnKey);
        
        if (embeddingInfo) {
          // Ajouter à la queue de processing
          this.queueForProcessing(tableId, change.rowId, change.newValue);
        }
      }
      
      // Démarrer le processing si pas déjà en cours
      this.processQueue();
      
    } catch (error) {
      log.error('Erreur handleDataChange:', error);
    }
  }

  /**
   * Gère l'ajout de nouveaux enregistrements
   */
  private async handleRecordAdd(event: any): Promise<void> {
    try {
      const { tableId, rowId, values } = event;
      
      // Chercher les colonnes Text avec auto-embedding dans cette table
      for (const [key, embeddingInfo] of this.activeColumns.entries()) {
        if (embeddingInfo.sourceTableId === tableId) {
          const textValue = values[embeddingInfo.sourceColumnId];
          if (textValue && typeof textValue === 'string') {
            this.queueForProcessing(tableId, rowId, textValue);
          }
        }
      }
      
      this.processQueue();
      
    } catch (error) {
      log.error('Erreur handleRecordAdd:', error);
    }
  }

  /**
   * Gère la mise à jour d'enregistrements existants
   */
  private async handleRecordUpdate(event: any): Promise<void> {
    try {
      const { tableId, rowId, oldValues, newValues } = event;
      
      for (const [key, embeddingInfo] of this.activeColumns.entries()) {
        if (embeddingInfo.sourceTableId === tableId) {
          const columnId = embeddingInfo.sourceColumnId;
          const oldText = oldValues[columnId];
          const newText = newValues[columnId];
          
          // Vérifier si le texte a suffisamment changé pour justifier un re-embedding
          if (this.shouldReEmbed(oldText, newText, embeddingInfo.config)) {
            this.queueForProcessing(tableId, rowId, newText);
          }
        }
      }
      
      this.processQueue();
      
    } catch (error) {
      log.error('Erreur handleRecordUpdate:', error);
    }
  }

  /**
   * Détermine si un texte doit être re-embedé
   */
  private shouldReEmbed(oldText: string, newText: string, config: AutoEmbeddingConfig): boolean {
    if (!oldText && !newText) return false;
    if (!newText) return false; // Texte supprimé, pas besoin d'embedding
    
    // Ignorer les textes trop courts
    if (newText.length < config.excludeShortText) return false;
    
    // Si pas d'ancien texte, embedding nécessaire
    if (!oldText) return true;
    
    // Calculer le changement
    const changeSize = Math.abs(newText.length - oldText.length);
    const changeRatio = changeSize / Math.max(oldText.length, 1);
    
    // Re-embed si changement > seuil
    return changeSize > config.updateThreshold || changeRatio > 0.1;
  }

  /**
   * Ajoute un élément à la queue de processing
   */
  private queueForProcessing(tableId: string, rowId: number, text: string): void {
    this.processingQueue.push({ tableId, rowId, text });
  }

  /**
   * Traite la queue d'embeddings
   */
  private async processQueue(): Promise<void> {
    if (this.isProcessing || this.processingQueue.length === 0) return;
    
    this.isProcessing = true;
    
    try {
      // Grouper par batch
      const batchSize = Math.max(...Array.from(this.activeColumns.values())
        .map(info => info.config.batchSize));
      
      while (this.processingQueue.length > 0) {
        const batch = this.processingQueue.splice(0, batchSize);
        await this.processBatch(batch);
      }
      
    } catch (error) {
      log.error('Erreur processQueue:', error);
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Traite un batch d'embeddings
   */
  private async processBatch(
    batch: Array<{tableId: string, rowId: number, text: string}>
  ): Promise<void> {
    try {
      // Grouper par modèle d'embedding pour optimiser
      const byModel = new Map<string, typeof batch>();
      
      for (const item of batch) {
        const columnKey = `${item.tableId}.?`; // Trouver la config
        const embeddingInfo = Array.from(this.activeColumns.values())
          .find(info => info.sourceTableId === item.tableId);
        
        if (embeddingInfo) {
          const model = embeddingInfo.config.model;
          if (!byModel.has(model)) byModel.set(model, []);
          byModel.get(model)!.push(item);
        }
      }
      
      // Traiter chaque modèle
      for (const [model, items] of byModel.entries()) {
        await this.processModelBatch(model, items);
      }
      
    } catch (error) {
      log.error('Erreur processBatch:', error);
    }
  }

  /**
   * Traite un batch pour un modèle spécifique
   */
  private async processModelBatch(
    model: string,
    batch: Array<{tableId: string, rowId: number, text: string}>
  ): Promise<void> {
    try {
      // Préparer les textes pour embedding
      const texts = batch.map(item => {
        const config = this.getConfigForTable(item.tableId);
        return this.preprocessText(item.text, config);
      });
      
      // Générer les embeddings en batch
      const embeddings = await this.embeddingService.generateBatchEmbeddings(texts, model);
      
      // Sauvegarder dans la base
      const updates = batch.map((item, index) => ({
        tableId: item.tableId,
        rowId: item.rowId,
        embedding: embeddings[index]
      }));
      
      await this.saveEmbeddings(updates);
      
      log.info(`Traité ${batch.length} embeddings avec modèle ${model}`);
      
    } catch (error) {
      log.error(`Erreur processModelBatch pour ${model}:`, error);
    }
  }

  /**
   * Préprocesse le texte avant embedding
   */
  private preprocessText(text: string, config: AutoEmbeddingConfig): string {
    if (!text) return '';
    
    // Tronquer si trop long
    let processed = text.length > config.maxLength 
      ? text.substring(0, config.maxLength) 
      : text;
    
    // Nettoyer le texte (enlever HTML, normaliser espaces, etc.)
    processed = processed
      .replace(/<[^>]*>/g, ' ')           // Enlever HTML
      .replace(/\s+/g, ' ')              // Normaliser espaces
      .trim();
    
    return processed;
  }

  /**
   * Sauvegarde les embeddings dans la base
   */
  private async saveEmbeddings(
    updates: Array<{tableId: string, rowId: number, embedding: number[]}>
  ): Promise<void> {
    try {
      for (const update of updates) {
        // Trouver la colonne embedding correspondante
        const embeddingInfo = Array.from(this.activeColumns.values())
          .find(info => info.sourceTableId === update.tableId);
        
        if (embeddingInfo) {
          // Mise à jour dans la base
          await this.dataEngine.query(
            `UPDATE ${update.tableId} SET ${embeddingInfo.embeddingColumnId} = $1 WHERE id = $2`,
            [JSON.stringify(update.embedding), update.rowId]
          );
          
          // Mettre à jour les stats
          embeddingInfo.totalProcessed++;
          embeddingInfo.lastProcessed = new Date();
        }
      }
      
    } catch (error) {
      log.error('Erreur saveEmbeddings:', error);
    }
  }

  /**
   * Obtient la configuration pour une table
   */
  private getConfigForTable(tableId: string): AutoEmbeddingConfig {
    const embeddingInfo = Array.from(this.activeColumns.values())
      .find(info => info.sourceTableId === tableId);
    
    return embeddingInfo?.config || this.defaultConfig;
  }

  /**
   * Traite les données existantes (migration initiale)
   */
  private async processExistingData(): Promise<void> {
    try {
      log.info('Traitement des données existantes pour auto-embedding...');
      
      for (const [key, embeddingInfo] of this.activeColumns.entries()) {
        await this.processExistingDataForColumn(embeddingInfo);
      }
      
    } catch (error) {
      log.error('Erreur processExistingData:', error);
    }
  }

  /**
   * Traite les données existantes pour une colonne spécifique
   */
  private async processExistingDataForColumn(embeddingInfo: EmbeddingColumnInfo): Promise<void> {
    try {
      const { sourceTableId, sourceColumnId, embeddingColumnId } = embeddingInfo;
      
      // Trouver les enregistrements sans embedding
      const query = `
        SELECT id, ${sourceColumnId}
        FROM ${sourceTableId}
        WHERE ${sourceColumnId} IS NOT NULL 
          AND ${sourceColumnId} != ''
          AND (${embeddingColumnId} IS NULL OR ${embeddingColumnId} = '[]')
        ORDER BY id
        LIMIT 1000
      `;
      
      const records = await this.dataEngine.query(query);
      
      if (records.length > 0) {
        log.info(`Traitement de ${records.length} enregistrements existants pour ${sourceTableId}.${sourceColumnId}`);
        
        // Ajouter à la queue
        for (const record of records) {
          this.queueForProcessing(sourceTableId, record.id, record[sourceColumnId]);
        }
        
        // Démarrer le processing
        await this.processQueue();
      }
      
    } catch (error) {
      log.error(`Erreur processExistingDataForColumn:`, error);
    }
  }

  /**
   * API pour activer/désactiver l'auto-embedding sur une colonne
   */
  public async configureAutoEmbedding(
    tableId: string, 
    columnId: string, 
    config: Partial<AutoEmbeddingConfig>
  ): Promise<void> {
    const key = `${tableId}.${columnId}`;
    const embeddingInfo = this.activeColumns.get(key);
    
    if (embeddingInfo) {
      embeddingInfo.config = { ...embeddingInfo.config, ...config };
      log.info(`Configuration auto-embedding mise à jour pour ${key}`);
    }
  }

  /**
   * Obtient les statistiques d'auto-embedding
   */
  public getStats(): Record<string, any> {
    const stats: Record<string, any> = {
      activeColumns: this.activeColumns.size,
      queueSize: this.processingQueue.length,
      isProcessing: this.isProcessing,
      columns: {}
    };
    
    for (const [key, info] of this.activeColumns.entries()) {
      stats.columns[key] = {
        model: info.config.model,
        totalProcessed: info.totalProcessed,
        lastProcessed: info.lastProcessed,
        enabled: info.config.enabled
      };
    }
    
    return stats;
  }
}

/**
 * Factory pour créer le service d'auto-embedding
 */
export function createAutoEmbeddingService(
  gristDoc: GristDoc,
  docStorage: DocStorage,
  dataEngine: DataEngine
): AutoEmbeddingService {
  return new AutoEmbeddingService(gristDoc, docStorage, dataEngine);
}
