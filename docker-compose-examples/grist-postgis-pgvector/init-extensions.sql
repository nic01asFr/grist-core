-- Script d'initialisation PostgreSQL pour Grist spatial
-- Extensions spatiales et vectorielles

-- Extensions de base
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Schéma pour les données spatiales Grist
CREATE SCHEMA IF NOT EXISTS grist_spatial;

-- Table pour les données géospatiales (simulation)
CREATE TABLE IF NOT EXISTS grist_spatial.geometries (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    row_id INTEGER NOT NULL,
    column_name TEXT NOT NULL,
    geometry GEOMETRY,
    srid INTEGER DEFAULT 4326,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(table_name, row_id, column_name)
);

-- Index spatial
CREATE INDEX IF NOT EXISTS idx_geometries_geom ON grist_spatial.geometries 
USING GIST(geometry);

-- Table pour les embeddings (simulation sans pgvector)
CREATE TABLE IF NOT EXISTS grist_spatial.embeddings (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    row_id INTEGER NOT NULL,
    column_name TEXT NOT NULL,
    content TEXT,
    embedding_data TEXT, -- JSON des dimensions d'embedding
    model_name TEXT DEFAULT 'embeddings-small',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(table_name, row_id, column_name)
);

-- Fonctions utilitaires
CREATE OR REPLACE FUNCTION grist_spatial.calculate_distance(
    geom1 GEOMETRY,
    geom2 GEOMETRY
) RETURNS FLOAT AS $$
BEGIN
    RETURN ST_Distance(geom1::geography, geom2::geography);
END;
$$ LANGUAGE plpgsql;

-- Message de confirmation
DO $$ 
BEGIN 
    RAISE NOTICE 'Grist spatial extensions initialized successfully!';
END $$;
