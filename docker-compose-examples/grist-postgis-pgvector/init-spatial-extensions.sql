-- Extensions spatiales et vectorielles pour base dédiée
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS vector;

-- Table démo pour capacités spatiales/vectorielles
CREATE TABLE IF NOT EXISTS spatial_features (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    location GEOMETRY(POINT, 4326),
    area GEOMETRY(POLYGON, 4326),
    embedding VECTOR(1024),
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index optimisés
CREATE INDEX IF NOT EXISTS idx_spatial_features_location ON spatial_features USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_spatial_features_area ON spatial_features USING GIST(area);
CREATE INDEX IF NOT EXISTS idx_spatial_features_embedding ON spatial_features USING ivfflat(embedding) WITH (lists = 100);

-- Données de démonstration
INSERT INTO spatial_features (name, description, location, area, embedding, tags) VALUES
    (
        'Tour Eiffel',
        'Monument emblématique de Paris',
        ST_GeomFromText('POINT(2.2945 48.8582)', 4326),
        ST_GeomFromText('POLYGON((2.2935 48.8575, 2.2955 48.8575, 2.2955 48.8590, 2.2935 48.8590, 2.2935 48.8575))', 4326),
        array_fill(0.1, ARRAY[1024])::vector,
        ARRAY['monument', 'paris', 'tour']
    ),
    (
        'Notre-Dame de Paris',
        'Cathédrale gothique historique',
        ST_GeomFromText('POINT(2.3522 48.8530)', 4326),
        ST_GeomFromText('POLYGON((2.3512 48.8525, 2.3532 48.8525, 2.3532 48.8535, 2.3512 48.8535, 2.3512 48.8525))', 4326),
        array_fill(0.2, ARRAY[1024])::vector,
        ARRAY['cathedral', 'paris', 'gothic']
    ),
    (
        'Musée du Louvre',
        'Musée d art et palais royal',
        ST_GeomFromText('POINT(2.3376 48.8606)', 4326),
        ST_GeomFromText('POLYGON((2.3366 48.8601, 2.3386 48.8601, 2.3386 48.8611, 2.3366 48.8611, 2.3366 48.8601))', 4326),
        array_fill(0.3, ARRAY[1024])::vector,
        ARRAY['museum', 'paris', 'art']
    )
ON CONFLICT DO NOTHING;

-- Fonctions utilitaires pour Grist
CREATE OR REPLACE FUNCTION search_nearby_features(target_point GEOMETRY, radius_meters FLOAT) 
RETURNS TABLE(id INTEGER, name TEXT, distance_meters FLOAT) AS $$
BEGIN
    RETURN QUERY
    SELECT f.id, f.name, ST_Distance(f.location::geography, target_point::geography)::FLOAT
    FROM spatial_features f
    WHERE ST_DWithin(f.location::geography, target_point::geography, radius_meters)
    ORDER BY ST_Distance(f.location::geography, target_point::geography);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION search_similar_embeddings(target_embedding VECTOR, limit_results INTEGER DEFAULT 10)
RETURNS TABLE(id INTEGER, name TEXT, similarity_score FLOAT) AS $$
BEGIN
    RETURN QUERY
    SELECT f.id, f.name, (1 - (f.embedding <-> target_embedding))::FLOAT as similarity
    FROM spatial_features f
    ORDER BY f.embedding <-> target_embedding
    LIMIT limit_results;
END;
$$ LANGUAGE plpgsql;

-- Rapport des extensions
DO $$
BEGIN
    RAISE NOTICE '🗺️  SPATIAL DATABASE INITIALIZED';
    RAISE NOTICE '📊 Extensions disponibles:';
    FOR rec IN 
        SELECT extname, extversion 
        FROM pg_extension 
        WHERE extname IN ('postgis', 'postgis_topology', 'vector')
        ORDER BY extname
    LOOP
        RAISE NOTICE '   ✅ %: version %', rec.extname, rec.extversion;
    END LOOP;
    
    RAISE NOTICE '🎯 Tables créées: spatial_features';
    RAISE NOTICE '🔍 Fonctions utilitaires: search_nearby_features, search_similar_embeddings';
    RAISE NOTICE '🏗️  Ready for Grist integration!';
END $$;