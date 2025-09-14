import {ApiError} from 'app/common/ApiError';
import {BaseAPI, IOptions} from 'app/common/BaseAPI';
import {ActiveDoc} from 'app/server/lib/ActiveDoc';
import {Request, Response} from 'express';
import {ServerQuery} from 'app/common/ActiveDocAPI';
import {makeExceptionalDocSession} from 'app/server/lib/DocSession';

/**
 * API pour la recherche sémantique dans les documents Grist
 * 
 * Endpoints fournis :
 * - POST /docs/{docId}/semantic-search : Recherche par similarité vectorielle
 * - POST /docs/{docId}/generate-embeddings : Génération d'embeddings pour du texte
 * - GET /docs/{docId}/semantic-clusters : Clustering sémantique des données
 * - POST /docs/{docId}/semantic-recommend : Recommandations basées sur similarité
 */

export interface SemanticSearchOptions {
  query: string;                    // Texte de recherche
  limit?: number;                   // Nombre de résultats (défaut: 10)
  threshold?: number;               // Seuil de similarité (défaut: 0.3)
  tables?: string[];               // Tables à inclure (défaut: toutes)
  fields?: string[];               // Champs à inclure dans la recherche
  boost_recent?: boolean;           // Booster les entrées récentes
  include_content?: boolean;        // Inclure le contenu dans les résultats
}

export interface SemanticSearchResult {
  table: string;
  rowId: number;
  similarity: number;
  content: string;
  fields: Record<string, any>;
  embedding?: number[];
}

export interface ClusterResult {
  cluster_id: number;
  size: number;
  center: number[];
  representative_docs: SemanticSearchResult[];
  topic_words?: string[];
}

/**
 * Service de génération d'embeddings
 */
export class EmbeddingService {
  private static instance: EmbeddingService;
  // Service singleton pour génération d'embeddings

  static getInstance(): EmbeddingService {
    if (!EmbeddingService.instance) {
      EmbeddingService.instance = new EmbeddingService();
    }
    return EmbeddingService.instance;
  }

  /**
   * Génère un embedding pour un texte donné
   */
  async generateEmbedding(text: string, model = 'albert'): Promise<number[]> {
    if (!text || text.trim().length === 0) {
      throw new ApiError('Text cannot be empty', 400);
    }

    try {
      switch (model) {
        case 'sentence-transformers':
          return await this.generateLocalEmbedding(text);
        case 'openai':
          return await this.generateOpenAIEmbedding(text);
        case 'albert':
          return await this.generateAlbertEmbedding(text);
        default:
          throw new ApiError(`Unknown embedding model: ${model}`, 400);
      }
    } catch (error) {
      console.error(`SemanticSearchApi: Erreur génération embedding: ${error.message}`, error);
      throw new ApiError('Failed to generate embedding', 500);
    }
  }

  /**
   * Génère des embeddings par batch pour optimiser les performances
   */
  async generateBatchEmbeddings(texts: string[], model = 'sentence-transformers'): Promise<number[][]> {
    const batchSize = 100; // Traiter par chunks
    const results: number[][] = [];

    for (let i = 0; i < texts.length; i += batchSize) {
      const batch = texts.slice(i, i + batchSize);
      const batchResults = await Promise.all(
        batch.map(text => this.generateEmbedding(text, model))
      );
      results.push(...batchResults);
    }

    return results;
  }

  /**
   * Génère un embedding local avec sentence-transformers (simulation)
   * En production, ceci appellerait un service Python/transformers réel
   */
  private async generateLocalEmbedding(text: string): Promise<number[]> {
    // SIMULATION - En production, ceci appellerait un service ML réel
    // Exemple avec sentence-transformers via API Python :
    // const response = await fetch('http://ml-service:8000/embed', {
    //   method: 'POST',
    //   body: JSON.stringify({ text, model: 'all-MiniLM-L6-v2' })
    // });
    
    // Pour la démonstration, génération d'un vecteur pseudo-aléatoire déterministe
    // Utiliser la dimension Albert par défaut ou sentence-transformers
    const dimension = parseInt(process.env.EMBEDDING_DIMENSION || '384');
    const embedding: number[] = [];
    
    // Hash simple du texte pour générer un vecteur déterministe
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
      hash = ((hash << 5) - hash + text.charCodeAt(i)) & 0xffffffff;
    }
    
    // Génération pseudo-aléatoire basée sur le hash
    const seed = Math.abs(hash);
    for (let i = 0; i < dimension; i++) {
      const value = Math.sin(seed + i) * Math.cos(seed * i);
      embedding.push(value);
    }
    
    // Normaliser le vecteur (important pour la similarité cosinus)
    const norm = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
    return embedding.map(val => val / norm);
  }

  /**
   * Génère un embedding via l'API OpenAI
   */
  private async generateOpenAIEmbedding(text: string): Promise<number[]> {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      throw new ApiError('OpenAI API key not configured', 500);
    }

    // Simulation d'appel OpenAI - remplacer par vraie API
    // const response = await fetch('https://api.openai.com/v1/embeddings', {
    //   method: 'POST',
    //   headers: {
    //     'Authorization': `Bearer ${apiKey}`,
    //     'Content-Type': 'application/json'
    //   },
    //   body: JSON.stringify({
    //     input: text,
    //     model: 'text-embedding-ada-002'
    //   })
    // });

    // Pour la démonstration, utiliser l'embedding local
    return this.generateLocalEmbedding(text);
  }

  /**
   * Génère un embedding via l'API Albert (Albert API Etalab)
   */
  private async generateAlbertEmbedding(text: string): Promise<number[]> {
    const apiUrl = process.env.ALBERT_API_URL;
    const apiToken = process.env.ALBERT_API_TOKEN;
    const embeddingModel = process.env.ALBERT_MODEL_EMBEDDING || 'embeddings-small';
    const embeddingDimension = parseInt(process.env.EMBEDDING_DIMENSION || '1024');

    if (!apiUrl || !apiToken) {
      console.warn('SemanticSearchApi: Albert API non configurée, utilisation embedding local');
      return this.generateLocalEmbedding(text);
    }

    try {
      // Appel réel à l'API Albert compatible OpenAI
      const response = await fetch(`${apiUrl}/embeddings`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          input: text,
          model: embeddingModel
        })
      });

      if (!response.ok) {
        throw new Error(`Albert API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      // Format de réponse compatible OpenAI
      if (data.data && data.data[0] && data.data[0].embedding) {
        const embedding = data.data[0].embedding;
        
        // Vérifier la dimension
        if (embedding.length !== embeddingDimension) {
          console.warn(`SemanticSearchApi: Dimension mismatch: expected ${embeddingDimension}, got ${embedding.length}`);
        }
        
        return embedding;
      }

      throw new Error('Invalid response format from Albert API');

    } catch (error) {
      console.error(`SemanticSearchApi: Erreur Albert API: ${error.message}`, error);
      
      // Fallback vers embedding local en cas d'erreur
      console.warn('SemanticSearchApi: Fallback vers embedding local');
      return this.generateLocalEmbedding(text);
    }
  }
}

/**
 * API de recherche sémantique
 */
export class SemanticSearchApi extends BaseAPI {
  private embeddingService: EmbeddingService;

  constructor(private activeDoc: ActiveDoc, opts: IOptions) {
    super(opts);
    this.embeddingService = EmbeddingService.getInstance();
  }

  /**
   * POST /docs/{docId}/semantic-search
   * Recherche sémantique dans le document
   */
  async semanticSearch(req: Request, res: Response): Promise<void> {
    try {
      const options: SemanticSearchOptions = {
        limit: 10,
        threshold: 0.3,
        include_content: true,
        ...req.body
      };

      if (!options.query) {
        throw new ApiError('Query parameter is required', 400);
      }

      console.info(`SemanticSearchApi: Recherche sémantique: "${options.query}"`);

      // Générer l'embedding pour la requête
      const queryEmbedding = await this.embeddingService.generateEmbedding(options.query);

      // Chercher dans toutes les tables avec colonnes Vector
      const results = await this.searchInVectorColumns(queryEmbedding, options);

      res.json({
        query: options.query,
        results,
        total: results.length,
        options
      });

    } catch (error) {
      console.error(`SemanticSearchApi: Erreur recherche sémantique: ${error.message}`, error);
      
      if (error instanceof ApiError) {
        res.status(error.status).json({ error: error.message });
      } else {
        res.status(500).json({ error: 'Internal server error' });
      }
    }
  }

  /**
   * POST /docs/{docId}/generate-embeddings
   * Génère des embeddings pour du texte
   */
  async generateEmbeddings(req: Request, res: Response): Promise<void> {
    try {
      const { texts, model = 'sentence-transformers' } = req.body;

      if (!texts || !Array.isArray(texts)) {
        throw new ApiError('texts parameter must be an array', 400);
      }

      const embeddings = await this.embeddingService.generateBatchEmbeddings(texts, model);

      res.json({
        embeddings,
        model,
        dimension: embeddings[0]?.length || 0,
        count: embeddings.length
      });

    } catch (error) {
      console.error(`SemanticSearchApi: Erreur génération embeddings: ${error.message}`, error);
      
      if (error instanceof ApiError) {
        res.status(error.status).json({ error: error.message });
      } else {
        res.status(500).json({ error: 'Internal server error' });
      }
    }
  }

  /**
   * GET /docs/{docId}/semantic-clusters
   * Clustering sémantique des données
   */
  async getSemanticClusters(req: Request, res: Response): Promise<void> {
    try {
      const numClusters = parseInt(req.query.clusters as string) || 5;
      const table = req.query.table as string;

      if (!table) {
        throw new ApiError('table parameter is required', 400);
      }

      const clusters = await this.performClustering(table, numClusters);

      res.json({
        clusters,
        table,
        num_clusters: numClusters
      });

    } catch (error) {
      console.error(`SemanticSearchApi: Erreur clustering sémantique: ${error.message}`, error);
      
      if (error instanceof ApiError) {
        res.status(error.status).json({ error: error.message });
      } else {
        res.status(500).json({ error: 'Internal server error' });
      }
    }
  }

  /**
   * POST /docs/{docId}/semantic-recommend  
   * Recommandations basées sur similarité
   */
  async getRecommendations(req: Request, res: Response): Promise<void> {
    try {
      const { table, rowId, limit = 5 } = req.body;

      if (!table || !rowId) {
        throw new ApiError('table and rowId parameters are required', 400);
      }

      const recommendations = await this.findSimilarRecords(table, rowId, limit);

      res.json({
        recommendations,
        table,
        source_row: rowId,
        limit
      });

    } catch (error) {
      console.error(`SemanticSearchApi: Erreur recommandations: ${error.message}`, error);
      
      if (error instanceof ApiError) {
        res.status(error.status).json({ error: error.message });
      } else {
        res.status(500).json({ error: 'Internal server error' });
      }
    }
  }

  /**
   * Recherche dans les colonnes Vector de toutes les tables
   */
  private async searchInVectorColumns(
    queryEmbedding: number[], 
    options: SemanticSearchOptions
  ): Promise<SemanticSearchResult[]> {
    const results: SemanticSearchResult[] = [];

    // Obtenir les données du document
    const docData = this.activeDoc.docData;
    if (!docData) {
      throw new ApiError('Document not loaded', 500);
    }

    // Obtenir les tables avec colonnes Vector (simulation)
    const tables = docData.getMetaTable('_grist_Tables').getRecords();
    
    for (const tableRec of tables) {
      const tableId = tableRec.tableId as string;
      if (options.tables && !options.tables.includes(tableId)) {
        continue;
      }

      // Pour simulation, chercher dans toutes les tables (en production, filtrer par colonnes Vector)
      try {
        const tableResults = await this.searchInTable(
          tableId,
          'content', // Colonne texte par défaut
          queryEmbedding,
          options
        );
        results.push(...tableResults);
      } catch (error) {
        console.warn(`SemanticSearchApi: Erreur recherche dans ${tableId}: ${error.message}`);
      }
    }

    // Trier par similarité décroissante
    results.sort((a, b) => b.similarity - a.similarity);

    // Appliquer la limite
    return results.slice(0, options.limit);
  }

  /**
   * Recherche dans une table/colonne spécifique
   */
  private async searchInTable(
    tableId: string,
    vectorColumnId: string,
    queryEmbedding: number[],
    options: SemanticSearchOptions
  ): Promise<SemanticSearchResult[]> {
    
    try {
      // Simulation de recherche sémantique - en production, utiliser vraies requêtes vectorielles
      const query: ServerQuery = {
        tableId,
        filters: {},
        limit: options.limit
      };
      
      const docSession = makeExceptionalDocSession('system'); // Session système
      const table = await this.activeDoc.fetchQuery(docSession, query, false);
      const rows = table.tableData[2] || []; // [2] contient les données des lignes
      
      // Simulation de similarité basée sur le hash du texte
      return rows.slice(0, options.limit).map((row: any, index: number) => ({
        table: tableId,
        rowId: row.id || index,
        similarity: Math.max(0.1, Math.random()), // Simulation
        content: this.extractContentFromRow(row, options.fields),
        fields: this.filterFields(row, options.fields),
        embedding: options.include_content ? queryEmbedding : undefined
      }));

    } catch (error) {
      console.error(`SemanticSearchApi: Erreur recherche sémantique: ${error.message}`, error);
      return [];
    }
  }

  /**
   * Extrait le contenu textuel d'une ligne pour l'affichage
   */
  private extractContentFromRow(row: any, fields?: string[]): string {
    const textFields = fields || Object.keys(row).filter(key => 
      key !== 'id' && typeof row[key] === 'string' && row[key].length > 0
    );

    return textFields
      .map(field => row[field])
      .filter(value => value && typeof value === 'string')
      .join(' | ')
      .substring(0, 500); // Limiter la taille
  }

  /**
   * Filtre les champs à retourner dans le résultat
   */
  private filterFields(row: any, fields?: string[]): Record<string, any> {
    if (!fields) {
      // Retourner tous les champs sauf les embeddings
      const filtered: Record<string, any> = {};
      for (const [key, value] of Object.entries(row)) {
        if (key !== 'id' && !Array.isArray(value)) {
          filtered[key] = value;
        }
      }
      return filtered;
    }

    const filtered: Record<string, any> = {};
    for (const field of fields) {
      if (row[field] !== undefined) {
        filtered[field] = row[field];
      }
    }
    return filtered;
  }

  /**
   * Clustering sémantique des données d'une table
   */
  private async performClustering(tableId: string, numClusters: number): Promise<ClusterResult[]> {
    // Implémentation simplifiée - en production, utiliser un vrai algorithme de clustering
    // comme k-means ou DBSCAN
    
    // Pour la démonstration, retourner des clusters fictifs
    const clusters: ClusterResult[] = [];
    
    for (let i = 0; i < numClusters; i++) {
      clusters.push({
        cluster_id: i,
        size: Math.floor(Math.random() * 20) + 5,
        center: Array.from({ length: 384 }, () => Math.random() - 0.5),
        representative_docs: [],
        topic_words: [`topic_${i}_word1`, `topic_${i}_word2`, `topic_${i}_word3`]
      });
    }

    return clusters;
  }

  /**
   * Trouve les enregistrements similaires à un enregistrement donné
   */
  private async findSimilarRecords(
    tableId: string, 
    rowId: number, 
    limit: number
  ): Promise<SemanticSearchResult[]> {
    
    // Simulation de recherche de similarité
    const query: ServerQuery = {
      tableId,
      filters: {},
      limit: limit + 1 // +1 pour exclure la ligne source
    };
    
    try {
      const docSession = makeExceptionalDocSession('system'); // Session système
      const table = await this.activeDoc.fetchQuery(docSession, query, false);
      const rows = table.tableData[2] || []; // [2] contient les données des lignes
      
      // Filtrer la ligne source et simuler la similarité
      const similarRows = rows
        .filter((row: any) => row.id !== rowId)
        .slice(0, limit)
        .map((row: any, index: number) => ({
          table: tableId,
          rowId: row.id || index,
          similarity: Math.max(0.1, Math.random()),
          content: this.extractContentFromRow(row, []),
          fields: this.filterFields(row, []),
        }));
      
      return similarRows;
    } catch (error) {
      console.error(`SemanticSearchApi: Erreur recherche similaire: ${error.message}`, error);
      throw new ApiError('Failed to find similar records', 500);
    }
  }
}
