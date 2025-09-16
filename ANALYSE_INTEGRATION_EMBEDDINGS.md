# 🧠 ANALYSE INTÉGRATION SERVICE EMBEDDINGS POUR GRIST

## 📍 ÉTAT ACTUEL DU PROJET

### ✅ **RÉALISATIONS ACCOMPLIES**
- **Python natif** : Fonctions spatiales/vectorielles opérationnelles
- **Types Vector** : Type `Vector` disponible dans Grist
- **API REST** : Endpoints spéciaux `/spatial/*` et `/vector/*`
- **Showcase structuré** : Tables professionnelles avec colonnes typées
- **Fonctions VECTOR_SIMILARITY** : Comparaison de vecteurs fonctionnelle

### ❌ **MANQUE IDENTIFIÉ** 
- **Génération automatique d'embeddings** lors de l'ajout/modification d'enregistrements
- **Service d'embedding API** (Albert, OpenAI, Hugging Face, etc.)
- **Recherche RAG vectorielle** sur les données de tables
- **Auto-embedding** des champs texte en vecteurs

---

## 🎯 OBJECTIFS INTÉGRATION EMBEDDINGS

### **1. Auto-Embedding lors de CRUD**
Quand un utilisateur ajoute/modifie un enregistrement avec du texte, générer automatiquement l'embedding correspondant dans une colonne `Vector`.

### **2. Recherche RAG Vectorielle**  
Endpoint pour rechercher dans les données Grist par similarité sémantique :
```
POST /api/docs/{docId}/vector/search
{
  "query": "architecture gothique paris",
  "table": "Documents_Semantiques",
  "field": "Embedding_Vector",
  "limit": 5,
  "threshold": 0.8
}
```

### **3. Service Embeddings Configurable**
Support pour différents fournisseurs :
- **Albert API** (priorité)
- OpenAI Embeddings
- Hugging Face
- Modèles locaux

---

## 🔧 ANALYSE TECHNIQUE - MÉCANISMES GRIST DISPONIBLES

### **A. Système de Triggers/Webhooks** ✅
**Localisation** : `app/server/lib/Triggers.ts`

```typescript
// Système existant qui peut déclencher des actions externes
export class DocTriggers {
  private _webHookEventQueue: WebHookEvent[] = []
  
  // Appelé après modification d'enregistrements
  public async handle(localActionBundle: LocalActionBundle): Promise<ActionSummary>
}
```

**Potentiel** : Intercepter `BulkAddRecord`/`BulkUpdateRecord` pour déclencher génération d'embeddings.

### **B. Actions Python Interceptables** ✅
**Localisation** : `sandbox/grist/docactions.py`

```python
def BulkUpdateRecord(self, table_id, row_ids, columns):
    # Point d'interception parfait pour auto-embedding
    # Détecter modifications de colonnes texte
    # Déclencher génération embedding pour colonnes Vector liées
```

**Avantage** : Intégration native côté Python sandbox.

### **C. API Endpoints Extensible** ✅  
**Localisation** : `app/server/lib/SpatialEndpoints.ts` (notre ajout)

Pattern établi pour ajouter de nouveaux endpoints spécialisés :
```typescript
export function addEmbeddingEndpoints(app: express.Application, docManager: DocManager): void {
  app.post('/api/docs/:docId/embeddings/generate', ...)
  app.post('/api/docs/:docId/vector/search', ...)
}
```

### **D. Types Vector Intégrés** ✅
**Localisation** : `app/client/widgets/UserType.ts`

Type `Vector` déjà reconnu par Grist, prêt pour stockage d'embeddings.

---

## 🚀 STRATÉGIE D'INTÉGRATION PROPOSÉE

### **Phase 1 : Service Embeddings Externe** 
**Objectif** : Créer un service autonome pour générer des embeddings

#### **1.1. Service Albert API** 
```typescript
// app/server/lib/EmbeddingService.ts
export class EmbeddingService {
  constructor(
    private provider: 'albert' | 'openai' | 'local',
    private apiKey: string,
    private baseUrl: string
  ) {}
  
  async generateEmbedding(text: string): Promise<number[]>
  async generateBatchEmbeddings(texts: string[]): Promise<number[][]>
}
```

#### **1.2. Configuration par Document**
Permettre à chaque document Grist de configurer son service d'embeddings :
```javascript
// Stocké dans _grist_DocInfo ou table dédiée
{
  embedding_provider: 'albert',
  embedding_api_key: 'encrypted_key',
  embedding_endpoint: 'https://albert-api.example.com/embed',
  auto_embedding_enabled: true
}
```

### **Phase 2 : Auto-Embedding Triggers**
**Objectif** : Génération automatique lors des modifications

#### **2.1. Détection Intelligente**
```python
# sandbox/grist/usertypes.py - Extension 
def detect_embedding_triggers(table_id, columns):
    """
    Détecter si une table a des colonnes Vector liées à des colonnes Text
    via métadonnées ou nommage conventionnel
    """
    # Exemple: colonne "Description" + colonne "Description_Vector"
```

#### **2.2. Hook d'Actions Python**  
```python
# sandbox/grist/docactions.py - Modification
def BulkUpdateRecord(self, table_id, row_ids, columns):
    # Logique existante...
    
    # NOUVEAU: Détecter besoins embeddings
    embedding_requests = self._detect_embedding_needs(table_id, columns)
    if embedding_requests:
        self._queue_embedding_generation(embedding_requests)
```

#### **2.3. Queue Asynchrone**
Utiliser le système de triggers existant pour traitement asynchrone :
```typescript
// Extension de app/server/lib/Triggers.ts
private async _processEmbeddingQueue() {
  // Traiter les demandes d'embedding en arrière-plan
  // Mettre à jour les colonnes Vector correspondantes
}
```

### **Phase 3 : API Recherche RAG**
**Objectif** : Endpoints de recherche sémantique

#### **3.1. Endpoint de Recherche**
```typescript
// app/server/lib/EmbeddingEndpoints.ts
app.post('/api/docs/:docId/vector/search', 
  withDoc(async (activeDoc, req, res) => {
    const { query, table, field, limit, threshold } = req.body;
    
    // 1. Générer embedding de la query
    const queryVector = await embeddingService.generateEmbedding(query);
    
    // 2. Recherche par similarité dans la table
    const results = await activeDoc.pyCall('VECTOR_SEARCH', [
      table, field, queryVector, limit, threshold
    ]);
    
    res.json({ results });
  })
);
```

#### **3.2. Fonction Python RAG**
```python  
# sandbox/grist/usertypes.py - Nouvelle fonction
def VECTOR_SEARCH(table_name, vector_column, query_vector, limit=10, threshold=0.7):
    """
    Recherche vectorielle dans une table Grist
    Retourne les enregistrements les plus similaires
    """
    # Implémentation recherche + ranking par similarité
```

---

## 🎮 FONCTIONNALITÉS PERMISES

### **1. Auto-Embedding Transparent**
```
Utilisateur ajoute: "Guide architecture gothique Notre-Dame"
→ Système génère automatiquement: [0.8, 0.1, 0.9, 0.2, ...]
→ Stocké dans colonne Vector liée
```

### **2. Recherche Sémantique Native**
```python
# Dans formules Grist
=VECTOR_SEARCH("Documents", "Embedding", "architecture paris", 5, 0.8)
```

### **3. API REST Recherche**
```bash
curl -X POST /api/docs/docId/vector/search \
  -H "Authorization: Bearer key" \
  -d '{"query": "tourisme paris", "table": "Documents"}'
```

### **4. Batch Processing**
```
Traitement en lot de documents existants
Régénération d'embeddings après changement de modèle  
```

### **5. Configuration Flexible**
- Choix du fournisseur d'embeddings par document
- Seuils de similarité configurables
- Colonnes source/target personnalisables

---

## 🔧 PLAN DE DÉVELOPPEMENT

### **Étape 1 : Infrastructure Service** (2-3 jours)
1. ✅ Créer `EmbeddingService.ts` avec support Albert API
2. ✅ Ajouter configuration dans `_grist_DocInfo`  
3. ✅ Tests de connectivité et génération d'embeddings

### **Étape 2 : Auto-Embedding** (3-4 jours)
1. ✅ Modifier `docactions.py` pour détecter besoins embeddings
2. ✅ Intégrer queue asynchrone dans `Triggers.ts`
3. ✅ Tests d'auto-génération lors CRUD

### **Étape 3 : Recherche RAG** (2-3 jours)  
1. ✅ Créer `VECTOR_SEARCH` fonction Python
2. ✅ Ajouter endpoints `/vector/search`
3. ✅ Tests recherche et ranking

### **Étape 4 : Interface Utilisateur** (optionnel)
1. Widget de configuration embeddings
2. Widget de recherche sémantique
3. Visualisation des résultats

---

## ❓ DÉCISIONS À PRENDRE

### **A. Fournisseur d'Embeddings Prioritaire**
- **Albert API** - Recommandé si API stable
- **OpenAI** - Fallback robuste
- **Local (Sentence-Transformers)** - Pas de dépendances externes

### **B. Stratégie de Détection Auto-Embedding**
- **Convention nommage** : `Description` + `Description_Vector`
- **Métadonnées explicites** : Configuration dans _grist_Tables_column
- **Scan automatique** : Détection Text + Vector dans même table

### **C. Mode de Déclenchement**
- **Synchrone** : Embedding généré immédiatement (plus lent)  
- **Asynchrone** : Queue background (recommandé)
- **Hybride** : Synchrone si rapide, sinon asynchrone

---

## 🎯 PROCHAINES ACTIONS RECOMMANDÉES

### **DÉMARRAGE IMMÉDIAT** ⚡
1. **Confirmer fournisseur embeddings** (Albert API ?)
2. **Créer EmbeddingService basique** 
3. **Tester génération embeddings simple**
4. **Implémenter auto-detection colonnes**

### **QUESTIONS POUR VOUS** 
1. **Quel service d'embedding préférez-vous** ? (Albert API, OpenAI, autre ?)
2. **Avez-vous les credentials/endpoints** pour Albert API ?
3. **Préférence synchrone vs asynchrone** pour l'auto-embedding ?
4. **Tables de test prioritaires** pour la validation ?

**Prêt à démarrer dès validation de ces points !** 🚀
