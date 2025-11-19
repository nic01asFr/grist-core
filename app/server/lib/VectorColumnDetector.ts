/**
 * VectorColumnDetector: Automatic detection of vector embedding columns in Grist tables
 *
 * SAFETY GUARANTEE: This module is READ-ONLY. It only analyzes existing data structures
 * and never modifies any user data or table schemas.
 *
 * Purpose:
 * - Identify columns containing vector embeddings (JSON arrays of numbers)
 * - Determine embedding dimensions and data types
 * - Provide metadata for creating optimized vec0 virtual tables
 *
 * Detection criteria:
 * - Column contains JSON array strings or native arrays
 * - Arrays contain numeric values (floats/integers)
 * - Consistent dimensions across multiple records
 * - Common naming patterns: *embedding*, *vector*, *emb*
 */

import log from 'app/server/lib/log';
import {MinDB} from 'app/server/lib/SqliteCommon';

/**
 * Metadata about a detected vector column
 */
export interface VectorColumnInfo {
  tableName: string;
  columnName: string;
  dimension: number;          // Vector dimensionality (e.g., 1024 for Albert embeddings)
  sampleCount: number;        // Number of non-null samples analyzed
  storageFormat: 'json_string' | 'json_array';  // How vectors are currently stored
  confidence: number;         // 0-1 confidence score that this is a vector column
  vec0TableName?: string;     // Suggested name for vec0 virtual table
}

/**
 * Configuration for vector column detection
 */
export interface DetectionConfig {
  maxSamplesToAnalyze?: number;      // Max records to sample per column (default: 100)
  minConfidence?: number;             // Minimum confidence to report column (default: 0.7)
  minDimension?: number;              // Minimum vector dimension (default: 2)
  maxDimension?: number;              // Maximum vector dimension (default: 4096)
  namePatterns?: RegExp[];            // Column name patterns to prioritize
}

const DEFAULT_CONFIG: Required<DetectionConfig> = {
  maxSamplesToAnalyze: 100,
  minConfidence: 0.7,
  minDimension: 2,
  maxDimension: 4096,
  namePatterns: [
    /embedding/i,
    /vector/i,
    /emb/i,
    /_vec$/i,
  ],
};

/**
 * Detect vector columns in a Grist database
 */
export class VectorColumnDetector {
  private config: Required<DetectionConfig>;

  constructor(config?: DetectionConfig) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Detect all vector columns in the database
   *
   * SAFETY: Read-only operation, no data modification
   */
  public async detectVectorColumns(db: MinDB): Promise<VectorColumnInfo[]> {
    const vectorColumns: VectorColumnInfo[] = [];

    try {
      // Get all user tables (exclude system tables)
      const tables = await this.getUserTables(db);

      for (const tableName of tables) {
        const columns = await this.getTableColumns(db, tableName);

        for (const columnName of columns) {
          const vectorInfo = await this.analyzeColumn(db, tableName, columnName);

          if (vectorInfo && vectorInfo.confidence >= this.config.minConfidence) {
            vectorColumns.push(vectorInfo);
            log.info(
              `✅ Vector column detected: ${tableName}.${columnName} ` +
              `(${vectorInfo.dimension}D, ${vectorInfo.sampleCount} samples, ` +
              `confidence: ${(vectorInfo.confidence * 100).toFixed(0)}%)`
            );
          }
        }
      }

      return vectorColumns;
    } catch (err: any) {
      log.error(`Error detecting vector columns: ${err.message}`);
      return [];
    }
  }

  /**
   * Get list of user tables (exclude Grist system tables)
   */
  private async getUserTables(db: MinDB): Promise<string[]> {
    const rows = await db.all(`
      SELECT name FROM sqlite_master
      WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        AND name NOT LIKE '_grist%'
        AND name NOT LIKE 'vec_%'
      ORDER BY name
    `);

    return rows.map(row => row.name as string);
  }

  /**
   * Get column names for a table
   */
  private async getTableColumns(db: MinDB, tableName: string): Promise<string[]> {
    const rows = await db.all(`PRAGMA table_info("${tableName}")`);
    return rows.map(row => row.name as string);
  }

  /**
   * Analyze a single column to determine if it contains vectors
   *
   * SAFETY: Only reads data, never writes
   */
  private async analyzeColumn(
    db: MinDB,
    tableName: string,
    columnName: string
  ): Promise<VectorColumnInfo | null> {
    try {
      // Sample non-null values from the column
      const samples = await db.all(`
        SELECT "${columnName}" as value
        FROM "${tableName}"
        WHERE "${columnName}" IS NOT NULL
          AND "${columnName}" != ''
        LIMIT ${this.config.maxSamplesToAnalyze}
      `);

      if (samples.length === 0) {
        return null;  // No data to analyze
      }

      // Analyze samples to determine if they're vectors
      const analysis = this.analyzeSamples(samples.map(s => s.value));

      if (!analysis) {
        return null;  // Not a vector column
      }

      // Calculate confidence based on multiple factors
      const nameBonus = this.matchesNamePattern(columnName) ? 0.2 : 0.0;
      const consistency = analysis.consistentDimensions ? 0.3 : 0.0;
      const validRange = this.isValidDimension(analysis.dimension) ? 0.3 : 0.0;
      const sampleSize = Math.min(samples.length / this.config.maxSamplesToAnalyze, 1.0) * 0.2;

      const confidence = nameBonus + consistency + validRange + sampleSize;

      if (confidence < this.config.minConfidence) {
        return null;
      }

      return {
        tableName,
        columnName,
        dimension: analysis.dimension,
        sampleCount: samples.length,
        storageFormat: analysis.format,
        confidence: Math.min(confidence, 1.0),
        vec0TableName: `vec_${tableName}_${columnName}`,
      };

    } catch (err: any) {
      // Silently ignore analysis errors (column might not be text-based, etc.)
      return null;
    }
  }

  /**
   * Analyze sample values to extract vector characteristics
   */
  private analyzeSamples(values: any[]): {
    dimension: number;
    format: 'json_string' | 'json_array';
    consistentDimensions: boolean;
  } | null {
    const parsedVectors: number[][] = [];

    for (const value of values) {
      try {
        let vector: number[];

        // Try parsing as JSON string
        if (typeof value === 'string') {
          const parsed = JSON.parse(value);
          if (Array.isArray(parsed) && parsed.every(v => typeof v === 'number')) {
            vector = parsed;
          } else {
            continue;  // Not a vector
          }
        }
        // Already an array
        else if (Array.isArray(value) && value.every(v => typeof v === 'number')) {
          vector = value;
        } else {
          continue;  // Not a vector
        }

        parsedVectors.push(vector);

      } catch {
        // Parsing failed, not a valid vector
        continue;
      }
    }

    // Need at least 30% of samples to be valid vectors
    if (parsedVectors.length < values.length * 0.3) {
      return null;
    }

    // Check dimension consistency
    const dimensions = parsedVectors.map(v => v.length);
    const uniqueDimensions = new Set(dimensions);

    if (uniqueDimensions.size !== 1) {
      return null;  // Inconsistent dimensions
    }

    const dimension = dimensions[0];

    // Determine storage format (check first value)
    const format = typeof values[0] === 'string' ? 'json_string' : 'json_array';

    return {
      dimension,
      format,
      consistentDimensions: true,
    };
  }

  /**
   * Check if column name matches common vector patterns
   */
  private matchesNamePattern(columnName: string): boolean {
    return this.config.namePatterns.some(pattern => pattern.test(columnName));
  }

  /**
   * Check if dimension is within valid range
   */
  private isValidDimension(dimension: number): boolean {
    return dimension >= this.config.minDimension && dimension <= this.config.maxDimension;
  }

  /**
   * Generate recommended vec0 table name
   */
  public static generateVec0TableName(tableName: string, columnName: string): string {
    // Sanitize names to avoid SQL injection and special characters
    const sanitize = (name: string) =>
      name.replace(/[^a-zA-Z0-9_]/g, '_').substring(0, 50);

    return `vec_${sanitize(tableName)}_${sanitize(columnName)}`;
  }
}
