# 🚀 Guide de Démarrage Rapide - Grist avec PostGIS et pg_vector

## 🎯 État Actuel

✅ **Grist** : Interface web accessible sur http://localhost:8484  
✅ **pg_vector 0.5.1** : Extension vectorielle installée et testée  
❌ **PostGIS** : Non disponible (nécessite image Docker différente)  
✅ **PostgreSQL 15** : Base de données opérationnelle sur port 5433

## 🔧 Services Docker

```bash
# Vérifier les services
docker-compose -f docker-compose-pgvector.yml ps

# Voir les logs
docker-compose -f docker-compose-pgvector.yml logs grist
docker-compose -f docker-compose-pgvector.yml logs grist-db-vector

# Redémarrer si nécessaire
docker-compose -f docker-compose-pgvector.yml restart grist
```

## 🔢 Utilisation du Type Vector

### 1. Créer une table avec colonnes vectorielles

Dans l'interface Grist (http://localhost:8484) :
1. Créer une nouvelle table
2. Ajouter une colonne de type **"Vector"**
3. Saisir des vecteurs au format :

```
[1.0, 2.0, 3.0, 4.0, 5.0]        # Format JSON
1.0, 2.0, 3.0, 4.0, 5.0          # Format CSV
```

### 2. Exemple de données vectorielles

| Document | Embedding Vector |
|----------|------------------|
| Article 1 | `[0.1, 0.2, 0.3, 0.4]` |
| Article 2 | `[0.5, 0.6, 0.7, 0.8]` |
| Article 3 | `[0.9, 1.0, 1.1, 1.2]` |

### 3. Formules avec similarité vectorielle

```python
# Dans une formule Grist (fonctionnalité future)
cosine_similarity($vector1, $vector2)
euclidean_distance($vector1, $vector2)
```

## 🗺️ Utilisation du Type Geometry

### 1. Créer une table avec colonnes spatiales

**Note :** PostGIS n'est pas installé dans cette configuration, mais le type Geometry de Grist accepte les données WKT :

| Lieu | Coordonnées |
|------|-------------|
| Paris | `POINT(2.3522 48.8566)` |
| Londres | `POINT(-0.1276 51.5074)` |
| Rectangle | `POLYGON((0 0, 4 0, 4 4, 0 4, 0 0))` |

### 2. Formats WKT supportés

```
POINT(longitude latitude)
LINESTRING(x1 y1, x2 y2, x3 y3)
POLYGON((x1 y1, x2 y2, x3 y3, x1 y1))
MULTIPOINT((x1 y1), (x2 y2))
```

## 🧪 Tests Direct PostgreSQL

### Test pg_vector
```bash
# Se connecter à PostgreSQL
docker exec -it grist-postgis-pgvector-grist-db-vector-1 psql -U grist -d grist

# Tester la similarité vectorielle
SELECT name, embedding, embedding <=> '[1,2,3]' as similarity 
FROM vector_test 
ORDER BY similarity;

# Recherche k-plus-proches-voisins
SELECT name, embedding <-> '[1,2,3]' as distance 
FROM vector_test 
ORDER BY distance 
LIMIT 2;
```

### Créer une table avec vecteurs
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title TEXT,
    content TEXT,
    embedding VECTOR(384)  -- Dimensions pour sentence-transformers
);

INSERT INTO documents (title, content, embedding) VALUES 
('Document 1', 'Contenu...', '[0.1,0.2,0.3,0.4]'),
('Document 2', 'Autre...', '[0.5,0.6,0.7,0.8]');
```

## 🔄 Opérations de Maintenance

### Redémarrer complètement
```bash
docker-compose -f docker-compose-pgvector.yml down
docker-compose -f docker-compose-pgvector.yml up -d
```

### Sauvegarder les données
```bash
# Sauvegarder la base
docker exec grist-postgis-pgvector-grist-db-vector-1 pg_dump -U grist grist > backup.sql

# Sauvegarder les documents Grist
docker cp grist-postgis-pgvector-grist-1:/persist ./backup-grist/
```

### Accès direct aux services
- **Grist UI** : http://localhost:8484
- **PostgreSQL** : localhost:5433 (user: grist, password: grist_demo_2024)
- **Redis** : Interne au stack Docker

## 📊 Cas d'Usage Avancés

### 1. Recherche Sémantique
Utiliser pg_vector pour la recherche de similarité de documents basée sur des embeddings de transformers.

### 2. Recommandation
Calculer la similarité entre profils utilisateurs représentés comme des vecteurs.

### 3. Classification
Trouver les vecteurs les plus proches d'un point de référence pour la classification.

### 4. Données Géospatiales (futures)
Une fois PostGIS ajouté, supporter les requêtes spatiales complexes.

## 🎛️ Configuration Personnalisée

Pour modifier la configuration, éditer :
- `.env` : Variables d'environnement
- `docker-compose-pgvector.yml` : Configuration des services
- `init-extensions-pgvector.sql` : Script d'initialisation PostgreSQL

## 🐛 Résolution de Problèmes

### Interface inaccessible
```bash
# Vérifier les ports
netstat -an | findstr :8484

# Vérifier les logs
docker-compose -f docker-compose-pgvector.yml logs grist
```

### Erreur de connexion base
```bash
# Redémarrer dans l'ordre
docker-compose -f docker-compose-pgvector.yml restart grist-db-vector
docker-compose -f docker-compose-pgvector.yml restart grist
```

### pg_vector ne fonctionne pas
```bash
# Vérifier l'extension
docker exec grist-postgis-pgvector-grist-db-vector-1 psql -U grist -d grist -c "\dx"
```

---

🎉 **Grist avec pg_vector est maintenant opérationnel !**

Accédez à http://localhost:8484 pour commencer à créer des tables avec des types Vector et Geometry.
