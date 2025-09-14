# Grist avec Support PostGIS et pg_vector

Cet exemple configure Grist avec PostgreSQL incluant le support des extensions PostGIS et pg_vector pour les données spatiales et vectorielles.

## 🚀 Démarrage Rapide

1. **Créer le fichier d'environnement** :
   ```bash
   cp .env.example .env
   # Éditer .env avec vos valeurs
   ```

2. **Lancer les services** :
   ```bash
   docker-compose up -d
   ```

3. **Accéder à Grist** :
   Ouvrir http://localhost:8484

## ⚙️ Configuration

### Variables d'environnement (.env)

```bash
# Mot de passe de la base de données
DATABASE_PASSWORD=votre_mot_de_passe_securise

# Répertoire pour la persistance des données
PERSIST_DIR=./persist

# Port d'exposition de Grist (optionnel)
# GRIST_PORT=8484
```

### Services inclus

- **Grist** : Interface principale sur le port 8484
- **PostgreSQL avec PostGIS** : Base de données avec extensions spatiales
- **Redis** : Cache pour les performances

## 🗺️ Utilisation des Types Géométriques

### Création de colonnes spatiales

1. Créer une nouvelle table ou modifier une existante
2. Ajouter une colonne de type **"Geometry"**
3. Saisir des données au format WKT :

```
POINT(2.3522 48.8566)                    # Paris
LINESTRING(0 0, 1 1, 2 2)                # Ligne
POLYGON((0 0, 4 0, 4 4, 0 4, 0 0))       # Rectangle
```

### Exemples de données

```csv
lieu,coordonnees
Tour Eiffel,"POINT(2.2945 48.8582)"
Notre-Dame,"POINT(2.3522 48.8530)"
Louvre,"POINT(2.3376 48.8606)"
```

## 🤖 Utilisation des Types Vectoriels

### Création de colonnes vectorielles

1. Ajouter une colonne de type **"Vector"**
2. Optionnel : Spécifier les dimensions avec `Vector:N`
3. Saisir des vecteurs :

```
[0.1, 0.2, 0.3, 0.4]                     # Format JSON
1.1, 2.2, 3.3, 4.4                       # Format CSV
```

### Exemples d'embeddings

```csv
document,embedding
"Article 1","[0.12, -0.34, 0.56, 0.78]"
"Article 2","[0.23, 0.45, -0.67, 0.89]"
```

## 🔍 Vérification des Extensions

Pour vérifier que les extensions sont bien installées :

```sql
-- Via l'interface SQL de Grist ou un client PostgreSQL
SELECT extname, extversion 
FROM pg_extension 
WHERE extname IN ('postgis', 'vector')
ORDER BY extname;
```

## 🛠️ Résolution de Problèmes

### PostGIS ne fonctionne pas

```bash
# Vérifier les logs du conteneur
docker-compose logs grist-db

# Se connecter au conteneur
docker-compose exec grist-db psql -U grist -d grist -c "SELECT PostGIS_Version();"
```

### pg_vector ne fonctionne pas

L'extension pg_vector nécessite une installation manuelle. Solutions :

#### Option 1 : Image PostgreSQL personnalisée
```dockerfile
FROM postgis/postgis:16-3.4

# Installer pg_vector
RUN apt-get update && \
    apt-get install -y git build-essential postgresql-server-dev-16 && \
    cd /tmp && \
    git clone https://github.com/pgvector/pgvector.git && \
    cd pgvector && \
    make && make install && \
    rm -rf /tmp/pgvector && \
    apt-get purge -y git build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*
```

#### Option 2 : Installation après démarrage
```bash
# Installer dans le conteneur en cours
docker-compose exec grist-db bash -c "
  apt-get update && 
  apt-get install -y git build-essential postgresql-server-dev-16 && 
  git clone https://github.com/pgvector/pgvector.git /tmp/pgvector &&
  cd /tmp/pgvector && 
  make && make install
"

# Redémarrer PostgreSQL
docker-compose restart grist-db
```

#### Option 3 : Image tierce avec pg_vector
```yaml
# Dans docker-compose.yml, remplacer :
grist-db:
  image: ankane/pgvector:16  # Image avec pg_vector pré-installé
  # ... reste de la configuration
```

### Problèmes de permissions

```bash
# Vérifier les droits sur les répertoires de persistance
sudo chown -R $(id -u):$(id -g) ./persist
chmod -R 755 ./persist
```

### Données perdues au redémarrage

Vérifier que la variable `PERSIST_DIR` pointe vers un répertoire existant avec les bonnes permissions.

## 📚 Ressources

- [Documentation PostGIS](https://postgis.net/docs/)
- [Documentation pg_vector](https://github.com/pgvector/pgvector)
- [Format WKT](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry)
- [Support PostGIS/pg_vector dans Grist](../../documentation/postgis-pgvector-support.md)
