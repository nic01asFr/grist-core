-- Script d'initialisation complet pour PostGIS + pg_vector
-- Support intégral des données spatiales et vectorielles pour Grist

-- ==================================================
-- 1. INSTALLATION DES EXTENSIONS
-- ==================================================

-- Installer PostGIS (données spatiales)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Installer pg_vector (embeddings vectoriels)  
CREATE EXTENSION IF NOT EXISTS vector;

-- ==================================================
-- 2. VÉRIFICATION DES EXTENSIONS INSTALLÉES
-- ==================================================

DO $$
DECLARE
    ext_record RECORD;
    ext_count INTEGER;
    postgis_installed BOOLEAN := FALSE;
    vector_installed BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '🔧 Extensions PostgreSQL installées :';
    ext_count := 0;
    
    FOR ext_record IN 
        SELECT extname, extversion 
        FROM pg_extension 
        WHERE extname IN ('postgis', 'postgis_topology', 'vector', 'plpgsql')
        ORDER BY extname
    LOOP
        RAISE NOTICE '  ✅ %: version %', ext_record.extname, ext_record.extversion;
        ext_count := ext_count + 1;
        
        IF ext_record.extname = 'vector' THEN
            vector_installed := TRUE;
        END IF;
        
        IF ext_record.extname = 'postgis' THEN
            postgis_installed := TRUE;
        END IF;
    END LOOP;
    
    RAISE NOTICE '📊 Total extensions installées: %', ext_count;
    
    -- Résumé des capacités
    IF vector_installed AND postgis_installed THEN
        RAISE NOTICE '🎉 SUPPORT COMPLET: Données spatiales (PostGIS) + Vecteurs (pg_vector)';
    ELSIF vector_installed THEN
        RAISE NOTICE '✅ Support vectoriel uniquement';
        RAISE NOTICE '❌ Données spatiales non disponibles';
    ELSIF postgis_installed THEN
        RAISE NOTICE '✅ Support spatial uniquement';
        RAISE NOTICE '❌ Support vectoriel non disponible';
    ELSE
        RAISE WARNING '❌ Aucune extension spatiale ou vectorielle disponible!';
    END IF;
END $$;

-- ==================================================
-- 3. TABLES DE TEST SPATIALES (PostGIS)
-- ==================================================

-- Table de test pour les géométries
CREATE TABLE IF NOT EXISTS spatial_test (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    location GEOMETRY(POINT, 4326),        -- Points avec SRID 4326 (WGS84)
    area GEOMETRY(POLYGON, 4326),          -- Polygones  
    route GEOMETRY(LINESTRING, 4326),      -- Lignes
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index spatial pour les performances
CREATE INDEX IF NOT EXISTS idx_spatial_test_location ON spatial_test USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_spatial_test_area ON spatial_test USING GIST(area);

-- Données de test spatiales
INSERT INTO spatial_test (name, location, area, route) VALUES
    (
        'Tour Eiffel', 
        ST_GeomFromText('POINT(2.2945 48.8582)', 4326),
        ST_GeomFromText('POLYGON((2.2935 48.8575, 2.2955 48.8575, 2.2955 48.8590, 2.2935 48.8590, 2.2935 48.8575))', 4326),
        ST_GeomFromText('LINESTRING(2.2940 48.8580, 2.2950 48.8585)', 4326)
    ),
    (
        'Notre-Dame', 
        ST_GeomFromText('POINT(2.3522 48.8530)', 4326),
        ST_GeomFromText('POLYGON((2.3512 48.8525, 2.3532 48.8525, 2.3532 48.8535, 2.3512 48.8535, 2.3512 48.8525))', 4326),
        ST_GeomFromText('LINESTRING(2.3517 48.8527, 2.3527 48.8533)', 4326)
    ),
    (
        'Louvre', 
        ST_GeomFromText('POINT(2.3376 48.8606)', 4326),
        ST_GeomFromText('POLYGON((2.3366 48.8601, 2.3386 48.8601, 2.3386 48.8611, 2.3366 48.8611, 2.3366 48.8601))', 4326),
        ST_GeomFromText('LINESTRING(2.3371 48.8603, 2.3381 48.8609)', 4326)
    )
ON CONFLICT DO NOTHING;

-- ==================================================
-- 4. TABLES DE TEST VECTORIELLES (pg_vector)
-- ==================================================

-- Table de test pour les embeddings
CREATE TABLE IF NOT EXISTS vector_test (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    content TEXT,
    embedding_small VECTOR(3),              -- Petit vecteur de test
    embedding_medium VECTOR(384),           -- Taille sentence-transformers
    embedding_large VECTOR(1536),           -- Taille OpenAI ada-002
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index vectoriel pour recherche de similarité  
CREATE INDEX IF NOT EXISTS idx_vector_test_small ON vector_test USING ivfflat(embedding_small) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_vector_test_medium ON vector_test USING hnsw(embedding_medium) WITH (m = 16, ef_construction = 64);

-- Données de test vectorielles
INSERT INTO vector_test (name, content, embedding_small, embedding_medium) VALUES
    (
        'Document Paris',
        'La ville lumière est magnifique avec sa Tour Eiffel.',
        '[1.0, 2.0, 3.0]',
        ARRAY_FILL(0.1::real, ARRAY[384])::real[]::vector  -- Vecteur de 384 dimensions avec valeurs 0.1
    ),
    (
        'Document London', 
        'London is a great city with Big Ben and the Thames.',
        '[4.0, 5.0, 6.0]',
        ARRAY_FILL(0.2::real, ARRAY[384])::real[]::vector
    ),
    (
        'Document Tokyo',
        '東京は素晴らしい都市で、多くの観光地があります。',
        '[7.0, 8.0, 9.0]',
        ARRAY_FILL(0.3::real, ARRAY[384])::real[]::vector
    )
ON CONFLICT DO NOTHING;

-- ==================================================
-- 5. TESTS FONCTIONNELS
-- ==================================================

DO $$
DECLARE
    spatial_result RECORD;
    vector_result RECORD;
    test_point GEOMETRY;
    test_vector VECTOR(3);
BEGIN
    RAISE NOTICE '🧪 DÉBUT DES TESTS FONCTIONNELS';
    
    -- Test PostGIS : Distance entre points
    BEGIN
        SELECT 
            s1.name as from_place,
            s2.name as to_place,
            ROUND(ST_Distance(s1.location, s2.location)::numeric, 2) as distance_meters,
            ROUND(ST_Distance(ST_Transform(s1.location, 3857), ST_Transform(s2.location, 3857))::numeric, 0) as distance_m_projected
        FROM spatial_test s1, spatial_test s2 
        WHERE s1.name = 'Tour Eiffel' AND s2.name = 'Notre-Dame'
        INTO spatial_result;
        
        RAISE NOTICE '🗺️  PostGIS Test: Distance % -> % = %m (géodésique)', 
                     spatial_result.from_place, 
                     spatial_result.to_place, 
                     spatial_result.distance_meters;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE WARNING '❌ Test PostGIS échoué: %', SQLERRM;
    END;
    
    -- Test pg_vector : Similarité cosinus
    BEGIN
        test_vector := '[1,2,3]';
        SELECT 
            name, 
            embedding_small,
            ROUND((1 - (embedding_small <=> test_vector))::numeric, 4) as cosine_similarity,
            ROUND((embedding_small <-> test_vector)::numeric, 4) as euclidean_distance
        FROM vector_test 
        ORDER BY embedding_small <=> test_vector
        LIMIT 1
        INTO vector_result;
        
        RAISE NOTICE '🤖 pg_vector Test: Plus similaire à % = "%" (similarité cosinus: %)', 
                     test_vector, 
                     vector_result.name, 
                     vector_result.cosine_similarity;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE WARNING '❌ Test pg_vector échoué: %', SQLERRM;
    END;
    
    -- Test combiné : Table avec géométrie ET vecteur
    BEGIN
        CREATE TABLE IF NOT EXISTS geoai_test (
            id SERIAL PRIMARY KEY,
            name TEXT,
            location GEOMETRY(POINT, 4326),
            description_vector VECTOR(3)
        );
        
        INSERT INTO geoai_test (name, location, description_vector) VALUES 
            ('Paris AI', ST_GeomFromText('POINT(2.3522 48.8566)', 4326), '[0.8, 0.9, 0.7]')
        ON CONFLICT DO NOTHING;
        
        RAISE NOTICE '🌍 Test Hybride: Table geo+AI créée avec succès';
    EXCEPTION
        WHEN OTHERS THEN
            RAISE WARNING '❌ Test hybride échoué: %', SQLERRM;
    END;
    
    RAISE NOTICE '✅ TESTS TERMINÉS';
END $$;

-- ==================================================
-- 6. FONCTIONS UTILITAIRES POUR GRIST
-- ==================================================

-- Fonction pour calculer la distance entre deux points WKT
CREATE OR REPLACE FUNCTION grist_spatial_distance(wkt1 TEXT, wkt2 TEXT)
RETURNS FLOAT AS $$
BEGIN
    RETURN ST_Distance(
        ST_GeomFromText(wkt1, 4326), 
        ST_GeomFromText(wkt2, 4326)
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour calculer la similarité cosinus entre deux vecteurs
CREATE OR REPLACE FUNCTION grist_vector_similarity(vec1 VECTOR, vec2 VECTOR)
RETURNS FLOAT AS $$
BEGIN
    RETURN 1 - (vec1 <=> vec2);
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour valider un WKT
CREATE OR REPLACE FUNCTION grist_is_valid_wkt(wkt_text TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    PERFORM ST_GeomFromText(wkt_text);
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

RAISE NOTICE '🎯 CONFIGURATION COMPLÈTE TERMINÉE';
RAISE NOTICE '📍 PostGIS: Données spatiales, géométries, calculs de distance';
RAISE NOTICE '🤖 pg_vector: Embeddings, similarité, recherche vectorielle';
RAISE NOTICE '🚀 Grist peut maintenant utiliser les types Geometry et Vector !');
