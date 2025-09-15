#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST FINAL - INTÉGRATION PYTHON NATIVE COMPLÈTE
Crée un document, obtient une API key et teste tous les endpoints avec les fonctions Python natives
"""

import requests
import json
import time
import sys

class TestPythonNativeFinal:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8888"
        self.session = requests.Session()
        self.org_id = None
        self.workspace_id = None  
        self.doc_id = None
        self.api_key = None
        
    def create_document_and_get_api_key(self):
        """Créer un nouveau document et obtenir une API key"""
        print("\n🔧 CRÉATION DOCUMENT & API KEY")
        print("=" * 50)
        
        try:
            # 1. Accéder à la page d'accueil pour initialiser une session
            print("📡 Initialisation session...")
            response = self.session.get(f"{self.base_url}/")
            if response.status_code != 200:
                print(f"❌ Erreur initialisation: {response.status_code}")
                return False
                
            # 2. Obtenir les organisations
            print("📋 Récupération organisations...")  
            response = self.session.get(f"{self.base_url}/api/orgs")
            if response.status_code != 200:
                print(f"❌ Erreur récupération orgs: {response.status_code}")
                return False
                
            orgs = response.json()
            if not orgs:
                print("❌ Aucune organisation trouvée")
                return False
                
            self.org_id = orgs[0]['id']
            print(f"✅ Organisation trouvée: {self.org_id}")
            
            # 3. Obtenir les workspaces
            print("📂 Récupération workspaces...")
            response = self.session.get(f"{self.base_url}/api/orgs/{self.org_id}/workspaces")
            if response.status_code != 200:
                print(f"❌ Erreur récupération workspaces: {response.status_code}")
                return False
                
            workspaces = response.json()
            if not workspaces:
                print("❌ Aucun workspace trouvé") 
                return False
                
            self.workspace_id = workspaces[0]['id']
            print(f"✅ Workspace trouvé: {self.workspace_id}")
            
            # 4. Créer un nouveau document
            print("📄 Création nouveau document...")
            doc_data = {"name": "Test Python Native Final"}
            response = self.session.post(f"{self.base_url}/api/workspaces/{self.workspace_id}/docs", 
                                       json=doc_data)
            if response.status_code not in [200, 201]:
                print(f"❌ Erreur création document: {response.status_code} - {response.text}")
                return False
                
            doc_response = response.json()
            self.doc_id = doc_response.get('id') or doc_response
            print(f"✅ Document créé: {self.doc_id}")
            
            # 5. Obtenir une API key via l'interface web
            print("🔑 Récupération API key...")
            response = self.session.get(f"{self.base_url}/api/profile/user")
            if response.status_code == 200:
                profile = response.json()
                if 'apiKey' in profile:
                    self.api_key = profile['apiKey']
                    print(f"✅ API key obtenue: {self.api_key[:20]}...")
                else:
                    # Générer une API key
                    response = self.session.patch(f"{self.base_url}/api/profile/user", 
                                                json={"apiKey": "generate"})
                    if response.status_code == 200:
                        profile = response.json()
                        self.api_key = profile.get('apiKey')
                        print(f"✅ API key générée: {self.api_key[:20]}...")
                    else:
                        print(f"❌ Erreur génération API key: {response.status_code}")
                        return False
            
            # Configurer les headers avec l'API key
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur création document: {e}")
            return False
    
    def test_endpoints(self):
        """Tester tous les endpoints avec les fonctions Python natives"""
        print("\n🧪 TEST ENDPOINTS PYTHON NATIFS")  
        print("=" * 50)
        
        endpoints_results = {}
        
        # Test 1: Capabilities
        print("📋 Test capabilities...")
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/spatial/capabilities")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Capabilities: {len(data['data']['features']['spatial_functions'])} fonctions spatiales")
                endpoints_results['capabilities'] = 'SUCCESS'
            else:
                print(f"❌ Capabilities failed: {response.status_code}")
                endpoints_results['capabilities'] = 'FAILED'
        except Exception as e:
            print(f"❌ Capabilities error: {e}")
            endpoints_results['capabilities'] = 'ERROR'
        
        # Test 2: Health check  
        print("🏥 Test health...")
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/spatial/health")
            if response.status_code == 200:
                data = response.json()
                status = data['data']['status']
                st_distance_status = data['data']['tests']['st_distance']['status']
                vector_status = data['data']['tests']['vector_similarity']['status']
                print(f"✅ Health: {status}, ST_DISTANCE: {st_distance_status}, VECTOR: {vector_status}")
                endpoints_results['health'] = 'SUCCESS'
            else:
                print(f"❌ Health failed: {response.status_code}")
                endpoints_results['health'] = 'FAILED'
        except Exception as e:
            print(f"❌ Health error: {e}")
            endpoints_results['health'] = 'ERROR'
        
        # Test 3: Distance calculation
        print("📍 Test distance...")
        try:
            payload = {
                "point1": "POINT(2.2945 48.8584)",  # Tour Eiffel
                "point2": "POINT(2.3522 48.8566)",  # Notre-Dame
                "unit": "km"
            }
            response = self.session.post(f"{self.base_url}/api/docs/{self.doc_id}/spatial/distance", 
                                       json=payload)
            if response.status_code == 200:
                data = response.json()
                distance = data['data']['distance']
                print(f"✅ Distance: {distance:.2f} km (Tour Eiffel ↔ Notre-Dame)")
                endpoints_results['distance'] = 'SUCCESS'
            else:
                print(f"❌ Distance failed: {response.status_code}")
                endpoints_results['distance'] = 'FAILED'
        except Exception as e:
            print(f"❌ Distance error: {e}")
            endpoints_results['distance'] = 'ERROR'
        
        # Test 4: Vector similarity
        print("🔢 Test vector similarity...")
        try:
            payload = {
                "vector1": [0.8, 0.2, 0.7, 0.9, 0.1],
                "vector2": [0.7, 0.3, 0.6, 0.8, 0.2], 
                "method": "cosine"
            }
            response = self.session.post(f"{self.base_url}/api/docs/{self.doc_id}/vector/similarity",
                                       json=payload)
            if response.status_code == 200:
                data = response.json()
                similarity = data['data']['similarity']
                print(f"✅ Similarity: {similarity:.3f}")
                endpoints_results['similarity'] = 'SUCCESS'
            else:
                print(f"❌ Similarity failed: {response.status_code}")
                endpoints_results['similarity'] = 'FAILED'
        except Exception as e:
            print(f"❌ Similarity error: {e}")
            endpoints_results['similarity'] = 'ERROR'
            
        return endpoints_results
    
    def check_python_native_logs(self):
        """Vérifier les logs pour confirmer l'utilisation du Python natif"""
        print("\n🔍 VÉRIFICATION LOGS PYTHON NATIF")
        print("=" * 50)
        
        try:
            import subprocess
            
            # Récupérer les logs récents du container
            result = subprocess.run([
                'docker', 'logs', 'grist-python-native-final', '--tail', '50'
            ], capture_output=True, text=True, shell=True)
            
            logs = result.stdout + result.stderr
            
            # Chercher les indicateurs d'utilisation Python native
            python_indicators = [
                "✅ Fonctions spatiales/vectorielles enregistrées",
                "✅ Utilisation du sandbox Python natif", 
                "✅ Accès réussi au document",
                "Sandbox stderr: [INFO] [__main__] Ready"
            ]
            
            found_indicators = []
            for indicator in python_indicators:
                if indicator in logs:
                    found_indicators.append(indicator)
                    print(f"✅ Trouvé: {indicator}")
            
            if found_indicators:
                print(f"\n🎉 {len(found_indicators)}/{len(python_indicators)} indicateurs Python natif trouvés!")
                return True
            else:
                print("\n⚠️  Aucun indicateur Python natif trouvé dans les logs récents")
                return False
                
        except Exception as e:
            print(f"❌ Erreur vérification logs: {e}")
            return False
    
    def run_complete_test(self):
        """Exécuter le test complet"""
        print("🚀 TEST INTÉGRATION PYTHON NATIVE COMPLÈTE")
        print("=" * 60)
        
        # Étape 1: Créer document et API key
        if not self.create_document_and_get_api_key():
            print("\n❌ ÉCHEC: Impossible de créer le document ou obtenir l'API key")
            return False
        
        # Attendre que le serveur soit prêt
        print("\n⏳ Attente stabilisation serveur (10 secondes)...")
        time.sleep(10)
        
        # Étape 2: Tester les endpoints
        results = self.test_endpoints()
        
        # Étape 3: Vérifier les logs
        logs_ok = self.check_python_native_logs()
        
        # Rapport final
        print("\n" + "=" * 60)
        print("📊 RAPPORT FINAL - INTÉGRATION PYTHON NATIVE")
        print("=" * 60)
        
        success_count = sum(1 for r in results.values() if r == 'SUCCESS')
        total_count = len(results)
        
        print(f"🎯 ENDPOINTS: {success_count}/{total_count} réussis")
        for endpoint, status in results.items():
            status_icon = "✅" if status == "SUCCESS" else "❌"
            print(f"   {status_icon} {endpoint}: {status}")
        
        print(f"🔍 LOGS PYTHON NATIF: {'✅ CONFIRMÉ' if logs_ok else '❌ NON CONFIRMÉ'}")
        
        # Informations document pour tests futurs
        print(f"\n📄 DOCUMENT CRÉÉ:")
        print(f"   📋 Organisation: {self.org_id}")
        print(f"   📂 Workspace: {self.workspace_id}")  
        print(f"   📄 Document: {self.doc_id}")
        print(f"   🔑 API Key: {self.api_key[:20]}..." if self.api_key else "   🔑 API Key: Non disponible")
        
        # Conclusion
        overall_success = success_count == total_count and logs_ok
        print(f"\n🏆 CONCLUSION: {'🎉 INTÉGRATION PYTHON NATIVE RÉUSSIE !' if overall_success else '⚠️  INTÉGRATION PARTIELLE - Voir détails ci-dessus'}")
        
        return overall_success

if __name__ == "__main__":
    tester = TestPythonNativeFinal()
    success = tester.run_complete_test()
    sys.exit(0 if success else 1)
