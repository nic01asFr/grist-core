-- Initialisation de la base de données Grist avec PostGIS + pgvector
-- Ce script est exécuté automatiquement lors de la première initialisation

-- Créer les extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS vector;

-- Table de test spatial (optionnel)
CREATE TABLE IF NOT EXISTS spatial_demo (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    location GEOMETRY(POINT, 4326),
    area GEOMETRY(POLYGON, 4326),
    embedding VECTOR(1024),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index spatial et vectoriel
CREATE INDEX IF NOT EXISTS idx_spatial_demo_location ON spatial_demo USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_spatial_demo_embedding ON spatial_demo USING ivfflat(embedding) WITH (lists = 100);

-- Données de test (Paris landmarks)
INSERT INTO spatial_demo (name, location, area, embedding) VALUES
    (
        'Tour Eiffel',
        ST_GeomFromText('POINT(2.2945 48.8582)', 4326),
        ST_GeomFromText('POLYGON((2.2935 48.8575, 2.2955 48.8575, 2.2955 48.8590, 2.2935 48.8590, 2.2935 48.8575))', 4326),
        array_fill(0.1, ARRAY[1024])::vector
    ),
    (
        'Notre-Dame',
        ST_GeomFromText('POINT(2.3522 48.8530)', 4326),
        ST_GeomFromText('POLYGON((2.3512 48.8525, 2.3532 48.8525, 2.3532 48.8535, 2.3512 48.8535, 2.3512 48.8525))', 4326),
        array_fill(0.2, ARRAY[1024])::vector
    )
ON CONFLICT DO NOTHING;

-- Vérification des extensions
DO $$
BEGIN
    RAISE NOTICE '🎉 Extensions PostgreSQL installées dans Grist:';
    FOR rec IN 
        SELECT extname, extversion 
        FROM pg_extension 
        WHERE extname IN ('postgis', 'postgis_topology', 'vector', 'plpgsql')
        ORDER BY extname
    LOOP
        RAISE NOTICE '  ✅ %: version %', rec.extname, rec.extversion;
    END LOOP;
    
    RAISE NOTICE '🗄️ Tables spatiales et vectorielles prêtes pour Grist';
END $$;