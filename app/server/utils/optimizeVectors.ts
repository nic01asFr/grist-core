/**
 * CLI utility for optimizing vector search in Grist documents
 *
 * Usage:
 *   grist-cli vector optimize <doc-path>
 *   grist-cli vector status <doc-path>
 *   grist-cli vector rollback <doc-path>
 */

import {DocStorage} from 'app/server/lib/DocStorage';
import {TrivialDocStorageManager} from 'app/server/lib/IDocStorageManager';
import {VectorOptimizer} from 'app/server/lib/VectorOptimizer';
import * as path from 'path';

/**
 * Optimize vectors in a Grist document
 */
export async function optimizeVectors(docPath: string, options: {
  dryRun?: boolean;
  batchSize?: number;
}): Promise<void> {
  // Use TrivialDocStorageManager - a minimal implementation that works for CLI
  const storageManager = new TrivialDocStorageManager();
  const docStorage = new DocStorage(storageManager, docPath);

  try {
    // Open the document
    console.log(`📂 Opening document: ${docPath}`);
    await docStorage.openFile();

    // Check if already optimized
    const isOptimized = await VectorOptimizer.isOptimized(docStorage);
    if (isOptimized) {
      console.log('ℹ️  Document is already optimized with vec0 tables');

      // Show current stats
      const stats = await VectorOptimizer.getOptimizationStats(docStorage);
      console.log('\n📊 Current optimization status:');
      console.log(`   - vec0 tables: ${stats.vec0Tables}`);
      console.log(`   - Total vectors: ${stats.totalVectors}`);
      console.log(`   - Sync triggers: ${stats.triggers}`);
      console.log(`   - Estimated speedup: ${stats.estimatedSpeedup}`);

      await docStorage.shutdown();
      return;
    }

    // Perform optimization
    console.log('\n🚀 Starting vector optimization...\n');

    const result = await VectorOptimizer.optimizeDocument(docStorage, {
      dryRun: options.dryRun,
      batchSize: options.batchSize,
    });

    // Display results
    console.log('\n' + '='.repeat(60));
    console.log('OPTIMIZATION RESULTS');
    console.log('='.repeat(60));
    console.log(`Document: ${result.docName}`);
    console.log(`Status: ${result.success ? '✅ SUCCESS' : '❌ FAILED'}`);
    console.log(`Duration: ${(result.duration / 1000).toFixed(2)}s`);
    console.log(`Migrations performed: ${result.migrationsPerformed}`);
    console.log(`Total vectors migrated: ${result.totalVectorsMigrated}`);

    if (result.errors.length > 0) {
      console.log(`\n⚠️  Errors encountered:`);
      result.errors.forEach(err => console.log(`   - ${err}`));
    }

    if (result.migrations.length > 0) {
      console.log(`\nDetailed migration results:`);
      result.migrations.forEach(m => {
        const status = m.status === 'completed' ? '✅' :
                       m.status === 'failed' ? '❌' :
                       m.status === 'in_progress' ? '🔄' : '⏸️';
        console.log(`   ${status} ${m.tableName}.${m.columnName}: ${m.migratedRows}/${m.totalRows} vectors`);
      });
    }

    // Show new stats
    if (result.success && result.migrationsPerformed > 0) {
      const stats = await VectorOptimizer.getOptimizationStats(docStorage);
      console.log(`\n📈 Performance improvement:`);
      console.log(`   - Estimated query speedup: ${stats.estimatedSpeedup}`);
    }

    console.log('='.repeat(60) + '\n');

    await docStorage.shutdown();

  } catch (err: any) {
    console.error(`\n❌ Error: ${err.message}`);
    await docStorage.shutdown();
    throw err;
  }
}

/**
 * Show optimization status for a document
 */
export async function showVectorStatus(docPath: string): Promise<void> {
  const storageManager = new TrivialDocStorageManager();
  const docStorage = new DocStorage(storageManager, docPath);

  try {
    console.log(`📂 Opening document: ${docPath}`);
    await docStorage.openFile();

    const isOptimized = await VectorOptimizer.isOptimized(docStorage);
    const stats = await VectorOptimizer.getOptimizationStats(docStorage);

    console.log('\n' + '='.repeat(60));
    console.log('VECTOR OPTIMIZATION STATUS');
    console.log('='.repeat(60));
    console.log(`Document: ${path.basename(docPath)}`);
    console.log(`Optimized: ${isOptimized ? '✅ Yes' : '❌ No'}`);

    if (isOptimized) {
      console.log(`\nvec0 Tables: ${stats.vec0Tables}`);
      console.log(`Total Vectors: ${stats.totalVectors.toLocaleString()}`);
      console.log(`Sync Triggers: ${stats.triggers}`);
      console.log(`Estimated Speedup: ${stats.estimatedSpeedup}`);

      // List vec0 tables
      const db = (docStorage as any)._db;
      const tables = await db.all(`
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name LIKE 'vec_%'
        ORDER BY name
      `);

      if (tables.length > 0) {
        console.log(`\nvec0 Virtual Tables:`);
        for (const table of tables) {
          const count = await db.get(`SELECT COUNT(*) as count FROM "${table.name}"`);
          console.log(`   - ${table.name}: ${count.count.toLocaleString()} vectors`);
        }
      }
    } else {
      console.log('\nℹ️  This document has not been optimized for vector search.');
      console.log('   Run "grist-cli vector optimize <doc-path>" to enable vec0 optimizations.');
    }

    console.log('='.repeat(60) + '\n');

    await docStorage.shutdown();

  } catch (err: any) {
    console.error(`\n❌ Error: ${err.message}`);
    await docStorage.shutdown();
    throw err;
  }
}

/**
 * Rollback vec0 optimizations from a document
 */
export async function rollbackVectorOptimization(docPath: string): Promise<void> {
  const storageManager = new TrivialDocStorageManager();
  const docStorage = new DocStorage(storageManager, docPath);

  try {
    console.log(`📂 Opening document: ${docPath}`);
    await docStorage.openFile();

    const isOptimized = await VectorOptimizer.isOptimized(docStorage);
    if (!isOptimized) {
      console.log('ℹ️  Document is not optimized - nothing to rollback');
      await docStorage.shutdown();
      return;
    }

    console.log('\n🔄 Rolling back vec0 optimizations...\n');

    const removedTables = await VectorOptimizer.rollbackOptimizations(docStorage);

    console.log('\n' + '='.repeat(60));
    console.log('ROLLBACK RESULTS');
    console.log('='.repeat(60));
    console.log(`✅ Successfully removed ${removedTables.length} vec0 tables`);

    if (removedTables.length > 0) {
      console.log(`\nRemoved tables:`);
      removedTables.forEach(table => console.log(`   - ${table}`));
    }

    console.log(`\nℹ️  Document has been reverted to JSON-based vector search.`);
    console.log(`   Original data was not affected.`);
    console.log('='.repeat(60) + '\n');

    await docStorage.shutdown();

  } catch (err: any) {
    console.error(`\n❌ Error: ${err.message}`);
    await docStorage.shutdown();
    throw err;
  }
}
