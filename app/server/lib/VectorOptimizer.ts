/**
 * VectorOptimizer: High-level interface for applying vec0 optimizations to Grist documents
 *
 * This module provides a safe, controlled way to enable sqlite-vec optimizations
 * for existing Grist documents without automatic, unexpected migrations.
 *
 * Usage:
 * 1. Manual optimization via CLI or admin interface
 * 2. Scheduled maintenance tasks
 * 3. Opt-in per-document basis
 *
 * SAFETY:
 * - Never runs automatically on document open
 * - Explicit user/admin action required
 * - All operations are logged and reversible
 * - Original data always preserved
 */

import log from 'app/server/lib/log';
import {DocStorage} from 'app/server/lib/DocStorage';
import {VectorMigration, MigrationStatus, MigrationConfig} from 'app/server/lib/VectorMigration';

/**
 * Optimization result summary
 */
export interface OptimizationResult {
  docName: string;
  success: boolean;
  migrationsPerformed: number;
  totalVectorsMigrated: number;
  errors: string[];
  migrations: MigrationStatus[];
  duration: number;  // milliseconds
}

/**
 * Vector optimizer for Grist documents
 */
export class VectorOptimizer {

  /**
   * Optimize a single Grist document by migrating vectors to vec0
   *
   * This is the main entry point for applying vec0 optimizations.
   * Safe to call multiple times - idempotent operation.
   *
   * @param docStorage - Open DocStorage instance
   * @param config - Migration configuration (optional)
   * @returns Optimization result summary
   */
  public static async optimizeDocument(
    docStorage: DocStorage,
    config?: MigrationConfig
  ): Promise<OptimizationResult> {
    const startTime = Date.now();
    const result: OptimizationResult = {
      docName: docStorage.docName,
      success: false,
      migrationsPerformed: 0,
      totalVectorsMigrated: 0,
      errors: [],
      migrations: [],
      duration: 0,
    };

    try {
      log.info(`🚀 Starting vec0 optimization for document: ${docStorage.docName}`);

      // Create migrator with provided config
      const migrator = new VectorMigration(config);

      // Perform migration using the underlying SQLite database
      const db = (docStorage as any)._db;  // Access private _db member

      if (!db) {
        throw new Error('Document database not available - ensure document is open');
      }

      // Execute migration
      result.migrations = await migrator.migrateAllVectorColumns(db);

      // Calculate summary statistics
      result.migrationsPerformed = result.migrations.filter(m => m.status === 'completed').length;
      result.totalVectorsMigrated = result.migrations.reduce((sum, m) => sum + m.migratedRows, 0);

      // Collect any errors
      result.errors = result.migrations
        .filter(m => m.status === 'failed' && m.error)
        .map(m => `${m.tableName}.${m.columnName}: ${m.error}`);

      result.success = result.migrationsPerformed > 0 || result.migrations.length === 0;

      const duration = Date.now() - startTime;
      result.duration = duration;

      if (result.success) {
        log.info(
          `✅ Optimization completed for ${docStorage.docName}: ` +
          `${result.migrationsPerformed} columns migrated, ` +
          `${result.totalVectorsMigrated} vectors optimized ` +
          `(${(duration / 1000).toFixed(2)}s)`
        );
      } else {
        log.warn(
          `⚠️  Optimization completed with errors for ${docStorage.docName}: ` +
          `${result.errors.length} errors encountered`
        );
      }

      return result;

    } catch (err: any) {
      log.error(`❌ Optimization failed for ${docStorage.docName}: ${err.message}`);
      result.errors.push(err.message);
      result.duration = Date.now() - startTime;
      return result;
    }
  }

  /**
   * Check if a document has vec0 optimizations enabled
   *
   * @param docStorage - Open DocStorage instance
   * @returns True if vec0 tables exist in the document
   */
  public static async isOptimized(docStorage: DocStorage): Promise<boolean> {
    try {
      const db = (docStorage as any)._db;
      if (!db) {
        return false;
      }

      // Check for any vec0 virtual tables
      const result = await db.get(`
        SELECT COUNT(*) as count
        FROM sqlite_master
        WHERE type = 'table' AND name LIKE 'vec_%'
      `);

      return (result?.count || 0) > 0;

    } catch (err: any) {
      log.warn(`Failed to check optimization status: ${err.message}`);
      return false;
    }
  }

  /**
   * Rollback vec0 optimizations for a document
   *
   * Removes all vec0 tables and triggers, reverting to JSON-based vector search.
   * Original data is never affected.
   *
   * @param docStorage - Open DocStorage instance
   * @returns List of vec0 tables that were removed
   */
  public static async rollbackOptimizations(docStorage: DocStorage): Promise<string[]> {
    const removedTables: string[] = [];

    try {
      log.info(`🔄 Rolling back vec0 optimizations for: ${docStorage.docName}`);

      const db = (docStorage as any)._db;
      if (!db) {
        throw new Error('Document database not available');
      }

      // Find all vec0 virtual tables
      const tables = await db.all(`
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name LIKE 'vec_%'
      `);

      if (tables.length === 0) {
        log.info('ℹ️  No vec0 tables found - document not optimized');
        return removedTables;
      }

      // Create migrator for rollback
      const migrator = new VectorMigration();

      // Rollback each vec0 table
      for (const table of tables) {
        await migrator.rollbackMigration(db, table.name);
        removedTables.push(table.name);
      }

      log.info(`✅ Rollback completed: removed ${removedTables.length} vec0 tables`);
      return removedTables;

    } catch (err: any) {
      log.error(`❌ Rollback failed for ${docStorage.docName}: ${err.message}`);
      throw err;
    }
  }

  /**
   * Get optimization statistics for a document
   *
   * @param docStorage - Open DocStorage instance
   * @returns Statistics about vec0 tables and vector data
   */
  public static async getOptimizationStats(docStorage: DocStorage): Promise<{
    vec0Tables: number;
    totalVectors: number;
    triggers: number;
    estimatedSpeedup: string;
  }> {
    try {
      const db = (docStorage as any)._db;
      if (!db) {
        return { vec0Tables: 0, totalVectors: 0, triggers: 0, estimatedSpeedup: 'N/A' };
      }

      // Count vec0 tables
      const tablesResult = await db.get(`
        SELECT COUNT(*) as count
        FROM sqlite_master
        WHERE type = 'table' AND name LIKE 'vec_%'
      `);
      const vec0Tables = tablesResult?.count || 0;

      // Count triggers
      const triggersResult = await db.get(`
        SELECT COUNT(*) as count
        FROM sqlite_master
        WHERE type = 'trigger' AND name LIKE 'sync_%'
      `);
      const triggers = triggersResult?.count || 0;

      // Count total vectors (sum across all vec0 tables)
      let totalVectors = 0;
      if (vec0Tables > 0) {
        const tables = await db.all(`
          SELECT name FROM sqlite_master
          WHERE type = 'table' AND name LIKE 'vec_%'
        `);

        for (const table of tables) {
          const countResult = await db.get(`SELECT COUNT(*) as count FROM "${table.name}"`);
          totalVectors += countResult?.count || 0;
        }
      }

      // Estimate speedup based on vector count
      let estimatedSpeedup = 'N/A';
      if (totalVectors > 0) {
        if (totalVectors < 1000) {
          estimatedSpeedup = '5-10×';
        } else if (totalVectors < 10000) {
          estimatedSpeedup = '10-30×';
        } else {
          estimatedSpeedup = '30-50×';
        }
      }

      return {
        vec0Tables,
        totalVectors,
        triggers,
        estimatedSpeedup,
      };

    } catch (err: any) {
      log.warn(`Failed to get optimization stats: ${err.message}`);
      return { vec0Tables: 0, totalVectors: 0, triggers: 0, estimatedSpeedup: 'N/A' };
    }
  }
}
