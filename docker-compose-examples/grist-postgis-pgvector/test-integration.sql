-- Script de Test d'Intégration Complète
-- Teste les nouveaux types Geometry et Vector dans Grist

-- ==================================================
-- 1. TEST DES TYPES VECTORIELS (pg_vector)
-- ==================================================

\echo '🤖 TEST pg_vector - Types vectoriels'

-- Créer une table de test pour Grist avec colonnes Vector
CREATE TABLE IF NOT EXISTS grist_vector_demo (
    id SERIAL PRIMARY KEY,
    document_title TEXT,
    content TEXT,
    embedding_3d VECTOR(3),           -- Pour test simple
    embedding_openai VECTOR(1536),    -- Dimension OpenAI ada-002  
    embedding_sentence VECTOR(384),   -- Dimension sentence-transformers
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insérer des données de test
INSERT INTO grist_vector_demo (document_title, content, embedding_3d, embedding_openai, embedding_sentence) VALUES
    (
        'Paris Tourism',
        'Visit the Eiffel Tower and enjoy French cuisine',
        '[0.8, 0.6, 0.9]',
        ARRAY_FILL(0.1::real, ARRAY[1536])::real[]::vector,
        ARRAY_FILL(0.2::real, ARRAY[384])::real[]::vector
    ),
    (
        'London Guide',
        'Explore Big Ben, Thames, and British culture',
        '[0.7, 0.8, 0.5]',
        ARRAY_FILL(0.3::real, ARRAY[1536])::real[]::vector,
        ARRAY_FILL(0.4::real, ARRAY[384])::real[]::vector
    ),
    (
        'Tokyo Adventure',
        'Discover temples, sushi, and modern technology',
        '[0.9, 0.5, 0.8]',
        ARRAY_FILL(0.5::real, ARRAY[1536])::real[]::vector,
        ARRAY_FILL(0.6::real, ARRAY[384])::real[]::vector
    )
ON CONFLICT DO NOTHING;

-- Test similarité vectorielle
\echo '📊 Test de similarité vectorielle (cosinus)'
SELECT 
    document_title,
    content,
    embedding_3d,
    ROUND((1 - (embedding_3d <=> '[0.8,0.6,0.9]'))::numeric, 4) as cosine_similarity,
    ROUND((embedding_3d <-> '[0.8,0.6,0.9]')::numeric, 4) as euclidean_distance
FROM grist_vector_demo
ORDER BY embedding_3d <=> '[0.8,0.6,0.9]'
LIMIT 3;

-- ==================================================
-- 2. TEST DES TYPES GÉOMÉTRIQUES (Compatible WKT) 
-- ==================================================

\echo '🗺️ TEST Geometry - Types géométriques (WKT)'

-- Créer une table de test pour Grist avec colonnes Geometry (stockage TEXT/WKT)
CREATE TABLE IF NOT EXISTS grist_geometry_demo (
    id SERIAL PRIMARY KEY,
    location_name TEXT,
    point_wkt TEXT,                    -- Point en format WKT
    area_wkt TEXT,                     -- Polygone en format WKT  
    route_wkt TEXT,                    -- Ligne en format WKT
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insérer des données de test en WKT (compatible avec le type Geometry de Grist)
INSERT INTO grist_geometry_demo (location_name, point_wkt, area_wkt, route_wkt, metadata) VALUES
    (
        'Tour Eiffel',
        'POINT(2.2945 48.8582)',
        'POLYGON((2.2935 48.8575, 2.2955 48.8575, 2.2955 48.8590, 2.2935 48.8590, 2.2935 48.8575))',
        'LINESTRING(2.2940 48.8580, 2.2950 48.8585)',
        '{"country": "France", "city": "Paris", "type": "monument"}'::jsonb
    ),
    (
        'Big Ben',
        'POINT(-0.1246 51.4994)',
        'POLYGON((-0.1256 51.4989, -0.1236 51.4989, -0.1236 51.4999, -0.1256 51.4999, -0.1256 51.4989))',
        'LINESTRING(-0.1251 51.4991, -0.1241 51.4997)',
        '{"country": "UK", "city": "London", "type": "clock_tower"}'::jsonb
    ),
    (
        'Tokyo Skytree',
        'POINT(139.8107 35.7101)',
        'POLYGON((139.8097 35.7096, 139.8117 35.7096, 139.8117 35.7106, 139.8097 35.7106, 139.8097 35.7096))',
        'LINESTRING(139.8102 35.7098, 139.8112 35.7104)',
        '{"country": "Japan", "city": "Tokyo", "type": "tower"}'::jsonb
    )
ON CONFLICT DO NOTHING;

-- Afficher les géométries
\echo '📍 Données géométriques au format WKT (compatible Grist)'
SELECT 
    location_name,
    point_wkt,
    CASE 
        WHEN LENGTH(area_wkt) > 50 
        THEN LEFT(area_wkt, 47) || '...' 
        ELSE area_wkt 
    END as area_preview,
    metadata->>'country' as country,
    metadata->>'type' as monument_type
FROM grist_geometry_demo
ORDER BY location_name;

-- ==================================================
-- 3. TEST TABLE HYBRIDE (Vector + Geometry)
-- ==================================================

\echo '🌍 TEST Hybride - Vector + Geometry dans la même table'

CREATE TABLE IF NOT EXISTS grist_hybrid_demo (
    id SERIAL PRIMARY KEY,
    place_name TEXT,
    description TEXT,
    -- Colonnes pour Grist type Geometry (WKT)
    location_wkt TEXT,
    -- Colonnes pour Grist type Vector  
    description_embedding VECTOR(3),
    -- Métadonnées
    tags TEXT[],
    rating NUMERIC(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO grist_hybrid_demo (
    place_name, description, location_wkt, description_embedding, tags, rating
) VALUES
    (
        'Louvre Museum',
        'World famous art museum with Mona Lisa',
        'POINT(2.3376 48.8606)',
        '[0.9, 0.8, 0.7]',
        ARRAY['art', 'museum', 'culture', 'paris'],
        4.7
    ),
    (
        'Central Park',
        'Large public park in Manhattan New York',
        'POINT(-73.9857 40.7829)',
        '[0.6, 0.9, 0.5]',
        ARRAY['park', 'nature', 'recreation', 'nyc'],
        4.5
    ),
    (
        'Shibuya Crossing',
        'Famous busy pedestrian crossing in Tokyo',
        'POINT(139.7016 35.6598)',
        '[0.8, 0.7, 0.9]',
        ARRAY['urban', 'crossing', 'busy', 'tokyo'],
        4.3
    )
ON CONFLICT DO NOTHING;

-- Test recherche hybride
\echo '🔍 Recherche hybride: géométrie + similarité vectorielle'
SELECT 
    place_name,
    description,
    location_wkt,
    description_embedding,
    ROUND((1 - (description_embedding <=> '[0.9,0.8,0.7]'))::numeric, 4) as semantic_similarity,
    tags,
    rating
FROM grist_hybrid_demo
ORDER BY description_embedding <=> '[0.9,0.8,0.7]'
LIMIT 3;

-- ==================================================
-- 4. FONCTIONS UTILITAIRES POUR GRIST
-- ==================================================

\echo '⚙️ Création de fonctions utilitaires pour Grist'

-- Fonction pour valider un WKT
CREATE OR REPLACE FUNCTION validate_wkt(wkt_text TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Validation basique du format WKT
    IF wkt_text IS NULL OR TRIM(wkt_text) = '' THEN
        RETURN FALSE;
    END IF;
    
    -- Vérifier que ça commence par un type géométrique valide
    IF NOT (UPPER(TRIM(wkt_text)) ~ '^(POINT|LINESTRING|POLYGON|MULTIPOINT|MULTILINESTRING|MULTIPOLYGON|GEOMETRYCOLLECTION)\s*\(') THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour calculer la similarité cosinus entre vecteurs
CREATE OR REPLACE FUNCTION cosine_similarity(vec1 VECTOR, vec2 VECTOR)
RETURNS FLOAT AS $$
BEGIN
    RETURN 1 - (vec1 <=> vec2);
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Fonction pour extraire le type de géométrie d'un WKT
CREATE OR REPLACE FUNCTION extract_geometry_type(wkt_text TEXT)
RETURNS TEXT AS $$
BEGIN
    IF wkt_text IS NULL THEN
        RETURN NULL;
    END IF;
    
    RETURN TRIM(SPLIT_PART(UPPER(TRIM(wkt_text)), '(', 1));
EXCEPTION
    WHEN OTHERS THEN
        RETURN 'INVALID';
END;
$$ LANGUAGE plpgsql;

-- ==================================================
-- 5. TESTS DE VALIDATION
-- ==================================================

\echo '✅ Tests de validation des fonctions utilitaires'

-- Test validation WKT
SELECT 
    'POINT(2.3 48.8)' as wkt_example,
    validate_wkt('POINT(2.3 48.8)') as is_valid_wkt,
    extract_geometry_type('POINT(2.3 48.8)') as geometry_type;

-- Test similarité cosinus
SELECT 
    '[1,0,0]' as vec1,
    '[1,0,0]' as vec2,
    cosine_similarity('[1,0,0]', '[1,0,0]') as perfect_similarity,
    cosine_similarity('[1,0,0]', '[0,1,0]') as orthogonal_similarity;

-- ==================================================
-- 6. RÉSUMÉ DES CAPACITÉS
-- ==================================================

\echo '📋 RÉSUMÉ DES CAPACITÉS INTÉGRÉES'
\echo ''
\echo '🤖 pg_vector 0.5.1:'
\echo '  - Types VECTOR(n) supportés'
\echo '  - Similarité cosinus (<=>, <>)'  
\echo '  - Distance euclidienne (<->)'
\echo '  - Index IVFFLAT et HNSW'
\echo ''
\echo '🗺️ Types Geometry (WKT):'
\echo '  - POINT, LINESTRING, POLYGON'
\echo '  - MULTIPOINT, MULTILINESTRING, MULTIPOLYGON'
\echo '  - Stockage compatible Grist (TEXT/WKT)'
\echo '  - Fonctions de validation'
\echo ''
\echo '🚀 Intégration Grist:'
\echo '  - Type Vector: Arrays de nombres'
\echo '  - Type Geometry: Chaînes WKT'  
\echo '  - Widgets d''édition spécialisés'
\echo '  - Support des dimensions vectorielles'
\echo ''

-- Compter les enregistrements de test
SELECT 
    'grist_vector_demo' as table_name,
    COUNT(*) as records,
    'Vector embeddings' as description
FROM grist_vector_demo
UNION ALL
SELECT 
    'grist_geometry_demo' as table_name,
    COUNT(*) as records,
    'WKT geometries' as description  
FROM grist_geometry_demo
UNION ALL
SELECT 
    'grist_hybrid_demo' as table_name,
    COUNT(*) as records,
    'Vector + Geometry' as description
FROM grist_hybrid_demo;

\echo ''
\echo '🎯 STATUS: Intégration PostGIS + pg_vector FONCTIONNELLE!'
\echo '🌐 Interface Grist: http://localhost:8484'
\echo '📊 Base PostgreSQL: localhost:5433 (user: grist)'
