
# 📋 INSTRUCTIONS DE TEST - EXTENSIONS SPATIALES & VECTORIELLES

## 🎯 Document de Test Configuré
- **URL du document**: http://127.0.0.1:8888/o/docs/new~cVpnNgHsFMAujRB2bSQGPP~5
- **Organisation**: docs
- **Document ID**: new~cVpnNgHsFMAujRB2bSQGPP~5
- **Table principale**: Table1

## 📝 ÉTAPES DE TEST MANUEL

### 1️⃣ ACCÈS AU DOCUMENT
1. Ouvrez: http://127.0.0.1:8888/o/docs/new~cVpnNgHsFMAujRB2bSQGPP~5
2. Vérifiez que le document s'affiche correctement
3. Identifiez la table principale

### 2️⃣ CRÉATION DES COLONNES DE TEST

**Ajoutez ces colonnes dans l'ordre:**

| Nom Colonne | Type | Label | Formule (si applicable) |
|-------------|------|-------|-------------------------|
| `nom_lieu` | Text | Nom du lieu | - |
| `coordonnees` | **Geometry** | Coordonnées GPS | - |
| `embedding` | **Vector** | Caractéristiques | - |
| `distance_paris` | Formula | Distance Paris (km) | `=ST_DISTANCE($coordonnees, "POINT(2.3488 48.8534)", "km")` |
| `similarite_ref` | Formula | Similarité référence | `=VECTOR_SIMILARITY($embedding, [0.8, 0.3, 0.7, 0.2, 0.9], "cosine")` |
| `score_composite` | Formula | Score composite | `=($similarite_ref * 0.7) + ((100 - $distance_paris) / 100 * 0.3)` |

### 3️⃣ SAISIE DES DONNÉES DE TEST

**Insérez ces lignes:**

```
Ligne 1:
- nom_lieu: "Tour Eiffel"
- coordonnees: "POINT(2.2945 48.8584)"
- embedding: [0.9, 0.1, 0.8, 0.2, 0.95]

Ligne 2:
- nom_lieu: "Arc de Triomphe" 
- coordonnees: "POINT(2.2950 48.8738)"
- embedding: [0.85, 0.15, 0.75, 0.25, 0.9]

Ligne 3:
- nom_lieu: "Opéra Bastille"
- coordonnees: "POINT(2.3697 48.8532)"
- embedding: [0.7, 0.4, 0.6, 0.3, 0.75]
```

### 4️⃣ VALIDATION DES RÉSULTATS

**Vérifiez que :**
- ✅ Les types `Geometry` et `Vector` sont disponibles dans la liste des types
- ✅ Les données géométriques et vectorielles sont acceptées sans erreur
- ✅ La formule `ST_DISTANCE` calcule ~1-3 km pour les monuments parisiens
- ✅ La formule `VECTOR_SIMILARITY` retourne des valeurs entre 0 et 1
- ✅ Le score composite se calcule automatiquement
- ✅ Pas d'erreur Python dans la console du navigateur (F12)

### 5️⃣ TESTS AVANCÉS

**Testez aussi :**
- `ST_AREA("POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))")` → doit retourner ~1
- `ST_CONTAINS("POLYGON((0 0, 0 2, 2 2, 2 0, 0 0))", "POINT(1 1)")` → doit retourner True
- `ST_CENTROID("POLYGON((0 0, 0 4, 4 4, 4 0, 0 0))")` → doit retourner "POINT(2 2)"
- `VECTOR_SIMILARITY([1,0,0], [0,1,0], "cosine")` → doit retourner 0
- `VECTOR_SIMILARITY([1,2,3], [1,2,3], "cosine")` → doit retourner 1

## 🎯 CRITÈRES DE SUCCÈS

### ✅ SUCCÈS COMPLET
- Tous les nouveaux types sont disponibles
- Toutes les formules fonctionnent
- Calculs automatiques corrects
- Pas d'erreur système

### ⚠️ SUCCÈS PARTIEL  
- Au moins un nouveau type fonctionne
- Au moins une formule avancée fonctionne
- Données de base acceptées

### ❌ ÉCHEC
- Types Geometry/Vector non disponibles
- Formules ST_*/VECTOR_* non reconnues
- Erreurs Python bloquantes

---

**🔄 Pour relancer ces tests :** Exécutez `python creation_document_test_final.py`
**💾 Configuration sauvée :** `grist_test_config.json`
