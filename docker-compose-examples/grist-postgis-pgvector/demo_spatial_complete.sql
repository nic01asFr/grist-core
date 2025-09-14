-- Démonstration complète des fonctionnalités spatiales et vectorielles
-- pour Grist avec PostGIS et pgvector

-- 1. Créer les extensions si nécessaire
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Créer une table de lieux touristiques parisiens avec géométries
CREATE TABLE IF NOT EXISTS lieux_touristiques (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100),
    description TEXT,
    categorie VARCHAR(50),
    localisation geometry(Point, 4326),
    zone_influence geometry(Polygon, 4326),
    embedding vector(1024)
);

-- 3. Insérer des données de lieux célèbres
INSERT INTO lieux_touristiques (nom, description, categorie, localisation) VALUES
('Tour Eiffel', 'Monument emblématique de Paris, tour de fer de 330 mètres', 'Monument', 
    ST_GeomFromText('POINT(2.2945 48.8582)', 4326)),
('Notre-Dame', 'Cathédrale gothique au cœur de Paris sur l''île de la Cité', 'Monument religieux',
    ST_GeomFromText('POINT(2.3499 48.8530)', 4326)),
('Arc de Triomphe', 'Monument historique au centre de la place de l''Étoile', 'Monument',
    ST_GeomFromText('POINT(2.2950 48.8738)', 4326)),
('Musée du Louvre', 'Plus grand musée d''art du monde', 'Musée',
    ST_GeomFromText('POINT(2.3376 48.8606)', 4326)),
('Sacré-Cœur', 'Basilique au sommet de la butte Montmartre', 'Monument religieux',
    ST_GeomFromText('POINT(2.3431 48.8867)', 4326))
ON CONFLICT DO NOTHING;

-- 4. Calculer les zones d'influence (buffer de 500m)
UPDATE lieux_touristiques 
SET zone_influence = ST_Transform(
    ST_Buffer(ST_Transform(localisation, 2154), 500), 
    4326
) 
WHERE zone_influence IS NULL;

-- 5. Créer une table de restaurants
CREATE TABLE IF NOT EXISTS restaurants (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100),
    cuisine VARCHAR(50),
    prix_moyen DECIMAL(5,2),
    localisation geometry(Point, 4326),
    description_embedding vector(1024)
);

-- 6. Insérer des restaurants
INSERT INTO restaurants (nom, cuisine, prix_moyen, localisation) VALUES
('Le Jules Verne', 'Gastronomique', 250.00, ST_GeomFromText('POINT(2.2945 48.8582)', 4326)),
('L''Ami Louis', 'Bistrot traditionnel', 85.00, ST_GeomFromText('POINT(2.3625 48.8673)', 4326)),
('Breizh Café', 'Crêperie moderne', 35.00, ST_GeomFromText('POINT(2.3625 48.8573)', 4326)),
('L''As du Fallafel', 'Moyen-Orient', 12.00, ST_GeomFromText('POINT(2.3592 48.8574)', 4326)),
('Pierre Gagnaire', 'Gastronomique', 380.00, ST_GeomFromText('POINT(2.3165 48.8663)', 4326))
ON CONFLICT DO NOTHING;

-- 7. Créer des fonctions utiles pour Grist
CREATE OR REPLACE FUNCTION distance_entre_points(
    point1 geometry,
    point2 geometry
) RETURNS FLOAT AS $$
BEGIN
    RETURN ST_Distance(point1::geography, point2::geography);
END;
$$ LANGUAGE plpgsql;

-- 8. Créer une vue pour analyser les restaurants près des monuments
CREATE OR REPLACE VIEW restaurants_pres_monuments AS
SELECT 
    r.nom as restaurant,
    r.cuisine,
    r.prix_moyen,
    l.nom as monument,
    ROUND(ST_Distance(r.localisation::geography, l.localisation::geography)::numeric, 2) as distance_metres
FROM restaurants r
CROSS JOIN lieux_touristiques l
WHERE ST_DWithin(r.localisation::geography, l.localisation::geography, 1000)
ORDER BY l.nom, distance_metres;

-- 9. Statistiques spatiales
CREATE OR REPLACE VIEW statistiques_spatiales AS
SELECT 
    'Nombre de monuments' as metrique,
    COUNT(*) as valeur
FROM lieux_touristiques
UNION ALL
SELECT 
    'Nombre de restaurants',
    COUNT(*)
FROM restaurants
UNION ALL
SELECT 
    'Distance moyenne entre monuments (m)',
    ROUND(AVG(ST_Distance(a.localisation::geography, b.localisation::geography))::numeric, 2)
FROM lieux_touristiques a, lieux_touristiques b
WHERE a.id < b.id
UNION ALL
SELECT 
    'Surface totale zones d''influence (km²)',
    ROUND((SUM(ST_Area(zone_influence::geography)) / 1000000)::numeric, 2)
FROM lieux_touristiques;

-- 10. Afficher les résultats
SELECT * FROM statistiques_spatiales;
SELECT * FROM restaurants_pres_monuments;

-- Distance spécifique Tour Eiffel - Notre-Dame
SELECT 
    'Tour Eiffel ↔ Notre-Dame' as trajet,
    ROUND(ST_Distance(
        ST_GeomFromText('POINT(2.2945 48.8582)', 4326)::geography,
        ST_GeomFromText('POINT(2.3499 48.8530)', 4326)::geography
    )::numeric, 2) as distance_metres;