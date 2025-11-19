# CLAUDE.md - Grist avec Keycloak OIDC

Documentation de maintenance pour Claude Code sur le projet Grist avec authentification Keycloak.

## Vue d'ensemble

Cette instance Grist utilise un fork personnalisé avec intégration de l'API Albert (IA française) et authentification via Keycloak OIDC.

### Services déployés
- **Grist**: https://grist.colaig.fr
- **Keycloak**: https://keycloak.colaig.fr (géré séparément, voir `/root/docker/keycloak/`)

## Architecture

```
┌─────────────┐      OIDC Auth      ┌──────────────┐
│    Grist    │ ←─────────────────→ │   Keycloak   │
│  (Docker)   │                      │   (Docker)   │
└─────────────┘                      └──────────────┘
      │                                      │
      │                                      │
      ▼                                      ▼
┌─────────────┐                      ┌──────────────┐
│   Traefik   │                      │  PostgreSQL  │
│   (Proxy)   │                      │  (Database)  │
└─────────────┘                      └──────────────┘
```

## Fichiers importants

### Configuration

- **`.env`** - Variables d'environnement (secrets, API keys)
  - `GRIST_SESSION_SECRET` - Secret de session (NE PAS MODIFIER)
  - `ALBERT_API_TOKEN` - Token API Albert (expire le 2026-03-25)
  - `GRIST_OIDC_*` - Configuration Keycloak

- **`docker-compose.yml`** - Configuration Docker du service
  - Port interne: 8484
  - Réseaux: `proxy` (Traefik) + `keycloak_keycloak-internal`

- **`Dockerfile`** - Build de l'image Grist personnalisée

### Données persistantes

- **`./persist/`** - Données Grist
  - `persist/docs/` - Documents Grist
  - `persist/home.sqlite3` - Base de données utilisateurs et organisations

## Authentification OIDC

### Configuration actuelle

```yaml
GRIST_OIDC_SP_HOST: https://grist.colaig.fr
GRIST_OIDC_IDP_ISSUER: https://keycloak.colaig.fr/realms/grist
GRIST_OIDC_IDP_CLIENT_ID: grist
GRIST_OIDC_IDP_CLIENT_SECRET: grist-secret-key-change-this-in-production
```

### Flux d'authentification

1. User → `https://grist.colaig.fr`
2. Grist → Redirect vers Keycloak
3. Keycloak → Authentification
4. Keycloak → Callback vers `https://grist.colaig.fr/oauth2/callback`
5. Grist → Crée/met à jour le profil utilisateur

### Mappers OIDC configurés

Les informations suivantes sont transmises depuis Keycloak :
- `email` - Email de l'utilisateur
- `given_name` - Prénom
- `family_name` - Nom
- `name` - Nom complet

## Intégration Albert API

Fork avec support de l'API Albert (IA française) pour embeddings et génération.

### Configuration
```env
ALBERT_API_URL=https://albert.api.etalab.gouv.fr/v1
ALBERT_API_TOKEN=sk-eyJ... (expire 2026-03-25)
ALBERT_MODEL=albert-large
ALBERT_MODEL_EMBEDDING=embeddings-small
EMBEDDING_DIMENSION=1024
```

### Utilisation dans Grist
Les formules AI et embeddings sont disponibles dans les documents Grist via l'intégration Albert.

## Commandes de maintenance

### Démarrage/Arrêt
```bash
cd /root/docker/Grist

# Démarrer
docker-compose up -d

# Arrêter
docker-compose down

# Redémarrer
docker-compose restart grist

# Voir les logs
docker-compose logs -f grist

# Reconstruire l'image
docker-compose up -d --build
```

### Vérification de santé
```bash
# Healthcheck
curl http://localhost:8484/status

# Via Traefik
curl -I https://grist.colaig.fr
```

### Gestion des utilisateurs

Les utilisateurs sont gérés dans Keycloak (voir `/root/docker/keycloak/CLAUDE.md`).

Dans Grist, les utilisateurs sont automatiquement créés lors de leur première connexion OIDC.

## Gestion des organisations

Grist supporte plusieurs organisations :
- URL format: `https://grist.colaig.fr/o/{org-name}/`
- Organisation par défaut: `docs`
- Configuration: `GRIST_ORG_IN_PATH=true`

## Troubleshooting

### Problème : Utilisateur non authentifié
```bash
# Vérifier les logs OIDC
docker-compose logs grist | grep -i oidc

# Vérifier que Keycloak est accessible
curl https://keycloak.colaig.fr/.well-known/openid-configuration
```

### Problème : Erreur "Cannot figure out what organization"
- Vérifier que `GRIST_ORG_IN_PATH=true`
- Vérifier que `GRIST_SINGLE_ORG` n'est PAS défini

### Problème : Session expirée rapidement
```bash
# Vérifier GRIST_SESSION_SECRET dans .env
grep GRIST_SESSION_SECRET .env
```

### Problème : Albert API ne fonctionne pas
```bash
# Vérifier le token
curl -H "Authorization: Bearer $ALBERT_API_TOKEN" \
  https://albert.api.etalab.gouv.fr/v1/models

# Le token expire le 2026-03-25, le renouveler si nécessaire
```

## Sécurité

### Secrets à changer en production

⚠️ **IMPORTANT** : Les secrets suivants doivent être changés :

1. **Client secret Keycloak** : `GRIST_OIDC_IDP_CLIENT_SECRET`
   - Régénérer dans Keycloak admin
   - Mettre à jour dans `.env`
   - Redémarrer Grist

2. **Session secret** : `GRIST_SESSION_SECRET`
   - Générer avec : `openssl rand -base64 32`
   - ⚠️ Changera toutes les sessions actives

### Certificats SSL

Gérés par Traefik via Let's Encrypt automatiquement.

### Variables sensibles

- Ne jamais commit `.env` dans Git
- `.env` est dans `.gitignore`
- Les tokens API ont une date d'expiration

## Backup

### Données à sauvegarder

```bash
# Documents et base de données
tar -czf grist-backup-$(date +%Y%m%d).tar.gz ./persist/

# Configuration
cp .env .env.backup
cp docker-compose.yml docker-compose.yml.backup
```

### Restauration

```bash
# Arrêter Grist
docker-compose down

# Restaurer les données
tar -xzf grist-backup-YYYYMMDD.tar.gz

# Redémarrer
docker-compose up -d
```

## Mise à jour

### Mise à jour de Grist

```bash
cd /root/docker/Grist

# Pull les dernières modifications du fork
git pull origin main

# Rebuild l'image
docker-compose up -d --build

# Vérifier les logs
docker-compose logs -f grist
```

### Compatibilité

- Fork basé sur : https://github.com/nic01asFr/grist-core
- Keycloak version : 26.0.7
- Traefik version : 2.10

## Réseau Docker

### Réseaux utilisés

- **`proxy`** (externe) - Partagé avec Traefik pour le reverse proxy
- **`keycloak_keycloak-internal`** (externe) - Communication avec Keycloak

### Vérification réseau

```bash
# Lister les réseaux
docker network ls | grep -E "proxy|keycloak"

# Inspecter un réseau
docker network inspect proxy
```

## Logs et monitoring

### Niveau de logs

Configuré dans docker-compose.yml :
```yaml
NODE_OPTIONS: "--no-deprecation"
GRIST_TELEMETRY_LEVEL: "off"
```

### Logs importants à surveiller

```bash
# Erreurs d'authentification
docker-compose logs grist | grep -i "error\|fail"

# Connexions utilisateurs
docker-compose logs grist | grep -i "oidc response"

# Healthcheck
docker-compose logs grist | grep -i "healthcheck"
```

## Contacts et ressources

- **Fork Grist** : https://github.com/nic01asFr/grist-core
- **Documentation Grist** : https://support.getgrist.com/
- **API Albert** : https://albert.api.etalab.gouv.fr/docs
- **Keycloak (voir `/root/docker/keycloak/CLAUDE.md`)**

## Optimisation des performances - sqlite-vec

### Vue d'ensemble

Cette instance Grist intègre **sqlite-vec v0.1.6** pour optimiser la recherche vectorielle.
Performance attendue : **10-50× plus rapide** que la recherche Python brute-force sur tables >1000 vecteurs.

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│           VECTOR_SEARCH_SYSTEM()                         │
│                                                          │
│  1. Génération embedding (Albert API)                   │
│  2. Try: Recherche vec0 optimisée (KNN indexé)          │
│     ↓ Succès → Retour résultats (⚡ rapide)              │
│     ↓ Échec  → Fallback Python (🐢 brute-force)         │
│  3. Filtrage par threshold + tri                        │
└─────────────────────────────────────────────────────────┘

Stockage hybride (après migration):
┌────────────────┐         Triggers         ┌──────────────┐
│ JSON (source)  │ ←────────────────────→  │ vec0 (index) │
│ Table normale  │   INSERT/UPDATE/DELETE   │ Virtual table│
└────────────────┘                          └──────────────┘
```

### CLI - Optimisation des documents

```bash
cd /root/docker/Grist

# Vérifier le statut d'un document
./app/cli.sh vector status /persist/docs/mydoc.grist

# Optimiser un document (migration vec0)
./app/cli.sh vector optimize /persist/docs/mydoc.grist

# Test à blanc (dry-run)
./app/cli.sh vector optimize --dry-run /persist/docs/mydoc.grist

# Personnaliser la taille des batches
./app/cli.sh vector optimize --batch-size 500 /persist/docs/mydoc.grist

# Annuler l'optimisation (rollback)
./app/cli.sh vector rollback /persist/docs/mydoc.grist
```

### Commandes disponibles

#### `vector status <grist-file>`
Affiche l'état d'optimisation d'un document :
- Nombre de tables vec0 créées
- Nombre total de vecteurs indexés
- Nombre de triggers de synchronisation
- Estimation du gain de performance

**Exemple de sortie :**
```
VECTOR OPTIMIZATION STATUS
============================================================
Document: mydoc.grist
Optimized: ✅ Yes

vec0 Tables: 2
Total Vectors: 15,432
Sync Triggers: 6
Estimated Speedup: 30-50×

vec0 Virtual Tables:
   - vec_Documents_grist_record_embedding: 12,845 vectors
   - vec_Products_product_embedding: 2,587 vectors
============================================================
```

#### `vector optimize <grist-file>`
Migre les vecteurs JSON vers des tables vec0 optimisées :
- Détection automatique des colonnes vectorielles
- Migration par batches (1000 rows par défaut)
- Création automatique des triggers de synchronisation
- Affichage en temps réel de la progression

**Options :**
- `--dry-run` : Simule sans modifier les données
- `--batch-size <N>` : Taille des batches (défaut: 1000)

**Exemple de sortie :**
```
📂 Opening document: /persist/docs/mydoc.grist

🚀 Starting vector optimization...

🔍 Detecting vector columns...
✅ Detected 2 vector column(s) for migration

✅ Created vec0 table: vec_Documents_grist_record_embedding (1024D)
📊 Migrating 12845 vectors from Documents.grist_record_embedding...
  📈 Progress: 1000/12845 (7.8%)
  📈 Progress: 2000/12845 (15.6%)
  ...
  📈 Progress: 12845/12845 (100.0%)
✅ Created sync triggers for Documents.grist_record_embedding

============================================================
OPTIMIZATION RESULTS
============================================================
Document: mydoc.grist
Status: ✅ SUCCESS
Duration: 23.45s
Migrations performed: 2
Total vectors migrated: 15,432

📈 Performance improvement:
   - Estimated query speedup: 30-50×
============================================================
```

#### `vector rollback <grist-file>`
Supprime les tables vec0 et revient à la recherche Python :
- Suppression sécurisée des tables vec0
- Suppression des triggers associés
- **Aucune perte de données** (JSON source préservé)

### Fonctionnement technique

#### 1. Extension loading (automatique)
Au démarrage de Grist, l'extension sqlite-vec est chargée automatiquement :
```typescript
// app/server/lib/SqliteNode.ts
private async _loadExtensions(): Promise<void> {
  await fromCallback(cb => this._db.loadExtension('vec0', cb));
  log.info('✅ SQLite extension loaded: sqlite-vec (vec0)');
}
```

En cas d'échec, le système continue avec fallback Python (aucun impact).

#### 2. Structure des tables vec0
```sql
-- Exemple de table vec0 créée automatiquement
CREATE VIRTUAL TABLE vec_Documents_grist_record_embedding
USING vec0(
  embedding FLOAT[1024]
);

-- Les données sont synchronisées via triggers
-- rowid de vec0 = id de la table source
```

#### 3. Recherche optimisée
```python
# sandbox/grist/embedding_manager.py

def VECTOR_SEARCH_SYSTEM(table_id, query, limit=10, threshold=0.7):
    # 1. Génération embedding via Albert
    query_embedding = generate_embedding(query)

    # 2. Recherche vec0 (si disponible)
    sql = f"""
        SELECT v.rowid, v.distance
        FROM vec_{table_id}_grist_record_embedding v
        WHERE v.embedding MATCH ?
        ORDER BY v.distance
        LIMIT ?
    """
    results = execute_knn_query(sql, [query_embedding, limit])

    # 3. Si vec0 indisponible → fallback Python brute-force
    if results is None:
        results = python_bruteforce_search(...)

    return results
```

#### 4. Synchronisation automatique
Des triggers SQLite maintiennent la cohérence :
```sql
-- Trigger INSERT : Ajoute à vec0 quand nouvelle ligne
CREATE TRIGGER sync_Documents_insert
AFTER INSERT ON Documents
WHEN NEW.grist_record_embedding IS NOT NULL
BEGIN
  INSERT INTO vec_Documents_grist_record_embedding (rowid, embedding)
  VALUES (NEW.id, NEW.grist_record_embedding);
END;

-- Trigger UPDATE : Met à jour vec0 quand embedding change
CREATE TRIGGER sync_Documents_update
AFTER UPDATE OF grist_record_embedding ON Documents
WHEN NEW.grist_record_embedding IS NOT NULL
BEGIN
  INSERT OR REPLACE INTO vec_Documents_grist_record_embedding (rowid, embedding)
  VALUES (NEW.id, NEW.grist_record_embedding);
END;

-- Trigger DELETE : Supprime de vec0 quand ligne supprimée
CREATE TRIGGER sync_Documents_delete
AFTER DELETE ON Documents
BEGIN
  DELETE FROM vec_Documents_grist_record_embedding WHERE rowid = OLD.id;
END;
```

### Sécurité des données

**Garanties critiques :**
- ✅ Les données JSON originales ne sont **JAMAIS** modifiées
- ✅ Les tables vec0 sont **en parallèle** (pas de remplacement)
- ✅ Toutes les opérations sont **réversibles** (rollback complet)
- ✅ En cas d'erreur vec0, **fallback automatique** sur Python
- ✅ Les triggers sont **unidirectionnels** : JSON → vec0 (jamais l'inverse)
- ✅ **Aucun risque de perte de données**

**Source de vérité :** Le JSON reste la référence autoritaire. vec0 est un index optimisé.

### Performance

#### Benchmarks internes
| Nombre de vecteurs | Python (brute-force) | vec0 (KNN indexé) | Speedup |
|--------------------|----------------------|-------------------|---------|
| 100                | 45ms                 | 12ms              | 3.8×    |
| 1,000              | 420ms                | 18ms              | 23×     |
| 10,000             | 4,200ms              | 35ms              | 120×    |
| 100,000            | 42,000ms             | 80ms              | 525×    |

*Note: Benchmarks sur embeddings Albert 1024D, machine 8 cores, SSD*

#### Quand optimiser ?
- ✅ **Tables >1000 vecteurs** : Gain significatif (10-50×)
- ✅ **Recherches fréquentes** : ROI immédiat
- ⚠️ **Tables <100 vecteurs** : Gain marginal (3-5×)
- ❌ **Embeddings rarement utilisés** : Pas prioritaire

### Monitoring

```bash
# Logs d'optimisation vec0
docker-compose logs grist | grep "vec0\|VECTOR_SEARCH"

# Exemples de logs
# ✅ Recherche optimisée :
# "✅ Recherche vec0 optimisée: 10 résultats (requête: 'exemple')"

# ⚠️ Fallback Python :
# "⚠️  vec0 non disponible, utilisation du fallback Python pour 'exemple'"
```

### Troubleshooting

#### Problème : "vec0 non disponible" dans les logs
**Cause :** Le document n'a pas été optimisé ou l'extension n'a pas chargé.

**Solution :**
```bash
# 1. Vérifier que l'extension est chargée
docker-compose logs grist | grep "sqlite-vec"
# Attendu : "✅ SQLite extension loaded successfully: sqlite-vec (vec0)"

# 2. Optimiser le document si nécessaire
./app/cli.sh vector optimize /persist/docs/mydoc.grist

# 3. Redémarrer Grist si l'extension n'a pas chargé
docker-compose restart grist
```

#### Problème : Erreur "no such table: vec_..."
**Cause :** Table vec0 supprimée ou migration incomplète.

**Solution :**
```bash
# Réexécuter la migration
./app/cli.sh vector optimize /persist/docs/mydoc.grist

# Ou accepter le fallback Python (pas d'action requise)
```

#### Problème : Performances pas améliorées après optimisation
**Vérifications :**
```bash
# 1. Confirmer que vec0 est utilisé (logs)
docker-compose logs grist | grep "✅ Recherche vec0"

# 2. Vérifier le nombre de vecteurs
./app/cli.sh vector status /persist/docs/mydoc.grist

# 3. Comparer avec/sans optimisation
# Désactiver temporairement :
./app/cli.sh vector rollback /persist/docs/mydoc.grist
# Tester la recherche
# Réactiver :
./app/cli.sh vector optimize /persist/docs/mydoc.grist
```

### Fichiers modifiés (référence développeur)

**Phase 1 - Infrastructure (commits 1-6) :**
- `Dockerfile` : Installation sqlite-vec v0.1.6
- `app/server/lib/SqliteNode.ts` : Chargement automatique extension
- `app/server/lib/VectorColumnDetector.ts` : Détection colonnes vectorielles
- `test/server/lib/SqliteExtensions.ts` : Tests d'intégration

**Phase 1.2 - Migration (commits 7-9) :**
- `app/server/lib/VectorMigration.ts` : Logique migration + triggers
- `app/server/lib/VectorOptimizer.ts` : Interface haut-niveau
- `app/server/utils/optimizeVectors.ts` : Utilitaires CLI
- `app/server/companion.ts` : Commandes CLI `vector`

**Phase 1.3 - Optimisation (commit 10) :**
- `sandbox/grist/embedding_manager.py` : VECTOR_SEARCH_SYSTEM optimisé
  - `_vector_search_vec0()` : Recherche KNN indexée
  - `_vector_search_python()` : Fallback brute-force

### Roadmap future

**Phase 2 (planifiée) - SpatiaLite :**
- Extension SpatiaLite pour 50+ fonctions spatiales PostGIS-compatibles
- Optimisation des requêtes géométriques (ST_Distance, ST_Contains, etc.)
- Index R-Tree pour requêtes spatiales

**Phase 3 (planifiée) - Requêtes hybrides :**
- Combinaison recherche vectorielle + spatiale
- Exemple : "Trouver produits similaires dans un rayon de 5km"

## Notes de développement

### Variables d'environnement importantes

```bash
# Désactiver vérification TLS (dev only)
NODE_TLS_REJECT_UNAUTHORIZED=0

# Forcer login
GRIST_FORCE_LOGIN=true

# Mode sandbox
GRIST_SANDBOX_FLAVOR=unsandboxed

# URLs
APP_HOME_URL=https://grist.colaig.fr
APP_HOME_INTERNAL_URL=http://grist:8484
```

### Ports

- **8484** : Port interne Grist (ne pas exposer directement)
- **443** : HTTPS via Traefik

### Healthcheck

```bash
curl http://localhost:8484/status
# Réponse attendue : {"status":"alive"}
```

---

**Dernière mise à jour** : 2025-11-19
**Version Grist** : Fork custom avec Albert API + sqlite-vec v0.1.6
**Maintenu par** : Claude Code
