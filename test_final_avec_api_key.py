#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST FINAL AVEC API KEY FOURNIE
Utilise l'API key fournie pour créer un document et tester les fonctions Python natives
"""

import requests
import json
import time
import sys

class TestFinalPythonNative:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8888"
        self.api_key = "10005e103cc5a462fa8080aa57f8a9e5ec9bd314"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        self.org_id = None
        self.workspace_id = None  
        self.doc_id = None
        
    def create_test_document(self):
        """Créer un nouveau document pour les tests ou utiliser un existant"""
        print("\n📄 CRÉATION DOCUMENT DE TEST")
        print("=" * 40)
        
        # Essayer d'abord avec un document existant visible dans les logs
        existing_doc = "p1UAgEqaxemRSvh1XwmyZ1"
        print(f"🔍 Test avec document existant: {existing_doc}")
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{existing_doc}")
            if response.status_code == 200:
                self.doc_id = existing_doc
                self.org_id = 2  # Vu dans les logs
                self.workspace_id = 2
                print(f"✅ Document existant utilisé: {self.doc_id}")
                return True
        except:
            pass
        
        print("🆕 Création nouveau document...")
        
        try:
            # 1. Récupérer les organisations
            print("📋 Récupération organisations...")
            response = self.session.get(f"{self.base_url}/api/orgs")
            if response.status_code != 200:
                print(f"❌ Erreur orgs: {response.status_code} - {response.text}")
                return False
                
            orgs = response.json()
            if not orgs:
                print("❌ Aucune organisation trouvée")
                return False
                
            self.org_id = orgs[0]['id']
            print(f"✅ Organisation: {self.org_id}")
            
            # 2. Récupérer les workspaces
            print("📂 Récupération workspaces...")
            response = self.session.get(f"{self.base_url}/api/orgs/{self.org_id}/workspaces")
            if response.status_code != 200:
                print(f"❌ Erreur workspaces: {response.status_code} - {response.text}")
                return False
                
            workspaces = response.json()
            if not workspaces:
                print("❌ Aucun workspace trouvé")
                return False
                
            self.workspace_id = workspaces[0]['id']
            print(f"✅ Workspace: {self.workspace_id}")
            
            # 3. Créer le document de test
            print("🆕 Création document...")
            doc_data = {"name": "Test Fonctions Python Natives"}
            response = self.session.post(f"{self.base_url}/api/workspaces/{self.workspace_id}/docs", 
                                       json=doc_data)
            if response.status_code not in [200, 201]:
                print(f"❌ Erreur création document: {response.status_code} - {response.text}")
                return False
                
            doc_response = response.json()
            
            # Gestion flexible de la réponse (string ou dict)
            if isinstance(doc_response, dict):
                self.doc_id = doc_response.get('id') or doc_response.get('docId')
            else:
                self.doc_id = str(doc_response)
                
            print(f"✅ Document créé: {self.doc_id}")
            print(f"   📋 Type réponse: {type(doc_response)}")
            print(f"   📄 Réponse complète: {doc_response}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur création document: {e}")
            return False
    
    def test_spatial_endpoints(self):
        """Tester les endpoints spatiaux avec les fonctions Python natives"""
        print("\n🧪 TEST ENDPOINTS SPATIAUX")
        print("=" * 40)
        
        results = {}
        
        # Test 1: Capabilities
        print("📋 Test capabilities...")
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/spatial/capabilities")
            if response.status_code == 200:
                data = response.json()
                spatial_funcs = len(data.get('data', {}).get('features', {}).get('spatial_functions', []))
                vector_funcs = len(data.get('data', {}).get('features', {}).get('vector_functions', []))
                print(f"✅ Capabilities: {spatial_funcs} fonctions spatiales, {vector_funcs} fonctions vectorielles")
                results['capabilities'] = True
            else:
                print(f"❌ Capabilities failed: {response.status_code}")
                results['capabilities'] = False
        except Exception as e:
            print(f"❌ Capabilities error: {e}")
            results['capabilities'] = False
        
        # Test 2: Health check avec détection Python natif
        print("🏥 Test health check...")
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/spatial/health")
            if response.status_code == 200:
                data = response.json()
                status = data.get('data', {}).get('status', 'unknown')
                distance_test = data.get('data', {}).get('tests', {}).get('st_distance', {})
                vector_test = data.get('data', {}).get('tests', {}).get('vector_similarity', {})
                
                distance_result = distance_test.get('result', 0)
                vector_result = vector_test.get('result', 0)
                
                print(f"✅ Health: {status}")
                print(f"   📏 ST_DISTANCE: {distance_result} (test 0°→1° = ~111km)")
                print(f"   🔢 VECTOR_SIMILARITY: {vector_result} (test identiques = 1.0)")
                
                # Détection si les résultats correspondent aux fonctions Python natives
                is_native = (distance_result > 100 and vector_result == 1.0)
                print(f"   🔍 Python natif détecté: {'✅ OUI' if is_native else '❌ NON (mocks)'}")
                
                results['health'] = True
                results['python_native'] = is_native
            else:
                print(f"❌ Health failed: {response.status_code}")
                results['health'] = False
                results['python_native'] = False
        except Exception as e:
            print(f"❌ Health error: {e}")
            results['health'] = False
            results['python_native'] = False
        
        # Test 3: Distance calculation
        print("📍 Test distance calculation...")
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
                distance = data.get('data', {}).get('distance', 0)
                print(f"✅ Distance Tour Eiffel ↔ Notre-Dame: {distance:.2f} km")
                results['distance'] = True
            else:
                print(f"❌ Distance failed: {response.status_code}")
                results['distance'] = False
        except Exception as e:
            print(f"❌ Distance error: {e}")
            results['distance'] = False
        
        # Test 4: Area calculation
        print("📐 Test area calculation...")
        try:
            payload = {
                "polygon": "POLYGON((2.35 48.85, 2.36 48.85, 2.36 48.86, 2.35 48.86, 2.35 48.85))",
                "unit": "m2"
            }
            response = self.session.post(f"{self.base_url}/api/docs/{self.doc_id}/spatial/area", 
                                       json=payload)
            if response.status_code == 200:
                data = response.json()
                area = data.get('data', {}).get('area', 0)
                print(f"✅ Aire polygone: {area:,.0f} m²")
                results['area'] = True
            else:
                print(f"❌ Area failed: {response.status_code}")
                results['area'] = False
        except Exception as e:
            print(f"❌ Area error: {e}")
            results['area'] = False
        
        # Test 5: Vector similarity
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
                similarity = data.get('data', {}).get('similarity', 0)
                print(f"✅ Similarité vectorielle: {similarity:.3f}")
                results['similarity'] = True
            else:
                print(f"❌ Similarity failed: {response.status_code}")
                results['similarity'] = False
        except Exception as e:
            print(f"❌ Similarity error: {e}")
            results['similarity'] = False
            
        return results
    
    def check_container_logs(self):
        """Vérifier les logs du container pour les indicateurs Python natif"""
        print("\n🔍 VÉRIFICATION LOGS CONTAINER")
        print("=" * 40)
        
        try:
            import subprocess
            
            # Récupérer les logs récents
            result = subprocess.run([
                'docker', 'logs', 'grist-python-native-final', '--tail', '100'
            ], capture_output=True, text=True, shell=True)
            
            logs = result.stdout + result.stderr
            
            # Indicateurs d'intégration Python native
            indicators = {
                "Fonctions enregistrées": "✅ Fonctions spatiales/vectorielles enregistrées",
                "Sandbox Python natif": "✅ Utilisation du sandbox Python natif",
                "Accès DocManager": "✅ Accès réussi au document",
                "Endpoints spatiaux": "✅ Endpoints spatiaux/vectoriels"
            }
            
            found = {}
            for name, pattern in indicators.items():
                found[name] = pattern in logs
                status = "✅" if found[name] else "❌"
                print(f"{status} {name}: {'TROUVÉ' if found[name] else 'NON TROUVÉ'}")
            
            # Chercher spécifiquement les erreurs KeyError (qui indiqueraient un problème)
            keyerrors = logs.count("KeyError")
            if keyerrors > 0:
                print(f"⚠️  {keyerrors} erreurs KeyError trouvées (fonctions non enregistrées?)")
            else:
                print("✅ Aucune erreur KeyError (fonctions bien enregistrées)")
                
            return found
            
        except Exception as e:
            print(f"❌ Erreur vérification logs: {e}")
            return {}
    
    def run_complete_test(self):
        """Exécuter le test complet"""
        print("🚀 TEST COMPLET FONCTIONS PYTHON NATIVES")
        print("=" * 60)
        print(f"🔑 API Key: {self.api_key[:20]}...")
        print(f"🌐 Base URL: {self.base_url}")
        
        # Étape 1: Créer le document de test
        if not self.create_test_document():
            print("\n❌ ÉCHEC: Impossible de créer le document de test")
            return False
        
        # Attendre un peu pour la stabilisation
        print("\n⏳ Attente stabilisation (5 secondes)...")
        time.sleep(5)
        
        # Étape 2: Tester les endpoints
        endpoint_results = self.test_spatial_endpoints()
        
        # Étape 3: Vérifier les logs
        log_results = self.check_container_logs()
        
        # Rapport final
        print("\n" + "=" * 60)
        print("📊 RAPPORT FINAL - FONCTIONS PYTHON NATIVES")
        print("=" * 60)
        
        # Résultats endpoints
        success_count = sum(1 for v in endpoint_results.values() if v and isinstance(v, bool))
        total_count = sum(1 for v in endpoint_results.values() if isinstance(v, bool))
        
        print(f"🎯 ENDPOINTS: {success_count}/{total_count} réussis")
        for test, result in endpoint_results.items():
            if isinstance(result, bool):
                status = "✅" if result else "❌"
                print(f"   {status} {test}: {'RÉUSSI' if result else 'ÉCHEC'}")
        
        # Détection Python natif
        python_native = endpoint_results.get('python_native', False)
        print(f"\n🐍 PYTHON NATIF: {'✅ CONFIRMÉ' if python_native else '❌ NON CONFIRMÉ (utilise les mocks)'}")
        
        # Résultats logs
        log_success = sum(1 for v in log_results.values() if v)
        log_total = len(log_results)
        print(f"🔍 LOGS CONTAINER: {log_success}/{log_total} indicateurs trouvés")
        
        # Informations pour tests futurs
        print(f"\n📄 DOCUMENT CRÉÉ POUR TESTS:")
        print(f"   📋 Organisation: {self.org_id}")
        print(f"   📂 Workspace: {self.workspace_id}")
        print(f"   📄 Document: {self.doc_id}")
        print(f"   🔑 API Key: {self.api_key}")
        
        # Conclusion globale
        overall_success = success_count == total_count and python_native
        print(f"\n🏆 CONCLUSION GLOBALE:")
        if overall_success:
            print("🎉 INTÉGRATION PYTHON NATIVE COMPLÈTEMENT RÉUSSIE !")
            print("✅ Tous les endpoints fonctionnent avec les vraies fonctions Python")
        else:
            print("⚠️  INTÉGRATION PARTIELLE:")
            if success_count < total_count:
                print(f"   - {total_count - success_count} endpoint(s) en échec")
            if not python_native:
                print("   - Les fonctions utilisent encore les mocks TypeScript")
                print("   - Les fonctions Python ne sont pas correctement intégrées aux endpoints")
        
        return overall_success

if __name__ == "__main__":
    tester = TestFinalPythonNative()
    success = tester.run_complete_test()
    sys.exit(0 if success else 1)
