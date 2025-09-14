# 🚀 Guide de Test des Extensions Spatiales dans Grist

## Accès à Grist
**URL:** http://localhost:8485

## 🧪 Tests des Fonctionnalités Spatiales

### 1. Créer un nouveau document
1. Accédez à http://localhost:8485
2. Cliquez sur "Create Empty Document" ou "Créer un document vide"
3. Donnez un nom au document (ex: "Test Spatial")

### 2. Test des fonctions géographiques

#### Calcul de distance
1. Ajoutez une nouvelle colonne (clic droit → "Add Column")
2. Nommez-la "Distance_Test"
3. Cliquez sur l'icône de formule (=)
4. Entrez cette formule :
```
=GEO_DISTANCE("POINT(2.3522 48.8566)", "POINT(2.3488 48.8534)")
```
**Résultat attendu:** ~434 mètres (distance Tour Eiffel ↔ Notre-Dame)

#### Test avec données réelles
1. Créez 3 colonnes :
   - **Lieu** (Text) : Nom du lieu
   - **Geometrie** (Text) : Coordonnées WKT
   - **Distance_Tour_Eiffel** (Formula)

2. Dans la colonne **Lieu**, entrez :
   - Tour Eiffel
   - Notre-Dame
   - Arc de Triomphe
   - Louvre

3. Dans la colonne **Geometrie**, entrez :
   - `POINT(2.2945 48.8584)`
   - `POINT(2.3490 48.8530)`
   - `POINT(2.2950 48.8738)`
   - `POINT(2.3364 48.8606)`

4. Dans la colonne **Distance_Tour_Eiffel**, formule :
```
=GEO_DISTANCE("POINT(2.2945 48.8584)", $Geometrie)
```

### 3. Test des fonctions vectorielles

#### Génération d'embeddings
1. Créez 2 colonnes :
   - **Description** (Text) : Description du lieu
   - **Embedding** (Formula)

2. Dans **Description**, entrez :
   - "Monument emblématique de Paris, tour de fer de 324m"
   - "Cathédrale gothique historique sur l'île de la Cité"
   - "Arc commémoratif sur les Champs-Élysées"
   - "Plus grand musée d'art du monde"

3. Dans **Embedding**, formule :
```
=GENERATE_EMBEDDING($Description)
```
**Note:** Cette fonction est asynchrone et peut prendre quelques secondes

#### Calcul de similarité
1. Créez une colonne **Similarite_Tour**
2. Formule pour comparer avec l'embedding de la Tour Eiffel :
```
=VECTOR_SIMILARITY($Embedding, GENERATE_EMBEDDING("Monument parisien célèbre"))
```

### 4. Fonctions avancées

#### Calcul d'aire
```
=GEO_AREA("POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))")
```
**Résultat:** Aire du polygone

#### Test de containment
```
=GEO_CONTAINS("POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))", "POINT(5 5)")
```
**Résultat:** true (le point est dans le polygone)

#### Recherche vectorielle
Pour rechercher les éléments similaires :
```
=SEARCH_SIMILAR($Embedding, LIST($Embedding.all), 3)
```

### 5. Cas d'usage pratiques

#### A. Base de données de lieux touristiques
1. **Colonnes à créer :**
   - Nom (Text)
   - Type (Choice: Monument, Musée, Parc, Restaurant)
   - Coordonnees (Text - format WKT)
   - Description (Text)
   - Embedding (Formula: `=GENERATE_EMBEDDING($Description)`)
   - Distance_Centre (Formula: `=GEO_DISTANCE($Coordonnees, "POINT(2.3522 48.8566)")`)

#### B. Analyse de similarité sémantique
1. **Colonnes :**
   - Texte (Text)
   - Vecteur (Formula: `=GENERATE_EMBEDDING($Texte)`)
   - Score_Reference (Formula: `=VECTOR_SIMILARITY($Vecteur, $Vecteur[0])`)

#### C. Clustering spatial
1. **Colonnes :**
   - Point (Text - WKT)
   - Zone (Formula basée sur la distance)
   - Cluster (Formula utilisant GEO_CONTAINS)

## 🔍 Vérification du bon fonctionnement

### Indicateurs de succès :
✅ Les formules GEO_DISTANCE retournent des valeurs numériques  
✅ GENERATE_EMBEDDING retourne un JSON avec 1024 dimensions  
✅ VECTOR_SIMILARITY retourne une valeur entre -1 et 1  
✅ GEO_CONTAINS retourne true/false  
✅ Les calculs sont cohérents (distances réalistes)

### En cas de problème :
1. **"Formula error"** : Vérifiez la syntaxe WKT (POINT(lon lat))
2. **Valeur vide** : Les fonctions async peuvent prendre du temps
3. **"undefined"** : Rechargez la page et réessayez
4. **Erreur réseau** : Albert API peut être temporairement indisponible (mode simulation activé)

## 📊 Export et utilisation

Les données avec calculs spatiaux peuvent être :
- Exportées en CSV/Excel
- Utilisées dans des graphiques
- Partagées via l'interface Grist
- Intégrées via l'API REST de Grist

## 🎯 Commandes utiles

### Vérifier les logs du container :
```bash
docker logs grist-spatial-test
```

### Recharger les extensions :
```bash
docker exec grist-spatial-test node /grist/spatial-loader.js
```

### Redémarrer Grist :
```bash
docker restart grist-spatial-test
```

## 💡 Tips

1. **Performance** : GENERATE_EMBEDDING est coûteux, utilisez-le avec parcimonie
2. **Cache** : Les embeddings sont recalculés à chaque modification
3. **Batch** : Groupez les calculs similaires dans la même colonne
4. **Précision** : GEO_DISTANCE utilise la formule haversine (précision ~0.5%)

---

**Support:** Les extensions spatiales sont en mode simulation si l'API Albert n'est pas accessible. Les calculs géographiques fonctionnent toujours normalement.