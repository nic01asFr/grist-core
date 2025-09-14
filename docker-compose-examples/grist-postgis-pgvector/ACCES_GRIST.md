# 🚀 ACCÈS À GRIST - GUIDE WSL/WINDOWS

## ✅ Grist est opérationnel !

Le container Grist fonctionne correctement avec PostgreSQL + PostGIS.

## 🌐 URLs d'accès

### Option 1: Localhost (recommandé)
```
http://localhost:8484
```

### Option 2: IP WSL directe
```
http://172.24.176.202:8484
```

### Option 3: Via Windows
Depuis Windows (navigateur), utilisez :
```
http://localhost:8484
```
ou
```
http://172.24.176.202:8484
```

## 🔧 Solutions si localhost ne fonctionne pas

### 1. Port forwarding Windows ↔ WSL
```bash
# Dans PowerShell en administrateur Windows :
netsh interface portproxy add v4tov4 listenport=8484 listenaddress=0.0.0.0 connectport=8484 connectaddress=172.24.176.202
```

### 2. Modifier la configuration Docker
```bash
# Redémarrer avec binding explicite
docker-compose -f docker-compose-demo.yml down
docker-compose -f docker-compose-demo.yml up -d
```

### 3. Test direct container
```bash
# Accès direct au container
docker exec -it grist-app-demo curl http://localhost:8484
```

## 🖥️ Interface Web

Une fois connecté à Grist :

1. **Page d'accueil** : Liste des documents
2. **Nouveau document** : Bouton "+" pour créer
3. **Types de colonnes** : Standards Grist disponibles
4. **Base de données** : PostgreSQL avec PostGIS actif

## 🗃️ Configuration base de données

```yaml
Host: postgres-db (ou localhost:5433 depuis l'extérieur)
Database: grist  
User: grist
Password: grist123
Extensions: postgis, postgis_topology
Schema spatial: grist_spatial
```

## 🔍 Vérification

### Test curl (fonctionne ✅)
```bash
curl http://localhost:8484
# Retourne: Found. Redirecting to http://localhost:8484/o/docs/

curl http://localhost:8484/o/docs/ | head -10
# Retourne: HTML de la page Grist
```

### État containers
```bash
docker-compose -f docker-compose-demo.yml ps
# Les deux containers sont UP et healthy
```

### Logs
```bash
docker-compose -f docker-compose-demo.yml logs grist-app | tail -10
# Montre les accès HTTP réussis
```

## 📱 Navigation navigateur

1. Ouvrez votre navigateur
2. Allez sur `http://localhost:8484`
3. Vous devriez voir la redirection vers `/o/docs/`
4. Interface Grist s'affiche avec "Welcome to Grist"

## 🛠️ Debugging si problème persiste

```bash
# 1. Vérifier les containers
docker-compose -f docker-compose-demo.yml ps

# 2. Logs détaillés
docker-compose -f docker-compose-demo.yml logs

# 3. Test réseau
curl -v http://localhost:8484

# 4. IP alternative
curl -v http://$(hostname -I | awk '{print $1}'):8484
```

## 🎯 URLs de test validées

- ✅ `http://localhost:8484` → Redirige vers `/o/docs/`
- ✅ `http://172.24.176.202:8484` → Fonctionne
- ✅ Container accessible et répond correctement
- ✅ PostgreSQL opérationnel sur port 5433

**Le système est complètement fonctionnel !**