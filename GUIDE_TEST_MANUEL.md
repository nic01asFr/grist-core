# 🧪 Guide de Test Manuel - Extensions Spatial & Vector

## 🎯 Objectif
Valider le bon fonctionnement des types `Geometry` et `Vector` directement dans l'interface Grist.

## 🌐 Accès à l'instance de test
- **URL**: http://127.0.0.1:8888
- **Container**: `grist-complete-final`
- **Status**: ✅ Opérationnel

---

## 📋 TEST 1: Création de colonnes avec types personnalisés

### Étapes :
1. **Ouvrez** http://127.0.0.1:8888
2. **Créez un nouveau document** ou utilisez un existant
3. **Ajoutez une nouvelle colonne** et sélectionnez le type **`Geometry`**
4. **Ajoutez une nouvelle colonne** et sélectionnez le type **`Vector`**

### Résultat attendu :
- ✅ Les types `Geometry` et `Vector` apparaissent dans la liste des types
- ✅ Pas d'erreur lors de la création des colonnes
- ✅ Les colonnes sont créées avec les bons types

---

## 📊 TEST 2: Saisie de données géométriques

### Données de test Geometry :
```
WKT Format:
- POINT(2.3488 48.8534)
- POLYGON((0 0, 4 0, 4 4, 0 4, 0 0))
- LINESTRING(0 0, 1 1, 2 2, 3 3)

GeoJSON Format:
- {"type":"Point","coordinates":[2.3488,48.8534]}
- {"type":"Polygon","coordinates":[[[0,0],[4,0],[4,4],[0,4],[0,0]]]}
```

### Étapes :
1. **Saisissez** chaque format dans une cellule de type `Geometry`
2. **Validez** la saisie (Entrée)
3. **Vérifiez** que la donnée est acceptée et stockée

### Résultat attendu :
- ✅ Les données WKT sont acceptées et stockées
- ✅ Les données GeoJSON sont converties en WKT
- ✅ Pas d'erreur Python dans la console du navigateur

---

## 🔢 TEST 3: Saisie de données vectorielles

### Données de test Vector :
```
Array Format:
- [1.0, 2.0, 3.0, 4.0, 5.0]
- [0.1, -0.2, 0.3, -0.4, 0.5, 0.6, -0.7, 0.8]

JSON String Format:
- "[1.0, 2.0, 3.0, 4.0, 5.0]"
- "[0.15, 0.23, -0.41, 0.67, -0.89]"

CSV String Format:
- "1.0, 2.0, 3.0, 4.0, 5.0"
- "0.15, 0.23, -0.41, 0.67, -0.89"
```

### Étapes :
1. **Saisissez** chaque format dans une cellule de type `Vector`
2. **Validez** la saisie (Entrée)
3. **Vérifiez** que la donnée est acceptée et stockée

### Résultat attendu :
- ✅ Tous les formats de vecteurs sont acceptés
- ✅ Conversion automatique vers format array
- ✅ Pas d'erreur lors de la saisie

---

## ⚠️ TEST 4: Validation des erreurs

### Données invalides à tester :

#### Geometry invalide :
```
- "INVALID_WKT_FORMAT"
- "POINT(not_a_number 48.8534)"
- {"type":"InvalidType","coordinates":[2,48]}
```

#### Vector invalide :
```
- "[1.0, invalid_number, 3.0]"
- "not_a_vector_format"
- [1, "text", 3]
```

### Étapes :
1. **Saisissez** chaque donnée invalide
2. **Tentez de valider** (Entrée)
3. **Observez** le comportement

### Résultat attendu :
- ✅ Messages d'erreur clairs pour données invalides
- ✅ Pas de crash de l'application
- ✅ Possibilité de corriger la saisie

---

## 🧮 TEST 5: Fonctionnalités avancées (si disponibles)

### Test de formules spatiales :
1. **Créez une colonne de formule**
2. **Testez** (si disponibles) :
   ```
   =ST_Distance($Geometry1, $Geometry2)
   =ST_Area($Polygon_Column)
   ```

### Test de formules vectorielles :
1. **Créez une colonne de formule**
2. **Testez** (si disponibles) :
   ```
   =VECTOR_SIMILARITY($Vector1, $Vector2)
   =GENERATE_EMBEDDING("Mon texte")
   ```

### Résultat attendu :
- ⚠️ Ces fonctions peuvent ne pas être disponibles (services non intégrés)
- ✅ Pas de crash même si les fonctions n'existent pas

---

## 📊 Exemple de données complètes

### Table de test suggérée :

| Nom | Localisation (Geometry) | Description | Embedding (Vector) |
|-----|-------------------------|-------------|-------------------|
| Paris | POINT(2.3488 48.8534) | Capitale française | [0.1, -0.2, 0.3, -0.4, 0.5] |
| Lyon | POINT(4.8357 45.7640) | Gastronomie | [0.2, 0.1, -0.3, 0.4, -0.5] |
| Marseille | POINT(5.3698 43.2965) | Port méditerranéen | [-0.1, 0.3, 0.2, -0.6, 0.4] |

---

## 🎯 Critères de succès

### ✅ Succès minimum requis :
- [ ] Types Geometry et Vector visibles dans l'interface
- [ ] Création de colonnes sans erreur
- [ ] Saisie de données WKT/GeoJSON pour Geometry
- [ ] Saisie de données vectorielles dans différents formats
- [ ] Validation des données invalides

### 🌟 Succès optimal :
- [ ] Toutes les fonctionnalités de base opérationnelles
- [ ] Formules spatiales/vectorielles disponibles
- [ ] Performance acceptable sur données de test
- [ ] Interface utilisateur intuitive

---

## 📝 Rapport de test

**Date** : ___________  
**Testeur** : ___________

### Résultats :
- [ ] ✅ TEST 1 - Types de colonnes : _____
- [ ] ✅ TEST 2 - Données Geometry : _____
- [ ] ✅ TEST 3 - Données Vector : _____
- [ ] ✅ TEST 4 - Validation erreurs : _____
- [ ] ⚠️ TEST 5 - Fonctions avancées : _____

### Commentaires :
```
_________________________________________________
_________________________________________________
_________________________________________________
```

### Score final : ___/5

---

## 🚀 Prochaines étapes selon les résultats

### Si tous les tests de base passent (1-4) :
1. **Intégration des services avancés** (APIs, fonctions natives)
2. **Tests de performance** sur plus gros volumes
3. **Documentation utilisateur** complète

### Si certains tests échouent :
1. **Debug des erreurs** spécifiques identifiées
2. **Correction du code** concerné
3. **Re-test** des fonctionnalités corrigées
