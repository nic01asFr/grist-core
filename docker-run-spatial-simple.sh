#!/bin/bash

# Script simple pour lancer Grist avec extensions spatiales injectées
# Alternative rapide au Docker Compose

set -e

echo "🚀 LANCEMENT GRIST SPATIAL - APPROCHE SIMPLE"
echo "============================================"

# Variables
GRIST_PORT=8485
POSTGRES_PORT=5433

# Nettoyer les containers existants
echo "🧹 Nettoyage containers existants..."
docker stop grist-spatial-simple postgres-spatial 2>/dev/null || true
docker rm grist-spatial-simple postgres-spatial 2>/dev/null || true

# Lancer PostgreSQL avec PostGIS
echo "🐘 Lancement PostgreSQL + PostGIS..."
docker run -d \
    --name postgres-spatial \
    -e POSTGRES_DB=grist \
    -e POSTGRES_USER=grist \
    -e POSTGRES_PASSWORD=grist \
    -p $POSTGRES_PORT:5432 \
    -v $(pwd)/init-spatial.sql:/docker-entrypoint-initdb.d/init-spatial.sql \
    pgvector/pgvector:pg16

# Attendre que PostgreSQL soit prêt
echo "⏳ Attente PostgreSQL..."
sleep 10

# Tester la connexion PostgreSQL
for i in {1..10}; do
    if docker exec postgres-spatial pg_isready -U grist >/dev/null 2>&1; then
        echo "✅ PostgreSQL prêt"
        break
    fi
    echo "   Tentative $i/10..."
    sleep 2
done

# Lancer Grist avec nos extensions
echo "📊 Lancement Grist avec extensions spatiales..."
docker run -d \
    --name grist-spatial-simple \
    --link postgres-spatial:postgres \
    -p $GRIST_PORT:8484 \
    -e GRIST_DATABASE_URL="postgresql://grist:grist@postgres:5432/grist" \
    -e GRIST_SPATIAL_ENABLED=true \
    -e GRIST_VECTOR_ENABLED=true \
    -e ALBERT_API_TOKEN="sk-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo5MywidG9rZW5faWQiOjExODksImV4cGlyZXNfYXQiOjE3NzgxOTEyMDB9.mXyNfn1kLYP3hNe5lzraEHjGAbfyB-YfiNpsnp52f80" \
    -e ALBERT_API_URL="https://albert.api.etalab.gouv.fr/v1" \
    -v $(pwd)/compiled-extensions:/grist-extensions:ro \
    -v grist-data:/persist \
    gristlabs/grist:latest \
    bash -c "
        echo '🔧 Installation dépendances spatiales...'
        npm install axios 2>/dev/null || true
        
        echo '💉 Injection extensions spatiales...'
        node -e '
            try {
                console.log(\"Chargement SpatialVectorService...\");
                require(\"/grist-extensions/SpatialVectorService.js\");
                
                console.log(\"Chargement NativeSpatialFunctions...\");  
                const functions = require(\"/grist-extensions/NativeSpatialFunctions.js\");
                console.log(\"Fonctions disponibles:\", Object.keys(functions));
                
                console.log(\"Chargement NativeSpatialApi...\");
                const { setupSpatialRoutes } = require(\"/grist-extensions/NativeSpatialApi.js\");
                console.log(\"API spatiale chargée\");
                
                console.log(\"✅ Toutes les extensions chargées avec succès !\");
            } catch (error) {
                console.log(\"❌ Erreur chargement:\", error.message);
            }
        ' || echo '⚠️ Extensions non chargées'
        
        echo '🚀 Démarrage Grist...'
        exec /usr/local/bin/docker-entrypoint.sh
    "

# Attendre que Grist soit prêt
echo "⏳ Attente de Grist..."
sleep 15

# Test de disponibilité
echo "🧪 Test de disponibilité..."
for i in {1..10}; do
    if curl -s http://localhost:$GRIST_PORT >/dev/null; then
        echo "✅ Grist accessible sur http://localhost:$GRIST_PORT"
        break
    fi
    echo "   Tentative $i/10..."
    sleep 3
done

# Logs des containers
echo ""
echo "📋 Status des containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔗 URLs importantes:"
echo "   - Grist spatial: http://localhost:$GRIST_PORT"
echo "   - PostgreSQL: localhost:$POSTGRES_PORT"

echo ""
echo "🧪 Test rapide des extensions:"
echo "   curl http://localhost:$GRIST_PORT/api/docs/test/spatial/config"

echo ""
echo "📜 Commandes utiles:"
echo "   docker logs grist-spatial-simple"
echo "   docker logs postgres-spatial"
echo "   docker exec -it grist-spatial-simple ls -la /grist-extensions/"