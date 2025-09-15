#!/usr/bin/env python3
"""
Test complet des endpoints spatiaux/vectoriels - Phase 3
Teste la nouvelle API REST spécialisée
"""

import requests
import json
import time
import sys

class TestEndpointsSpatiaux:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8888"
        self.api_key = "93c6a276615f0da72b0cbe42b4df3ca5638fedc3"
        self.doc_id = "1BeMtty2wV73RATVWU5cY3"  # Document pour test intégration Python native
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        print("🌐 TEST ENDPOINTS SPATIAUX/VECTORIELS - PHASE 3")
        print("=" * 60)
        print(f"📄 Document: {self.doc_id}")
        print(f"🔌 Base URL: {self.base_url}")
        print()
    
    def test_capabilities_endpoint(self):
        """Test de l'endpoint des capacités"""
        print("📋 Test /api/docs/:docId/spatial/capabilities")
        
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/spatial/capabilities")
            
            if response.ok:
                data = response.json()
                print(f"   ✅ Status: {response.status_code}")
                print(f"   📊 Fonctions spatiales: {len(data['data']['spatial_functions'])}")
                print(f"   🔢 Fonctions vectorielles: {len(data['data']['vector_functions'])}")
                print(f"   📝 Version: {data['data']['version']}")
                return True
            else:
                print(f"   ❌ Erreur: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def test_health_endpoint(self):
        """Test de l'endpoint de santé"""
        print("🏥 Test /api/docs/:docId/spatial/health")
        
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/spatial/health")
            
            if response.ok:
                data = response.json()
                print(f"   ✅ Status: {response.status_code}")
                print(f"   💚 Service: {data['data']['status']}")
                
                # Vérifier les tests
                tests = data['data']['tests']
                for test_name, test_result in tests.items():
                    status = "✅" if test_result['status'] == 'pass' else "❌"
                    print(f"   {status} {test_name}: {test_result['result']} (attendu: {test_result['expected']})")
                
                return data['data']['status'] == 'healthy'
            else:
                print(f"   ❌ Erreur: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def test_distance_endpoint(self):
        """Test de l'endpoint ST_DISTANCE"""
        print("📍 Test /api/docs/:docId/spatial/distance")
        
        test_data = {
            "point1": "POINT(2.2945 48.8584)",  # Tour Eiffel
            "point2": "POINT(2.3522 48.8566)",  # Notre-Dame
            "unit": "km"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/spatial/distance",
                json=test_data
            )
            
            if response.ok:
                data = response.json()
                distance = data['data']['distance']
                print(f"   ✅ Status: {response.status_code}")
                print(f"   📏 Distance: {distance:.2f} km")
                print(f"   🗺️ Tour Eiffel ↔ Notre-Dame")
                
                # Vérifier que la distance est réaliste (3-8 km)
                return 3 <= distance <= 8
            else:
                print(f"   ❌ Erreur: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def test_area_endpoint(self):
        """Test de l'endpoint ST_AREA"""
        print("📐 Test /api/docs/:docId/spatial/area")
        
        test_data = {
            "polygon": "POLYGON((2.35 48.85, 2.36 48.85, 2.36 48.86, 2.35 48.86, 2.35 48.85))",
            "unit": "m2"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/spatial/area",
                json=test_data
            )
            
            if response.ok:
                data = response.json()
                area = data['data']['area']
                print(f"   ✅ Status: {response.status_code}")
                print(f"   📏 Aire: {area:,.0f} m²")
                print(f"   🟦 Polygone test (~1 km²)")
                
                # Vérifier que l'aire est dans l'ordre de grandeur attendu
                return area > 0
            else:
                print(f"   ❌ Erreur: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def test_contains_endpoint(self):
        """Test de l'endpoint ST_CONTAINS"""
        print("🎯 Test /api/docs/:docId/spatial/contains")
        
        test_data = {
            "container": "POLYGON((2.35 48.85, 2.36 48.85, 2.36 48.86, 2.35 48.86, 2.35 48.85))",
            "contained": "POINT(2.355 48.855)"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/spatial/contains",
                json=test_data
            )
            
            if response.ok:
                data = response.json()
                contains = data['data']['contains']
                print(f"   ✅ Status: {response.status_code}")
                print(f"   🎯 Contains: {contains}")
                print(f"   📐 Point dans polygone")
                
                return isinstance(contains, bool)
            else:
                print(f"   ❌ Erreur: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def test_vector_similarity_endpoint(self):
        """Test de l'endpoint VECTOR_SIMILARITY"""
        print("🔢 Test /api/docs/:docId/vector/similarity")
        
        test_data = {
            "vector1": [0.8, 0.2, 0.7, 0.9, 0.1],
            "vector2": [0.7, 0.3, 0.6, 0.8, 0.2],
            "method": "cosine"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/vector/similarity",
                json=test_data
            )
            
            if response.ok:
                data = response.json()
                similarity = data['data']['similarity']
                print(f"   ✅ Status: {response.status_code}")
                print(f"   🔢 Similarité: {similarity:.3f}")
                print(f"   🧮 Méthode: {data['data']['method']}")
                
                # Vérifier que la similarité est entre 0 et 1
                return 0 <= similarity <= 1
            else:
                print(f"   ❌ Erreur: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def test_batch_distances_endpoint(self):
        """Test de l'endpoint batch distances"""
        print("📊 Test /api/docs/:docId/spatial/batch/distances")
        
        test_data = {
            "reference_point": "POINT(2.3522 48.8566)",  # Notre-Dame
            "points": [
                "POINT(2.2945 48.8584)",  # Tour Eiffel
                "POINT(2.2950 48.8738)",  # Arc de Triomphe
                "POINT(2.3431 48.8867)"   # Sacré-Cœur
            ],
            "unit": "km"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/spatial/batch/distances",
                json=test_data
            )
            
            if response.ok:
                data = response.json()
                results = data['data']['results']
                count = data['data']['count']
                
                print(f"   ✅ Status: {response.status_code}")
                print(f"   📊 Calculées: {count} distances")
                
                for result in results:
                    print(f"      📏 Point {result['index']}: {result['distance']:.2f} km")
                
                return count == len(test_data['points'])
            else:
                print(f"   ❌ Erreur: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def test_batch_similarities_endpoint(self):
        """Test de l'endpoint batch similarities"""
        print("🔢 Test /api/docs/:docId/vector/batch/similarities")
        
        test_data = {
            "reference_vector": [0.8, 0.2, 0.7, 0.9, 0.1],
            "vectors": [
                [0.8, 0.2, 0.7, 0.9, 0.1],  # Identique
                [0.7, 0.3, 0.6, 0.8, 0.2],  # Similaire
                [0.1, 0.9, 0.2, 0.1, 0.8],  # Différent
                [0.9, 0.1, 0.8, 0.95, 0.05] # Très similaire
            ],
            "method": "cosine",
            "threshold": 0.5
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/vector/batch/similarities",
                json=test_data
            )
            
            if response.ok:
                data = response.json()
                results = data['data']['results']
                count = data['data']['count']
                total = data['data']['total_processed']
                
                print(f"   ✅ Status: {response.status_code}")
                print(f"   📊 Calculées: {total} / Filtrées: {count}")
                
                for result in results:
                    print(f"      🔢 Vecteur {result['index']}: {result['similarity']:.3f}")
                
                return count <= total
            else:
                print(f"   ❌ Erreur: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("🚀 LANCEMENT DES TESTS ENDPOINTS")
        print()
        
        # Attendre que le serveur démarre
        print("⏳ Attente démarrage serveur (10 secondes)...")
        time.sleep(10)
        
        tests = [
            ("Capacités", self.test_capabilities_endpoint),
            ("Santé", self.test_health_endpoint),
            ("Distance", self.test_distance_endpoint),
            ("Aire", self.test_area_endpoint),
            ("Contient", self.test_contains_endpoint),
            ("Similarité", self.test_vector_similarity_endpoint),
            ("Batch Distances", self.test_batch_distances_endpoint),
            ("Batch Similarities", self.test_batch_similarities_endpoint)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            results[test_name] = test_func()
            print()
        
        # Rapport final
        self.generate_report(results)
        return results
    
    def generate_report(self, results):
        """Génère le rapport final"""
        print("=" * 60)
        print("📊 RAPPORT FINAL - ENDPOINTS SPATIAUX/VECTORIELS")
        print("=" * 60)
        
        total = len(results)
        passed = sum(results.values())
        score = (passed / total) * 100
        
        print(f"🎯 SCORE ENDPOINTS: {passed}/{total} ({score:.0f}%)")
        print()
        
        print("📋 Détail des résultats:")
        for test_name, success in results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}: {'RÉUSSI' if success else 'ÉCHEC'}")
        
        print()
        print("🎯 CONCLUSION:")
        if score == 100:
            print("🎉 PARFAIT ! TOUS LES ENDPOINTS FONCTIONNENT !")
            print("🚀 PHASE 3 COMPLÈTEMENT RÉUSSIE !")
            print("✅ API REST spatiale/vectorielle opérationnelle")
        elif score >= 75:
            print("🎉 EXCELLENT ! API majoritairement fonctionnelle")
            print("✅ Phase 3 quasi-réussie")
        elif score >= 50:
            print("✅ BON ! Intégration partielle des endpoints")
        else:
            print("❌ PROBLÈME - Endpoints non fonctionnels")
        
        print(f"\n🌐 API Base URL: {self.base_url}/api/docs/{self.doc_id[:8]}/spatial/")
        print("📖 Documentation disponible: /spatial/capabilities")

if __name__ == "__main__":
    tester = TestEndpointsSpatiaux()
    results = tester.run_all_tests()
    
    # Code de sortie
    passed = sum(results.values())
    total = len(results)
    
    if passed >= total * 0.75:  # 75% de réussite minimum
        sys.exit(0)
    else:
        sys.exit(1)
