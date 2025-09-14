#!/usr/bin/env python3
"""
Création et test d'un document Grist dédié aux extensions spatiales et vectorielles
Conservation des IDs org/doc pour tests répétés
"""

import requests
import json
import time
import re
from urllib.parse import urljoin

class GristTestDocumentManager:
    """Gestionnaire de document de test pour les extensions"""
    
    def __init__(self, base_url="http://127.0.0.1:8888", api_key="f4631937690617681be6860542a5cbdb9794c0ed"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'GristExtensionTester/1.0'
        })
        
        # Variables à conserver
        self.org_id = None
        self.workspace_id = None
        self.doc_id = None
        self.table_id = None
        
    def discover_organization(self):
        """Découvre l'organisation courante"""
        print("🏢 Découverte de l'organisation...")
        
        # Méthode 1: Via page d'accueil
        try:
            response = self.session.get(self.base_url)
            if response.ok:
                # Chercher les patterns d'organisation dans le HTML
                org_patterns = [
                    r'/o/([^/\s"\']+)',
                    r'org["\']:\s*["\']([^"\']+)',
                    r'orgId["\']:\s*["\']([^"\']+)'
                ]
                
                for pattern in org_patterns:
                    matches = re.findall(pattern, response.text)
                    if matches:
                        org_id = matches[0]
                        if org_id and org_id != 'docs':  # Exclure 'docs' qui n'est pas un org_id
                            print(f"   ✅ Organisation trouvée: {org_id}")
                            self.org_id = org_id
                            return org_id
                
                print("   ⚠️ Pas d'organisation spécifique trouvée - utilisation par défaut")
                self.org_id = "docs"  # Organisation par défaut
                return "docs"
        except Exception as e:
            print(f"   ❌ Erreur découverte org: {e}")
            self.org_id = "docs"
            return "docs"
    
    def create_test_document(self):
        """Crée le document de test dédié"""
        print("📄 Création du document de test...")
        
        if not self.org_id:
            self.discover_organization()
        
        doc_name = f"Test Extensions Spatiales Vectorielles - {int(time.time())}"
        
        # Essayer plusieurs endpoints de création
        creation_endpoints = [
            f'/api/orgs/{self.org_id}/docs',
            '/api/docs',
            f'/api/orgs/docs/docs',
        ]
        
        for endpoint in creation_endpoints:
            print(f"   Tentative: {endpoint}")
            
            try:
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json={'name': doc_name}
                )
                
                print(f"      Status: {response.status_code}")
                
                if response.ok:
                    result = response.text
                    try:
                        data = response.json()
                        doc_id = data.get('id') if isinstance(data, dict) else data
                    except:
                        doc_id = result.strip()
                    
                    if doc_id:
                        print(f"   ✅ Document créé: {doc_id}")
                        self.doc_id = doc_id
                        self.save_test_ids()
                        return doc_id
                else:
                    error_text = response.text[:100] + "..." if len(response.text) > 100 else response.text
                    print(f"      Erreur: {error_text}")
                    
            except Exception as e:
                print(f"      Exception: {e}")
        
        print("   ❌ Échec création - utilisation document existant")
        return None
    
    def save_test_ids(self):
        """Sauvegarde les IDs pour réutilisation"""
        test_config = {
            'org_id': self.org_id,
            'workspace_id': self.workspace_id,
            'doc_id': self.doc_id,
            'table_id': self.table_id,
            'base_url': self.base_url,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'test_purpose': 'Extensions Spatiales et Vectorielles Grist'
        }
        
        try:
            with open('grist_test_config.json', 'w') as f:
                json.dump(test_config, f, indent=2)
            print(f"   💾 Configuration sauvegardée dans grist_test_config.json")
        except Exception as e:
            print(f"   ⚠️ Erreur sauvegarde: {e}")
    
    def load_test_ids(self):
        """Charge les IDs sauvegardés"""
        try:
            with open('grist_test_config.json', 'r') as f:
                config = json.load(f)
            
            self.org_id = config.get('org_id')
            self.workspace_id = config.get('workspace_id')
            self.doc_id = config.get('doc_id')
            self.table_id = config.get('table_id')
            
            print(f"   📋 Configuration chargée:")
            print(f"      Org ID: {self.org_id}")
            print(f"      Doc ID: {self.doc_id}")
            print(f"      Créé le: {config.get('created_at')}")
            
            return True
        except FileNotFoundError:
            print("   ℹ️ Aucune configuration existante")
            return False
        except Exception as e:
            print(f"   ⚠️ Erreur chargement config: {e}")
            return False
    
    def verify_document_access(self, doc_id=None):
        """Vérifie l'accès au document"""
        test_doc_id = doc_id or self.doc_id
        if not test_doc_id:
            return False
        
        print(f"🔍 Vérification accès document: {test_doc_id}")
        
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{test_doc_id}")
            
            if response.ok:
                print(f"   ✅ Document accessible via API")
                
                # Vérifier aussi l'accès web
                web_url = f"{self.base_url}/o/{self.org_id or 'docs'}/{test_doc_id}"
                web_response = self.session.get(web_url)
                
                if web_response.ok:
                    print(f"   ✅ Document accessible via web: {web_url}")
                    return True
                else:
                    print(f"   ⚠️ Document API OK mais web inaccessible")
                    return True  # API suffit
            else:
                print(f"   ❌ Document inaccessible: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Erreur vérification: {e}")
            return False
    
    def setup_test_structure(self):
        """Configure la structure de test complète"""
        if not self.doc_id:
            print("❌ Aucun document disponible")
            return False
        
        print(f"🏗️ Configuration de la structure de test...")
        
        # 1. Identifier la table principale
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/tables")
            
            if response.ok:
                tables = response.json().get('tables', [])
                if tables:
                    self.table_id = tables[0]['id']
                    print(f"   ✅ Table identifiée: {self.table_id}")
                else:
                    print(f"   ⚠️ Aucune table trouvée")
                    return False
            else:
                print(f"   ❌ Erreur listage tables: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Erreur structure: {e}")
            return False
        
        return True
    
    def generate_test_instructions(self):
        """Génère les instructions de test manuel"""
        if not all([self.org_id, self.doc_id, self.table_id]):
            print("⚠️ Configuration incomplète - instructions génériques")
            doc_url = f"{self.base_url}"
        else:
            doc_url = f"{self.base_url}/o/{self.org_id}/{self.doc_id}"
        
        instructions = f"""
# 📋 INSTRUCTIONS DE TEST - EXTENSIONS SPATIALES & VECTORIELLES

## 🎯 Document de Test Configuré
- **URL du document**: {doc_url}
- **Organisation**: {self.org_id or 'Non définie'}
- **Document ID**: {self.doc_id or 'Non défini'}
- **Table principale**: {self.table_id or 'Table1'}

## 📝 ÉTAPES DE TEST MANUEL

### 1️⃣ ACCÈS AU DOCUMENT
1. Ouvrez: {doc_url}
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
"""
        
        return instructions

def main():
    """Fonction principale de création et configuration"""
    print("🚀 CRÉATION DOCUMENT DE TEST DÉDIÉ")
    print("=" * 40)
    print(f"⏰ Début: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    manager = GristTestDocumentManager()
    
    try:
        # 1. Charger configuration existante
        print("\n📋 ÉTAPE 1: Vérification configuration existante")
        config_loaded = manager.load_test_ids()
        
        if config_loaded and manager.doc_id:
            # Vérifier si le document existe encore
            if manager.verify_document_access():
                print("   ✅ Document existant réutilisé")
                use_existing = True
            else:
                print("   ⚠️ Document existant inaccessible - création nouveau")
                use_existing = False
        else:
            use_existing = False
        
        # 2. Découvrir/créer document si nécessaire
        if not use_existing:
            print("\n🏢 ÉTAPE 2: Découverte organisation")
            manager.discover_organization()
            
            print("\n📄 ÉTAPE 3: Création document")
            doc_id = manager.create_test_document()
            
            if doc_id:
                manager.doc_id = doc_id
            else:
                print("   ⚠️ Utilisation document existant")
                manager.doc_id = "new~rhRFrQmKGvugn5cR45RTXe~5"  # Fallback
        
        # 3. Configuration structure
        print("\n🏗️ ÉTAPE 4: Configuration structure de test")
        structure_ok = manager.setup_test_structure()
        
        # 4. Sauvegarder configuration
        manager.save_test_ids()
        
        # 5. Générer instructions
        print("\n📝 ÉTAPE 5: Génération instructions de test")
        instructions = manager.generate_test_instructions()
        
        # Sauvegarder instructions
        with open('INSTRUCTIONS_TEST_MANUEL.md', 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        # Résumé final
        print(f"\n🎯 RÉSUMÉ FINAL")
        print("=" * 20)
        print(f"✅ Organisation: {manager.org_id}")
        print(f"✅ Document: {manager.doc_id}")  
        print(f"✅ Table: {manager.table_id}")
        print(f"✅ URL document: {manager.base_url}/o/{manager.org_id or 'docs'}/{manager.doc_id}")
        print(f"💾 Configuration: grist_test_config.json")
        print(f"📋 Instructions: INSTRUCTIONS_TEST_MANUEL.md")
        
        if all([manager.org_id, manager.doc_id, manager.table_id]):
            print(f"\n🎉 DOCUMENT DE TEST PARFAITEMENT CONFIGURÉ !")
            print("🔧 Suivez les instructions dans INSTRUCTIONS_TEST_MANUEL.md")
            print("🌟 Testez les extensions directement dans l'interface Grist")
        else:
            print(f"\n⚠️ Configuration partielle - Tests manuels possibles")
        
        print(f"\n⏰ Fin: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
        
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
