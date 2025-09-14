#!/bin/bash

# Script de démarrage pour container Grist spatial standalone

echo "🚀 Démarrage container Grist Spatial Standalone"

# Initialiser PostgreSQL si nécessaire
if [ ! -f /var/lib/postgresql/16/main/PG_VERSION ]; then
    echo "Initialisation PostgreSQL..."
    su - postgres -c "/usr/lib/postgresql/16/bin/initdb -D /var/lib/postgresql/16/main"
fi

# Démarrer PostgreSQL temporairement pour initialisation
echo "Démarrage PostgreSQL pour initialisation..."
su - postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/16/main -l /var/lib/postgresql/16/main/log start"

# Attendre que PostgreSQL soit prêt
echo "Attente PostgreSQL..."
until su - postgres -c "pg_isready -q"; do
    sleep 1
done

# Créer la base et l'utilisateur
echo "Configuration base de données..."
su - postgres -c "createdb grist" 2>/dev/null || true
su - postgres -c "psql -c \"CREATE USER grist WITH PASSWORD 'grist123';\"" 2>/dev/null || true
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE grist TO grist;\"" 2>/dev/null || true

# Activer les extensions
echo "Activation extensions PostGIS et pgvector..."
su - postgres -c "psql -d grist -c \"CREATE EXTENSION IF NOT EXISTS postgis;\""
su - postgres -c "psql -d grist -c \"CREATE EXTENSION IF NOT EXISTS vector;\""

# Arrêter PostgreSQL temporaire
su - postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/16/main stop"

# Construire Grist si nécessaire
if [ ! -f /grist/dist/server.js ]; then
    echo "Construction Grist..."
    cd /grist
    su - grist -c "cd /grist && npm run build"
fi

# Créer les répertoires de logs pour supervisor
mkdir -p /var/log/supervisor

# Démarrer supervisor qui gère PostgreSQL et Grist
echo "Démarrage services avec supervisor..."
exec supervisord -c /etc/supervisor/conf.d/supervisor.conf