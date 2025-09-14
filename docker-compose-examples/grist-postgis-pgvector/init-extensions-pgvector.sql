-- Script d'initialisation pour l'image ankane/pgvector
-- Cette image inclut déjà pg_vector mais pas PostGIS

-- Installer PostGIS (si disponible)
DO $$
BEGIN
    -- Tenter d'installer PostGIS
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS postgis_topology;
    RAISE NOTICE 'PostGIS extensions installed successfully';
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'PostGIS extensions not available in this image';
        RAISE WARNING 'Only vector support will be enabled';
        RAISE WARNING 'Error: %', SQLERRM;
END $$;

-- Activer pg_vector (devrait déjà être disponible)
CREATE EXTENSION IF NOT EXISTS vector;

-- Vérifier les extensions installées
DO $$
DECLARE
    ext_record RECORD;
    ext_count INTEGER;
    vector_installed BOOLEAN := FALSE;
    postgis_installed BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE 'Installed extensions:';
    ext_count := 0;
    
    FOR ext_record IN 
        SELECT extname, extversion 
        FROM pg_extension 
        WHERE extname IN ('postgis', 'postgis_topology', 'vector', 'plpgsql')
        ORDER BY extname
    LOOP
        RAISE NOTICE '  - %: version %', ext_record.extname, ext_record.extversion;
        ext_count := ext_count + 1;
        
        IF ext_record.extname = 'vector' THEN
            vector_installed := TRUE;
        END IF;
        
        IF ext_record.extname = 'postgis' THEN
            postgis_installed := TRUE;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Total extensions installed: %', ext_count;
    
    -- Résumé des capacités
    IF vector_installed AND postgis_installed THEN
        RAISE NOTICE '✅ Full support: Vector embeddings + Spatial data (PostGIS)';
    ELSIF vector_installed THEN
        RAISE NOTICE '✅ Vector embeddings support enabled';
        RAISE NOTICE '❌ Spatial data (PostGIS) not available';
    ELSIF postgis_installed THEN
        RAISE NOTICE '✅ Spatial data (PostGIS) support enabled';
        RAISE NOTICE '❌ Vector embeddings not available';
    ELSE
        RAISE WARNING '❌ Neither vector nor spatial extensions available!';
    END IF;
END $$;

-- Créer une table de test pour vérifier que pg_vector fonctionne
CREATE TABLE IF NOT EXISTS vector_test (
    id SERIAL PRIMARY KEY,
    name TEXT,
    embedding VECTOR(3)
);

-- Insérer des données de test
INSERT INTO vector_test (name, embedding) VALUES 
    ('test1', '[1,2,3]'),
    ('test2', '[4,5,6]'),
    ('test3', '[7,8,9]')
ON CONFLICT DO NOTHING;

-- Test de requête avec pg_vector
DO $$
DECLARE
    similarity_result RECORD;
BEGIN
    RAISE NOTICE 'Vector test table created with sample data';
    
    -- Test de similarité cosinus
    SELECT name, embedding <=> '[1,2,3]' as distance 
    FROM vector_test 
    ORDER BY distance 
    LIMIT 1
    INTO similarity_result;
    
    RAISE NOTICE 'pg_vector test successful! Closest to [1,2,3]: % (distance: %)', 
                 similarity_result.name, similarity_result.distance;
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'pg_vector test failed: %', SQLERRM;
END $$;
