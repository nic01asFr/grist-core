# 🧪 **GUIDE DE TEST COMPLET MANUEL - EXTENSIONS GRIST**

**Document de test configuré** : http://127.0.0.1:8888/o/docs/new~cVpnNgHsFMAujRB2bSQGPP~5

---

## 🎯 **OBJECTIF**
Valider que les extensions spatiales et vectorielles fonctionnent parfaitement dans Grist :
- ✅ Types **Geometry** et **Vector** disponibles
- ✅ Formules **ST_*** et **VECTOR_*** opérationnelles  
- ✅ Calculs automatiques corrects
- ✅ Pas d'erreur système

---

## 🚀 **ÉTAPE 1 : ACCÈS AU DOCUMENT**

1. **Ouvrez le navigateur** et allez sur : 
   ```
   http://127.0.0.1:8888/o/docs/new~cVpnNgHsFMAujRB2bSQGPP~5
   ```

2. **Vérifiez** que :
   - ✅ Le document s'ouvre sans erreur
   - ✅ Vous voyez une table vide (Table1)
   - ✅ L'interface Grist fonctionne normalement

---

## 📋 **ÉTAPE 2 : CRÉATION DES COLONNES DE TEST**

### **A. Colonnes de base**

**Ajoutez ces colonnes dans l'ordre :**

1. **Colonne "Lieu"**
   - Cliquez sur **"+"** pour ajouter une colonne
   - **ID** : `lieu`
   - **Label** : `Lieu`  
   - **Type** : `Text`

2. **Colonne "Description"**
   - **ID** : `description`
   - **Label** : `Description`
   - **Type** : `Text`

### **B. Colonnes avec nouveaux types - CŒUR DU TEST**

3. **Colonne "Position GPS"** 🌟
   - **ID** : `position`
   - **Label** : `Position GPS`
   - **Type** : `Geometry` ← **NOUVEAU TYPE À VÉRIFIER**
   
   **🎯 RÉSULTAT ATTENDU :** 
   - ✅ Le type `Geometry` apparaît dans la liste des types
   - ✅ La colonne se crée sans erreur

4. **Colonne "Caractéristiques"** 🌟  
   - **ID** : `caracteristiques`
   - **Label** : `Caractéristiques`
   - **Type** : `Vector` ← **NOUVEAU TYPE À VÉRIFIER**
   
   **🎯 RÉSULTAT ATTENDU :**
   - ✅ Le type `Vector` apparaît dans la liste des types
   - ✅ La colonne se crée sans erreur

### **C. Colonnes formules spatiales - TEST DES NOUVELLES FONCTIONS**

5. **Distance Notre-Dame**
   - **ID** : `distance_notre_dame`
   - **Label** : `Distance Notre-Dame (km)`
   - **Type** : `Formula`
   - **Formule** : 
   ```
   =ST_DISTANCE($position, "POINT(2.3522 48.8566)", "km")
   ```

6. **Dans Paris centre**
   - **ID** : `dans_paris_centre`
   - **Label** : `Dans Paris centre`  
   - **Type** : `Formula`
   - **Formule** :
   ```
   =ST_CONTAINS("POLYGON((2.25 48.80, 2.45 48.80, 2.45 48.90, 2.25 48.90, 2.25 48.80))", $position)
   ```

### **D. Colonnes formules vectorielles - TEST DES NOUVELLES FONCTIONS**

7. **Similarité monument**
   - **ID** : `similarite_monument`
   - **Label** : `Similarité monument`
   - **Type** : `Formula`
   - **Formule** :
   ```
   =VECTOR_SIMILARITY($caracteristiques, [0.9, 0.1, 0.8, 0.2, 0.95], "cosine")
   ```

8. **Similarité culture**
   - **ID** : `similarite_culture`
   - **Label** : `Similarité culture`
   - **Type** : `Formula`  
   - **Formule** :
   ```
   =VECTOR_SIMILARITY($caracteristiques, [0.7, 0.3, 0.6, 0.4, 0.75], "cosine")
   ```

### **E. Colonnes formules mixtes - TEST COMBINAISONS**

9. **Score touristique**
   - **ID** : `score_touristique`
   - **Label** : `Score touristique`
   - **Type** : `Formula`
   - **Formule** :
   ```
   =($similarite_monument * 0.6) + ((5 - $distance_notre_dame) / 5 * 0.4)
   ```

10. **Recommandation**
    - **ID** : `recommandation`  
    - **Label** : `Recommandation`
    - **Type** : `Formula`
    - **Formule** :
    ```
    =IF($score_touristique > 0.7, "Recommandé", IF($score_touristique > 0.4, "Intéressant", "Pas prioritaire"))
    ```

---

## 📊 **ÉTAPE 3 : SAISIE DES DONNÉES DE TEST**

**Ajoutez ces lignes une par une :**

### **Ligne 1 : Notre-Dame de Paris**
- **lieu** : `Notre-Dame de Paris`
- **description** : `Cathédrale gothique emblématique`
- **position** : `POINT(2.3522 48.8566)`
- **caracteristiques** : `[0.95, 0.05, 0.90, 0.10, 0.98]`

### **Ligne 2 : Tour Eiffel**  
- **lieu** : `Tour Eiffel`
- **description** : `Tour de fer emblématique`
- **position** : `POINT(2.2945 48.8584)`
- **caracteristiques** : `[0.98, 0.02, 0.95, 0.05, 1.00]`

### **Ligne 3 : Musée du Louvre**
- **lieu** : `Musée du Louvre` 
- **description** : `Plus grand musée d'art au monde`
- **position** : `POINT(2.3380 48.8606)`
- **caracteristiques** : `[0.85, 0.15, 0.80, 0.20, 0.90]`

### **Ligne 4 : Arc de Triomphe**
- **lieu** : `Arc de Triomphe`
- **description** : `Monument aux morts, Champs-Élysées`  
- **position** : `POINT(2.2950 48.8738)`
- **caracteristiques** : `[0.88, 0.12, 0.85, 0.15, 0.92]`

### **Ligne 5 : Sacré-Cœur**
- **lieu** : `Sacré-Cœur`
- **description** : `Basilique sur la butte Montmartre`
- **position** : `POINT(2.3431 48.8867)`  
- **caracteristiques** : `[0.82, 0.18, 0.78, 0.22, 0.85]`

---

## 🔍 **ÉTAPE 4 : VALIDATION DES RÉSULTATS**

### **A. Vérification des types**

**Après avoir créé les colonnes, vérifiez :**

- ✅ **Type Geometry** : La colonne `position` accepte les données WKT comme `POINT(2.3522 48.8566)`
- ✅ **Type Vector** : La colonne `caracteristiques` accepte les arrays comme `[0.95, 0.05, 0.90, 0.10, 0.98]`
- ✅ **Pas d'erreur** Python dans la console (F12)

### **B. Vérification des formules spatiales**

**Attendez ~10 secondes que les formules se calculent, puis vérifiez :**

- ✅ **distance_notre_dame** : Doit afficher des valeurs comme `0.0`, `1.2`, `0.3` km (distances réalistes)
- ✅ **dans_paris_centre** : Doit afficher `True` pour la plupart des monuments (dans le polygone)

### **C. Vérification des formules vectorielles**

- ✅ **similarite_monument** : Doit afficher des valeurs entre 0 et 1 (ex: `0.823`, `0.945`)
- ✅ **similarite_culture** : Doit afficher des valeurs différentes de la précédente

### **D. Vérification des formules mixtes**

- ✅ **score_touristique** : Doit calculer un score composite (ex: `0.78`, `0.91`)  
- ✅ **recommandation** : Doit afficher "Recommandé", "Intéressant", ou "Pas prioritaire"

---

## 🧮 **ÉTAPE 5 : TESTS AVANCÉS**

### **Testez directement dans une cellule vide :**

1. **Test formule spatiale simple** :
   ```
   =ST_DISTANCE("POINT(0 0)", "POINT(0 1)", "km")
   ```
   **Résultat attendu** : ~111 km

2. **Test aire** :
   ```
   =ST_AREA("POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))")
   ```
   **Résultat attendu** : Valeur positive

3. **Test centroïde** :
   ```  
   =ST_CENTROID("POLYGON((0 0, 0 4, 4 4, 4 0, 0 0))")
   ```
   **Résultat attendu** : "POINT(2 2)"

4. **Test similarité vectorielle** :
   ```
   =VECTOR_SIMILARITY([1,0,0], [0,1,0], "cosine")
   ```
   **Résultat attendu** : 0

5. **Test vecteurs identiques** :
   ```
   =VECTOR_SIMILARITY([1,2,3], [1,2,3], "cosine")  
   ```
   **Résultat attendu** : 1

---

## 📊 **CRITÈRES DE VALIDATION FINALE**

### **✅ SUCCÈS COMPLET** (Objectif : 8/8)
- [ ] Types Geometry et Vector disponibles dans l'interface
- [ ] Données géométriques WKT acceptées sans erreur  
- [ ] Données vectorielles array acceptées sans erreur
- [ ] Formules ST_DISTANCE calculent des distances cohérentes
- [ ] Formules VECTOR_SIMILARITY retournent 0-1
- [ ] Formules ST_CONTAINS retournent True/False logiques  
- [ ] Formules mixtes se calculent automatiquement
- [ ] Aucune erreur Python dans console (F12)

### **⚠️ SUCCÈS PARTIEL** (6-7/8)
- Au moins un nouveau type fonctionne
- Au moins une famille de formules fonctionne
- Données de base acceptées

### **❌ ÉCHEC** (<6/8)  
- Types Geometry/Vector non disponibles
- Formules ST_*/VECTOR_* non reconnues
- Erreurs Python bloquantes

---

## 🎯 **RÉSULTATS ATTENDUS PAR LIGNE**

| Lieu | Distance ND | Dans centre | Sim. monument | Sim. culture | Score | Recommandation |
|------|-------------|-------------|---------------|--------------|-------|----------------|
| Notre-Dame | ~0.0 km | True | ~0.99 | ~0.85 | ~0.99 | Recommandé |
| Tour Eiffel | ~1.2 km | True | ~0.95 | ~0.78 | ~0.87 | Recommandé |  
| Louvre | ~0.3 km | True | ~0.88 | ~0.82 | ~0.85 | Recommandé |
| Arc Triomphe | ~1.8 km | True | ~0.92 | ~0.80 | ~0.81 | Recommandé |
| Sacré-Cœur | ~2.1 km | True | ~0.85 | ~0.78 | ~0.71 | Recommandé |

**Si ces valeurs s'affichent correctement = 🎉 EXTENSIONS PARFAITEMENT FONCTIONNELLES !**

---

## 🔧 **EN CAS DE PROBLÈME**

### **Si types Geometry/Vector non disponibles :**
- Vérifiez que le container `grist-test-formulas` tourne bien
- Redémarrez si nécessaire : `docker restart grist-test-formulas`

### **Si formules non reconnues :**
- Vérifiez la syntaxe exacte (copier-coller depuis ce guide)
- Regardez la console (F12) pour les erreurs Python

### **Si calculs incorrects :**
- Attendez ~30 secondes pour que tous les calculs se terminent
- Rafraîchissez la page (F5)

---

## 📝 **RAPPORT DE TEST**

**Date** : ___________  
**Testeur** : ___________

### **Résultats :**
- [ ] ✅ Types Geometry/Vector disponibles : _____
- [ ] ✅ Données spatiales acceptées : _____  
- [ ] ✅ Données vectorielles acceptées : _____
- [ ] ✅ Formules ST_* fonctionnelles : _____
- [ ] ✅ Formules VECTOR_* fonctionnelles : _____
- [ ] ✅ Calculs automatiques corrects : _____
- [ ] ✅ Formules mixtes opérationnelles : _____
- [ ] ✅ Interface stable (pas d'erreur) : _____

### **Score final** : ___/8

### **Commentaires** :
```
_________________________________________________
_________________________________________________
_________________________________________________
```

---

**🎉 Si score ≥ 6/8 : MISSION RÉUSSIE ! Extensions opérationnelles !** 

**📧 Merci de me rapporter vos résultats pour validation finale.**
