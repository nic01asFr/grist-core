import * as sqlUtils from "app/gen-server/sqlUtils";
import {MigrationInterface, QueryRunner} from "typeorm";

/**
 * Migration to install PostgreSQL extensions for spatial and vector data support.
 * This migration installs:
 * - PostGIS extension for spatial/geometry data support
 * - pg_vector extension for vector embeddings support
 */
export class PostgresExtensions1750000000000 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    const dbType = queryRunner.connection.driver.options.type;
    
    // Only apply to PostgreSQL databases
    if (dbType !== 'postgres') {
      console.log('Skipping PostgreSQL extensions migration for non-PostgreSQL database');
      return;
    }

    try {
      // Install PostGIS extension
      console.log('Installing PostGIS extension...');
      await queryRunner.query('CREATE EXTENSION IF NOT EXISTS postgis');
      console.log('PostGIS extension installed successfully');
      
      // Install pg_vector extension
      console.log('Installing pg_vector extension...');
      await queryRunner.query('CREATE EXTENSION IF NOT EXISTS vector');
      console.log('pg_vector extension installed successfully');
      
      // Verify extensions are installed
      const extensions = await queryRunner.query(`
        SELECT extname FROM pg_extension 
        WHERE extname IN ('postgis', 'vector')
        ORDER BY extname
      `);
      
      console.log('Installed extensions:', extensions.map((ext: any) => ext.extname));
      
    } catch (error) {
      console.error('Error installing PostgreSQL extensions:', error);
      
      // Check if it's a permissions error
      if (error.message.includes('permission denied') || 
          error.message.includes('must be owner of database')) {
        console.error(`
Migration failed: Insufficient database permissions to install extensions.
Please ensure the database user has SUPERUSER privileges or install extensions manually:

  CREATE EXTENSION IF NOT EXISTS postgis;
  CREATE EXTENSION IF NOT EXISTS vector;

Then re-run the migration.
        `);
      }
      
      // Check if extensions are not available
      if (error.message.includes('could not open extension control file')) {
        console.error(`
Migration failed: Extensions not available.
Please install the required PostgreSQL extensions on your system:

For PostGIS:
  - Ubuntu/Debian: apt-get install postgresql-postgis
  - RHEL/CentOS: yum install postgis
  - macOS: brew install postgis

For pg_vector:
  - Follow installation instructions at: https://github.com/pgvector/pgvector

Then re-run the migration.
        `);
      }
      
      throw error;
    }
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    const dbType = queryRunner.connection.driver.options.type;
    
    // Only apply to PostgreSQL databases
    if (dbType !== 'postgres') {
      return;
    }

    try {
      console.log('Removing PostgreSQL extensions...');
      
      // Note: We use CASCADE to remove any dependent objects
      // Be careful with this in production!
      await queryRunner.query('DROP EXTENSION IF EXISTS vector CASCADE');
      await queryRunner.query('DROP EXTENSION IF EXISTS postgis CASCADE');
      
      console.log('PostgreSQL extensions removed successfully');
    } catch (error) {
      console.error('Error removing PostgreSQL extensions:', error);
      throw error;
    }
  }
}
