-- Script d'initialisation PostgreSQL avec PostGIS et pgvector
-- Exécuté au démarrage du container PostgreSQL

-- Créer les extensions spatiales et vectorielles
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- Vérifier les extensions installées
SELECT name, default_version, installed_version 
FROM pg_available_extensions 
WHERE name IN ('postgis', 'vector');

-- Créer un schema pour les données spatiales/vectorielles
CREATE SCHEMA IF NOT EXISTS spatial_data;

-- Table exemple pour tester les fonctionnalités spatiales
CREATE TABLE IF NOT EXISTS spatial_data.test_locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    geometry GEOMETRY(Point, 4326),
    embedding vector(1024),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index spatial pour les performances
CREATE INDEX IF NOT EXISTS idx_test_locations_geom ON spatial_data.test_locations USING GIST (geometry);
CREATE INDEX IF NOT EXISTS idx_test_locations_embedding ON spatial_data.test_locations USING ivfflat (embedding vector_cosine_ops);

-- Insérer des données de test
INSERT INTO spatial_data.test_locations (name, description, geometry, embedding) 
VALUES 
    ('Tour Eiffel', 'Monument emblématique de Paris', ST_SetSRID(ST_MakePoint(2.2945, 48.8584), 4326), '[0.1, 0.2, 0.3]'::vector),
    ('Notre-Dame', 'Cathédrale historique de Paris', ST_SetSRID(ST_MakePoint(2.3490, 48.8530), 4326), '[0.4, 0.5, 0.6]'::vector),
    ('Arc de Triomphe', 'Monument aux Champs-Élysées', ST_SetSRID(ST_MakePoint(2.2950, 48.8738), 4326), '[0.7, 0.8, 0.9]'::vector)
ON CONFLICT DO NOTHING;

-- Fonction PL/pgSQL pour calculer la distance vectorielle
CREATE OR REPLACE FUNCTION spatial_data.vector_similarity(v1 vector, v2 vector)
RETURNS float AS $$
BEGIN
    RETURN 1 - (v1 <=> v2);  -- Cosine similarity = 1 - cosine distance
END;
$$ LANGUAGE plpgsql;

-- Vue pour combiner données spatiales et vectorielles
CREATE OR REPLACE VIEW spatial_data.enriched_locations AS
SELECT 
    id,
    name,
    description,
    ST_AsText(geometry) as wkt_geometry,
    ST_X(geometry) as longitude,
    ST_Y(geometry) as latitude,
    embedding::text as embedding_json,
    created_at
FROM spatial_data.test_locations;

-- Privilèges pour l'utilisateur Grist
GRANT ALL PRIVILEGES ON SCHEMA spatial_data TO grist;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA spatial_data TO grist;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA spatial_data TO grist;

-- Log d'initialisation
DO $$
BEGIN
    RAISE NOTICE '✅ Base de données spatiale initialisée avec PostGIS et pgvector';
    RAISE NOTICE '📊 % locations de test insérées', (SELECT COUNT(*) FROM spatial_data.test_locations);
END $$;