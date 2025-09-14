#!/bin/bash
set -e

echo "🚀 Démarrage Grist avec PostgreSQL + PostGIS + pgvector intégrés"

# Vérifier si PostgreSQL est déjà initialisé
if [ ! -f /var/lib/postgresql/data/PG_VERSION ]; then
    echo "❌ PostgreSQL data directory not properly initialized"
    exit 1
fi

# Créer l'utilisateur grist pour la base de données si nécessaire
echo "🔧 Configuration de la base de données PostgreSQL..."

# Démarrer PostgreSQL temporairement pour l'initialisation
su - postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/data -l /tmp/postgres_init.log start"

# Attendre que PostgreSQL soit prêt
sleep 5

# Initialiser la base de données Grist avec les extensions
su - postgres -c "psql -c \"CREATE USER grist WITH PASSWORD 'grist_integrated_2024';\"" 2>/dev/null || true
su - postgres -c "psql -c \"CREATE DATABASE grist OWNER grist;\"" 2>/dev/null || true
su - postgres -c "psql -d grist -c \"GRANT ALL PRIVILEGES ON DATABASE grist TO grist;\""

# Installer les extensions PostGIS et pgvector
echo "🗄️ Installation des extensions PostGIS et pgvector..."
su - postgres -c "psql -d grist -c \"CREATE EXTENSION IF NOT EXISTS postgis;\""
su - postgres -c "psql -d grist -c \"CREATE EXTENSION IF NOT EXISTS postgis_topology;\""
su - postgres -c "psql -d grist -c \"CREATE EXTENSION IF NOT EXISTS vector;\""

# Vérifier les extensions installées
echo "✅ Extensions installées:"
su - postgres -c "psql -d grist -c \"SELECT extname, extversion FROM pg_extension WHERE extname IN ('postgis', 'postgis_topology', 'vector');\""

# Arrêter PostgreSQL temporaire
su - postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/data stop"

# Créer les répertoires de logs
mkdir -p /var/log/supervisor
chown -R postgres:postgres /var/lib/postgresql
chown -R grist:grist /grist /persist

echo "🎯 Configuration terminée, lancement de Supervisor..."

# Exécuter la commande fournie (supervisord par défaut)
exec "$@"