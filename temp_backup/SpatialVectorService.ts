/**
 * Service intégré pour les fonctionnalités spatiales et vectorielles natives dans Grist
 * Intégration PostgreSQL + PostGIS + pgvector + Albert API
 */

import { DataSource } from 'typeorm';
import { HomeDBManager } from 'app/gen-server/lib/HomeDBManager';
import { log } from 'app/server/lib/log';

// Configuration Albert API
interface AlbertConfig {
  apiUrl: string;
  apiToken: string;
  embeddingModel: string;
  dimensions: number;
}

// Types pour les données spatiales
interface GeometryData {
  type: 'Point' | 'Polygon' | 'LineString' | 'MultiPoint' | 'MultiPolygon' | 'MultiLineString';
  coordinates: number[] | number[][] | number[][][];
  srid?: number;
}

interface EmbeddingData {
  content: string;
  embedding: number[];
  modelName: string;
}

interface SimilarityResult {
  tableName: string;
  rowId: number;
  columnName: string;
  content: string;
  similarity: number;
}

export class SpatialVectorService {
  private _dataSource: DataSource | null = null;
  private _albertConfig: AlbertConfig;

  constructor(private _homeDbManager: HomeDBManager) {
    this._albertConfig = {
      apiUrl: process.env.ALBERT_API_URL || 'https://albert.api.etalab.gouv.fr/v1',
      apiToken: process.env.ALBERT_API_TOKEN || 'test-token',
      embeddingModel: process.env.ALBERT_MODEL_EMBEDDING || 'embeddings-small',
      dimensions: parseInt(process.env.EMBEDDING_DIMENSION || '1024')
    };
  }

  /**
   * Initialise le service et vérifie les extensions PostgreSQL
   */
  public async initialize(): Promise<void> {
    try {
      this._dataSource = this._homeDbManager.connection;
      
      if (!this._dataSource) {
        throw new Error('Aucune connexion base de données disponible');
      }

      // Vérifier que nous avons bien PostgreSQL
      const dbType = this._dataSource.options.type;
      if (dbType !== 'postgres') {
        log.warn('SpatialVectorService: PostgreSQL requis pour les fonctionnalités spatiales/vectorielles');
        return;
      }

      // Vérifier les extensions PostGIS et pgvector
      await this._checkExtensions();
      log.info('SpatialVectorService: Initialisé avec succès');

    } catch (error) {
      log.error('SpatialVectorService: Erreur d\'initialisation', error);
      throw error;
    }
  }

  /**
   * Vérification des extensions PostgreSQL requises
   */
  private async _checkExtensions(): Promise<void> {
    const extensions = await this._dataSource!.query(`
      SELECT extname, extversion 
      FROM pg_extension 
      WHERE extname IN ('postgis', 'postgis_topology', 'vector')
    `);

    const extensionNames = extensions.map((ext: any) => ext.extname);
    
    if (!extensionNames.includes('postgis')) {
      throw new Error('Extension PostGIS non trouvée');
    }
    if (!extensionNames.includes('vector')) {
      throw new Error('Extension pgvector non trouvée');
    }

    log.info(`SpatialVectorService: Extensions validées:`, extensions);
  }

  /**
   * Génère un embedding pour un texte via Albert API ou fallback
   */
  public async generateEmbedding(text: string): Promise<number[]> {
    if (!text || text.trim().length === 0) {
      throw new Error('Texte vide pour génération d\'embedding');
    }

    // Mode simulation si token de test
    if (this._albertConfig.apiToken === 'test-token') {
      return this._generateMockEmbedding(text);
    }

    try {
      // Appel Albert API
      const response = await fetch(`${this._albertConfig.apiUrl}/embeddings`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this._albertConfig.apiToken}`,
          'Content-Type': 'application/json',
          'User-Agent': 'Grist-Native-Integration/1.0'
        },
        body: JSON.stringify({
          input: text,
          model: this._albertConfig.embeddingModel
        })
      });

      if (!response.ok) {
        log.warn(`Albert API erreur ${response.status}, fallback simulation`);
        return this._generateMockEmbedding(text);
      }

      const data = await response.json();
      return data.data[0].embedding;

    } catch (error) {
      log.warn('Albert API indisponible, fallback simulation:', error);
      return this._generateMockEmbedding(text);
    }
  }

  /**
   * Génération d'embedding simulé pour développement/test
   */
  private _generateMockEmbedding(text: string): number[] {
    const embedding = new Array(this._albertConfig.dimensions);
    const seed = this._hashString(text);
    
    for (let i = 0; i < this._albertConfig.dimensions; i++) {
      // Génération déterministe basée sur le texte
      embedding[i] = Math.sin(seed * 0.01 + i * 0.1) * 0.1;
    }
    
    return embedding;
  }

  /**
   * Hash simple pour génération déterministe
   */
  private _hashString(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Conversion 32bit
    }
    return Math.abs(hash);
  }

  /**
   * Stocke un embedding dans la base de données
   */
  public async storeEmbedding(
    tableName: string, 
    rowId: number, 
    columnName: string, 
    content: string
  ): Promise<void> {
    const embedding = await this.generateEmbedding(content);
    
    await this._dataSource!.query(`
      INSERT INTO grist_spatial.embeddings (table_name, row_id, column_name, content, embedding, model_name)
      VALUES ($1, $2, $3, $4, $5, $6)
      ON CONFLICT (table_name, row_id, column_name) 
      DO UPDATE SET 
        content = EXCLUDED.content,
        embedding = EXCLUDED.embedding,
        model_name = EXCLUDED.model_name,
        created_at = NOW()
    `, [tableName, rowId, columnName, content, JSON.stringify(embedding), this._albertConfig.embeddingModel]);
  }

  /**
   * Recherche de similarité vectorielle
   */
  public async searchSimilar(
    queryText: string, 
    threshold: number = 0.7, 
    limit: number = 10
  ): Promise<SimilarityResult[]> {
    const queryEmbedding = await this.generateEmbedding(queryText);
    
    const results = await this._dataSource!.query(`
      SELECT table_name, row_id, column_name, content,
             (1 - (embedding <-> $1::vector))::float as similarity
      FROM grist_spatial.embeddings
      WHERE (1 - (embedding <-> $1::vector)) >= $2
      ORDER BY embedding <-> $1::vector
      LIMIT $3
    `, [JSON.stringify(queryEmbedding), threshold, limit]);

    return results.map((row: any) => ({
      tableName: row.table_name,
      rowId: row.row_id,
      columnName: row.column_name,
      content: row.content,
      similarity: row.similarity
    }));
  }

  /**
   * Stocke une géométrie spatiale
   */
  public async storeGeometry(
    tableName: string,
    rowId: number,
    columnName: string,
    geometry: GeometryData
  ): Promise<void> {
    const wkt = this._geometryToWKT(geometry);
    const srid = geometry.srid || 4326;

    await this._dataSource!.query(`
      INSERT INTO grist_spatial.geometries (table_name, row_id, column_name, geometry, srid)
      VALUES ($1, $2, $3, ST_GeomFromText($4, $5), $5)
      ON CONFLICT (table_name, row_id, column_name)
      DO UPDATE SET 
        geometry = EXCLUDED.geometry,
        srid = EXCLUDED.srid,
        created_at = NOW()
    `, [tableName, rowId, columnName, wkt, srid]);
  }

  /**
   * Calcul de distance spatiale entre deux géométries
   */
  public async calculateDistance(
    tableName1: string, rowId1: number, columnName1: string,
    tableName2: string, rowId2: number, columnName2: string
  ): Promise<number> {
    const result = await this._dataSource!.query(`
      SELECT ST_Distance(g1.geometry::geography, g2.geometry::geography) as distance
      FROM grist_spatial.geometries g1, grist_spatial.geometries g2
      WHERE g1.table_name = $1 AND g1.row_id = $2 AND g1.column_name = $3
        AND g2.table_name = $4 AND g2.row_id = $5 AND g2.column_name = $6
    `, [tableName1, rowId1, columnName1, tableName2, rowId2, columnName2]);

    return result.length > 0 ? result[0].distance : null;
  }

  /**
   * Recherche spatiale par proximité
   */
  public async searchNearby(
    centerGeometry: GeometryData,
    radiusMeters: number,
    limit: number = 10
  ): Promise<any[]> {
    const wkt = this._geometryToWKT(centerGeometry);
    const srid = centerGeometry.srid || 4326;

    return await this._dataSource!.query(`
      SELECT table_name, row_id, column_name,
             ST_Distance(geometry::geography, ST_GeomFromText($1, $2)::geography) as distance
      FROM grist_spatial.geometries
      WHERE ST_DWithin(geometry::geography, ST_GeomFromText($1, $2)::geography, $3)
      ORDER BY distance
      LIMIT $4
    `, [wkt, srid, radiusMeters, limit]);
  }

  /**
   * Conversion d'une géométrie en WKT
   */
  private _geometryToWKT(geometry: GeometryData): string {
    const { type, coordinates } = geometry;
    
    switch (type) {
      case 'Point':
        return `POINT(${(coordinates as number[]).join(' ')})`;
      case 'Polygon':
        const rings = (coordinates as number[][][]).map(ring => 
          '(' + ring.map(coord => coord.join(' ')).join(',') + ')'
        ).join(',');
        return `POLYGON(${rings})`;
      case 'LineString':
        const lineCoords = (coordinates as number[][]).map(coord => coord.join(' ')).join(',');
        return `LINESTRING(${lineCoords})`;
      default:
        throw new Error(`Type de géométrie non supporté: ${type}`);
    }
  }

  /**
   * Obtient les statistiques du service
   */
  public async getStats(): Promise<{embeddings: number, geometries: number}> {
    if (!this._dataSource) {
      return { embeddings: 0, geometries: 0 };
    }

    const embeddingCount = await this._dataSource.query(`
      SELECT COUNT(*) as count FROM grist_spatial.embeddings
    `);
    
    const geometryCount = await this._dataSource.query(`
      SELECT COUNT(*) as count FROM grist_spatial.geometries  
    `);

    return {
      embeddings: parseInt(embeddingCount[0].count),
      geometries: parseInt(geometryCount[0].count)
    };
  }
}

// Export singleton
export const spatialVectorService = new SpatialVectorService(HomeDBManager.getInstance());