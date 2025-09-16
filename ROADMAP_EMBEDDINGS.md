# 🛣️ ROADMAP INTÉGRATION EMBEDDINGS - GRIST

## 📊 **OÙ NOUS EN SOMMES**

```
🏗️ ARCHITECTURE GRIST EXTENSIONS
├── ✅ Types Grist (Geometry, Vector)
├── ✅ Python Sandbox (ST_DISTANCE, VECTOR_SIMILARITY)  
├── ✅ API REST (/spatial/*, /vector/*)
├── ✅ Showcase Structuré (4 tables spécialisées)
└── ❌ Auto-Embeddings Service [PROCHAINE ÉTAPE]
```

### **ÉTAT TECHNIQUE VALIDÉ** ✅
- Container `grist-showcase-final` opérationnel
- Python natif confirmé (ST_DISTANCE: 111km, VECTOR_SIMILARITY: 1.0)
- 4 tables créées : Monuments, Zones, Documents, Analyses
- Types Vector/Geometry fonctionnels dans l'interface

### **LIMITATION ACTUELLE** ⚠️
- Documents sémantiques **vides** (pas de génération d'embeddings automatique)
- Pas de service **Albert API** intégré
- Pas de **recherche RAG** vectorielle
- Embeddings **manuels** uniquement

---

## 🎯 **FONCTIONNALITÉS CIBLES**

### **1. Auto-Embedding Transparent** 🤖
```
Utilisateur tape: "Guide architecture gothique Notre-Dame"
           ↓ (automatique)
Système génère: [0.8, 0.1, 0.9, 0.2, 0.7, ...]
           ↓
Stocké en: colonne Vector associée
```

### **2. Recherche RAG Native** 🔍  
```python
# Dans formules Grist
=VECTOR_SEARCH("Documents", "Embedding", "architecture paris", 5)

# Via API REST
POST /api/docs/{docId}/vector/search
{"query": "tourisme paris", "limit": 5}
```

### **3. Service Albert API Intégré** 🧠
- Configuration par document
- Support multi-fournisseurs (Albert, OpenAI, local)
- Traitement batch et temps réel

---

## 🔧 **PLAN TECHNIQUE DÉTAILLÉ**

### **PHASE 1 : SERVICE EMBEDDINGS** (2-3 jours)
```typescript
// app/server/lib/EmbeddingService.ts
export class EmbeddingService {
  async generateEmbedding(text: string): Promise<number[]>
  async connectAlbertAPI(apiKey: string, endpoint: string)
}
```

**Livrables** :
- ✅ Classe EmbeddingService avec Albert API
- ✅ Configuration par document dans _grist_DocInfo
- ✅ Tests de connectivité et génération

### **PHASE 2 : AUTO-EMBEDDING HOOKS** (3-4 jours)
```python
# sandbox/grist/docactions.py - Extension
def BulkUpdateRecord(self, table_id, row_ids, columns):
    # Détection modifications colonnes Text
    # Déclenchement auto-embedding pour colonnes Vector liées
```

**Livrables** :
- ✅ Hooks Python dans docactions.py
- ✅ Détection intelligente colonnes Text→Vector
- ✅ Queue asynchrone pour traitement background

### **PHASE 3 : RECHERCHE RAG** (2-3 jours)
```python
# sandbox/grist/usertypes.py - Nouvelle fonction
def VECTOR_SEARCH(table, vector_col, query, limit=10, threshold=0.7):
    # Recherche par similarité sémantique dans tables Grist
```

**Livrables** :
- ✅ Fonction VECTOR_SEARCH Python native  
- ✅ Endpoint /api/docs/{docId}/vector/search
- ✅ Intégration dans formules Grist

---

## 🎮 **MÉCANISMES GRIST IDENTIFIÉS**

### **A. Triggers/Webhooks System** ✅
**Fichier** : `app/server/lib/Triggers.ts`
- Système robuste pour déclencher actions externes
- Queue événements avec retry automatique
- **Usage** : Déclenchement génération embeddings

### **B. Python Actions Hooks** ✅  
**Fichier** : `sandbox/grist/docactions.py`
- Interception BulkAddRecord/BulkUpdateRecord
- Accès direct aux données modifiées
- **Usage** : Détection besoins auto-embedding

### **C. API Endpoints Extensibles** ✅
**Fichier** : `app/server/lib/SpatialEndpoints.ts` (notre ajout)
- Pattern établi pour nouveaux endpoints spécialisés
- Accès ActiveDoc et PyCall
- **Usage** : Endpoints recherche RAG

### **D. Types Vector Intégrés** ✅
**Fichier** : `app/client/widgets/UserType.ts`
- Type Vector reconnu nativement
- Stockage/affichage dans interface
- **Usage** : Stockage embeddings générés

---

## ❓ **QUESTIONS DÉCISIONNELLES**

### **1. SERVICE D'EMBEDDINGS** 
```
A) Albert API   - API française, spécialisée
B) OpenAI       - Robuste, payant, facile intégration  
C) Hugging Face - Gratuit, nombreux modèles
D) Local        - Offline, pas de dépendances externes
```

### **2. MODE DÉCLENCHEMENT**
```
A) Synchrone   - Immédiat mais bloque l'interface
B) Asynchrone  - Background, UX fluide (recommandé)
C) Hybride     - Rapide→sync, lent→async
```

### **3. STRATÉGIE DÉTECTION**  
```
A) Convention  - "Description" + "Description_Vector"
B) Métadonnées - Configuration explicite par colonne
C) Auto-scan   - Détection Text+Vector dans même table
```

---

## 🚀 **DÉMARRAGE PROPOSÉ**

### **ACTION IMMÉDIATE** ⚡
1. **Confirmer service embeddings préféré**
2. **Obtenir credentials API (Albert)**  
3. **Créer EmbeddingService.ts basique**
4. **Tester première génération d'embedding**

### **TEST VALIDATION**
```python
# Test simple dans container existant
python -c "
import requests
embedding_service = EmbeddingService('albert', api_key, endpoint)
result = embedding_service.generate('architecture gothique paris')
print(f'Embedding généré: {len(result)} dimensions')
"
```

### **RÉSULTAT ATTENDU**
- Documents sémantiques **automatiquement peuplés**
- Recherche **"architecture paris"** → résultats pertinents  
- **Showcase complet** avec toutes fonctionnalités actives

---

## 💡 **DÉCISION REQUISE**

**Pouvons-nous démarrer avec** :
1. **Service Albert API** (besoin credentials) 
2. **Mode asynchrone** pour auto-embedding
3. **Convention nommage** pour détection colonnes
4. **Tests sur showcase existant**

**Un "go" lance l'implémentation immédiate !** 🎯
