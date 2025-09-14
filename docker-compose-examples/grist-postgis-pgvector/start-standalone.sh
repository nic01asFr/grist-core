#!/bin/bash

# Script de démarrage pour container Grist spatial standalone

echo "🚀 Démarrage Grist Spatial Standalone"

# Créer les répertoires de logs
mkdir -p /var/log/supervisor

# Initialiser PostgreSQL si pas déjà fait
if [ ! -f /var/lib/postgresql/16/main/PG_VERSION ]; then
    echo "Initialisation PostgreSQL..."
    su - postgres -c "/usr/lib/postgresql/16/bin/initdb -D /var/lib/postgresql/16/main"
    echo "Configuration PostgreSQL..."
    echo "host all all 127.0.0.1/32 trust" >> /etc/postgresql/16/main/pg_hba.conf
    echo "listen_addresses = '*'" >> /etc/postgresql/16/main/postgresql.conf
fi

# Démarrer supervisor qui gère PostgreSQL et Grist
echo "Démarrage services avec supervisor..."
exec supervisord -c /etc/supervisor/conf.d/supervisor.conf