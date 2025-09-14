# Support PostGIS et pg_vector dans Grist

Ce document décrit l'implémentation du support des extensions PostgreSQL PostGIS et pg_vector dans Grist, permettant la gestion des données spatiales et vectorielles.

## 🎯 Vue d'ensemble

L'extension permet d'utiliser dans Grist :
- **PostGIS** : Types géométriques pour les données spatiales (points, lignes, polygones)
- **pg_vector** : Types vectoriels pour les embeddings et la recherche de similarité

## 📋 Prérequis

### Extensions PostgreSQL

#### PostGIS
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-postgis

# RHEL/CentOS
sudo yum install postgis

# macOS
brew install postgis
```

#### pg_vector
```bash
# Installation depuis les sources (recommandée)
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make && sudo make install

# Ou via package manager si disponible
# Ubuntu 22.04+
sudo apt install postgresql-16-pgvector
```

### Configuration Base de Données

Les extensions sont installées automatiquement via la migration, mais peuvent être installées manuellement :

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
```

## 🔧 Types de Données

### Type Geometry (PostGIS)

Le type `Geometry` stocke les données spatiales au format WKT (Well-Known Text).

#### Formats supportés :
- `POINT(longitude latitude)` - Ex: `POINT(2.3522 48.8566)`
- `LINESTRING(x1 y1, x2 y2, ...)` - Ex: `LINESTRING(0 0, 1 1, 2 2)`
- `POLYGON((x1 y1, x2 y2, ...))` - Ex: `POLYGON((0 0, 4 0, 4 4, 0 4, 0 0))`
- `MULTIPOINT`, `MULTILINESTRING`, `MULTIPOLYGON`, `GEOMETRYCOLLECTION`

#### Utilisation dans l'interface :
- **Affichage** : Texte tronqué avec tooltip complet
- **Édition** : Zone de texte avec validation WKT et exemples

### Type Vector (pg_vector)

Le type `Vector` stocke les embeddings/vecteurs numériques.

#### Formats supportés :
- Tableau JSON : `[1.0, 2.0, 3.0, 4.0]`
- Valeurs séparées : `1.0, 2.0, 3.0, 4.0`
- Support des dimensions : `Vector:512` pour un vecteur de 512 dimensions

#### Utilisation dans l'interface :
- **Affichage** : Représentation compacte avec dimensions
- **Édition** : Zone de texte avec validation et aide contextuelle

## 🚀 Utilisation

### Création de colonnes

1. **Interface Web** : Sélectionner le type "Geometry" ou "Vector" lors de la création d'une colonne
2. **API** : Utiliser les types dans les définitions de schéma
3. **Import** : Les types sont détectés automatiquement depuis PostgreSQL

### Exemples d'utilisation

#### Données géométriques
```python
# Dans une formule Grist
# Créer un point à partir de coordonnées
$geometry = f"POINT({$longitude} {$latitude})"

# Calculer la distance entre deux points (requiert des fonctions PostGIS)
ST_Distance($point1, $point2)
```

#### Données vectorielles
```python
# Dans une formule Grist
# Créer un vecteur d'embeddings
$embedding = [0.1, 0.2, 0.3, 0.4, 0.5]

# Calculer la similarité cosinus (requiert des fonctions pg_vector)
1 - ($vector1 <=> $vector2)
```

## 🔍 Fonctions Disponibles

### Fonctions PostGIS (prévues)
- `ST_Distance(geom1, geom2)` - Distance entre géométries
- `ST_Area(geometry)` - Aire d'un polygone
- `ST_Length(geometry)` - Longueur d'une ligne
- `ST_Intersects(geom1, geom2)` - Test d'intersection
- `ST_Contains(geom1, geom2)` - Test de contenance

### Fonctions pg_vector (prévues)
- `cosine_distance(vector1, vector2)` - Distance cosinus
- `euclidean_distance(vector1, vector2)` - Distance euclidienne
- `dot_product(vector1, vector2)` - Produit scalaire

## 📊 Migration et Déploiement

### Migration Automatique

La migration `1750000000000-PostgresExtensions.ts` :
- Vérifie le type de base de données (PostgreSQL uniquement)
- Installe les extensions avec gestion d'erreurs
- Fournit des messages d'aide en cas de problème

### Rollback

Pour désinstaller les extensions :
```sql
DROP EXTENSION IF EXISTS vector CASCADE;
DROP EXTENSION IF EXISTS postgis CASCADE;
```

⚠️ **Attention** : Le rollback supprime toutes les données utilisant ces types.

## 🛠️ Développement

### Structure des fichiers

```
sandbox/grist/usertypes.py          # Types Python (Geometry, Vector)
app/plugin/GristData.ts             # Définitions TypeScript
app/common/gristTypes.ts            # Conversions SQL->Grist
app/client/widgets/GeometryEditor.ts # Interface géométrie
app/client/widgets/VectorEditor.ts   # Interface vecteur
app/gen-server/migration/           # Migration PostgreSQL
```

### Extensions futures

#### Interface géométrique avancée
- Carte interactive pour l'édition
- Import/Export GeoJSON, Shapefile
- Visualisation spatiale

#### Interface vectorielle avancée
- Visualisation de vecteurs
- Calcul de similarité en temps réel
- Intégration avec des services d'IA

#### Fonctions étendues
- Toutes les fonctions PostGIS
- Fonctions avancées pg_vector
- Opérateurs spécialisés

## 🐛 Résolution de problèmes

### Erreurs communes

#### "Extension not found"
```
Erreur : could not open extension control file
```
**Solution** : Installer les extensions système (voir Prérequis)

#### "Permission denied"
```
Erreur : permission denied to create extension
```
**Solution** : L'utilisateur PostgreSQL doit avoir les droits SUPERUSER

#### "Invalid WKT"
**Solution** : Vérifier la syntaxe WKT dans l'éditeur de géométrie

#### "Vector dimension mismatch"
**Solution** : S'assurer que le nombre d'éléments correspond au type déclaré

### Logs et débogage

Les erreurs sont loggées dans :
- Console navigateur (validation widgets)
- Logs serveur Grist (backend)
- Logs PostgreSQL (extensions)

## 📚 Ressources

- [Documentation PostGIS](https://postgis.net/docs/)
- [Documentation pg_vector](https://github.com/pgvector/pgvector)
- [Format WKT](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry)
- [Spécifications Grist Data Format](./grist-data-format.md)
