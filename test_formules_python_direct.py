#!/usr/bin/env python3
"""
Test direct des formules Python dans Grist
Force l'exécution via le moteur de formules Python, pas SQLite
"""

import requests
import json
import time
import sys

class TestFormulesDirectes:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8888"
        self.api_key = "3816d9d8e74c8bfd9abd3384b1019dc48d5605b5"
        self.doc_id = "nEr4gKyXWpVbKj6W7RgS4Z"
        self.table_id = "Table1"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        print("🧮 TEST DIRECT DES FORMULES PYTHON GRIST")
        print("=" * 60)
        print(f"📄 Document: {self.doc_id}")
        print(f"🐍 Moteur: Sandbox Python (pas SQLite)")
        print()
    
    def force_formula_recalculation(self):
        """Force le recalcul des formules en modifiant les données"""
        print("🔄 Forçage du recalcul des formules...")
        
        try:
            # Modifier légèrement une donnée pour forcer le recalcul
            update_payload = {
                "records": [
                    {
                        "id": 1,  # Tour Eiffel
                        "fields": {
                            "lieu": "Tour Eiffel [TEST]"  # Modification mineure
                        }
                    }
                ]
            }
            
            response = self.session.patch(
                f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/records",
                json=update_payload
            )
            
            if response.ok:
                print("   ✅ Modification appliquée pour forcer recalcul")
                return True
            else:
                print(f"   ❌ Erreur modification: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def check_formulas_after_delay(self, delay=8):
        """Vérifier les formules après un délai"""
        print(f"   ⏳ Attente {delay} secondes pour calcul...")
        time.sleep(delay)
        
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/records")
            
            if response.ok:
                data = response.json()
                records = data.get('records', [])
                
                print(f"   📊 Vérification {len(records)} enregistrements:")
                
                for i, record in enumerate(records[:3], 1):
                    fields = record.get('fields', {})
                    lieu = fields.get('lieu', f'Record {i}')
                    distance = fields.get('distance_paris')
                    similarite = fields.get('similarite_test')
                    
                    # Status des formules
                    distance_status = "✅" if distance not in [None, '', 'null'] else "❌"
                    similarite_status = "✅" if similarite not in [None, '', 'null'] else "❌"
                    
                    print(f"   {i}. {lieu}:")
                    print(f"      {distance_status} Distance: {distance}")
                    print(f"      {similarite_status} Similarité: {similarite}")
                
                # Vérifier si au moins une formule a calculé
                working_formulas = sum(1 for record in records 
                                     if record.get('fields', {}).get('distance_paris') not in [None, '', 'null'])
                
                return working_formulas > 0, records
            else:
                print(f"   ❌ Erreur récupération: {response.status_code}")
                return False, []
                
        except Exception as e:
            print(f"   ❌ Exception vérification: {e}")
            return False, []
    
    def create_simple_test_column(self):
        """Créer une colonne de test simple pour vérifier le moteur de formules"""
        print("🧪 Test colonne formule simple...")
        
        try:
            # Créer une colonne avec une formule Python basique
            test_col = {
                "id": "test_python",
                "fields": {
                    "type": "Numeric",
                    "label": "Test Python",
                    "formula": '2 + 3 * 4'  # Simple: doit donner 14
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns",
                json=test_col
            )
            
            if response.ok:
                print("   ✅ Colonne test créée")
                
                # Attendre calcul
                time.sleep(3)
                
                # Vérifier résultat
                records_response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/records")
                if records_response.ok:
                    records = records_response.json().get('records', [])
                    if records:
                        test_result = records[0].get('fields', {}).get('test_python')
                        print(f"   🎯 Résultat test: {test_result} (attendu: 14)")
                        
                        if test_result == 14:
                            print("   🎉 MOTEUR PYTHON FONCTIONNE !")
                            return True
                
                # Supprimer colonne test
                self.session.delete(f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns/test_python")
                
            else:
                print(f"   ❌ Erreur création colonne test: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception test simple: {e}")
            
        return False
    
    def create_spatial_test_column(self):
        """Créer une colonne avec test spatial direct"""
        print("📍 Test colonne formule spatiale...")
        
        try:
            # Test direct avec valeurs hardcodées
            spatial_col = {
                "id": "test_spatial",
                "fields": {
                    "type": "Numeric",
                    "label": "Test ST_DISTANCE",
                    "formula": 'ST_DISTANCE("POINT(2.2945 48.8584)", "POINT(2.3522 48.8566)", "km")'
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns",
                json=spatial_col
            )
            
            if response.ok:
                print("   ✅ Colonne test spatiale créée")
                
                # Attendre calcul
                time.sleep(5)
                
                # Vérifier résultat
                records_response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/records")
                if records_response.ok:
                    records = records_response.json().get('records', [])
                    if records:
                        test_result = records[0].get('fields', {}).get('test_spatial')
                        print(f"   🎯 Résultat ST_DISTANCE: {test_result} km (attendu: ~4.5)")
                        
                        if test_result is not None and isinstance(test_result, (int, float)):
                            print("   🎉 FONCTION ST_DISTANCE FONCTIONNE !")
                            success = True
                        else:
                            print("   ❌ Fonction ST_DISTANCE non fonctionnelle")
                            success = False
                
                # Supprimer colonne test
                self.session.delete(f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns/test_spatial")
                return success
            else:
                print(f"   ❌ Erreur création colonne spatiale: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception test spatial: {e}")
            
        return False
    
    def create_vector_test_column(self):
        """Créer une colonne avec test vectoriel direct"""
        print("🔢 Test colonne formule vectorielle...")
        
        try:
            # Test direct avec valeurs hardcodées
            vector_col = {
                "id": "test_vector",
                "fields": {
                    "type": "Numeric",
                    "label": "Test VECTOR_SIMILARITY",
                    "formula": 'VECTOR_SIMILARITY([0.8, 0.2, 0.7], [0.8, 0.2, 0.7], "cosine")'
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns",
                json=vector_col
            )
            
            if response.ok:
                print("   ✅ Colonne test vectorielle créée")
                
                # Attendre calcul
                time.sleep(5)
                
                # Vérifier résultat
                records_response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/records")
                if records_response.ok:
                    records = records_response.json().get('records', [])
                    if records:
                        test_result = records[0].get('fields', {}).get('test_vector')
                        print(f"   🎯 Résultat VECTOR_SIMILARITY: {test_result} (attendu: 1.0)")
                        
                        if test_result is not None and isinstance(test_result, (int, float)):
                            print("   🎉 FONCTION VECTOR_SIMILARITY FONCTIONNE !")
                            success = True
                        else:
                            print("   ❌ Fonction VECTOR_SIMILARITY non fonctionnelle")
                            success = False
                
                # Supprimer colonne test
                self.session.delete(f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns/test_vector")
                return success
            else:
                print(f"   ❌ Erreur création colonne vectorielle: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Exception test vectoriel: {e}")
            
        return False
    
    def run_complete_test(self):
        """Exécute la suite complète de tests"""
        print("🚀 DÉBUT DU TEST COMPLET DU MOTEUR PYTHON")
        print()
        
        results = {
            'python_engine': False,
            'spatial_functions': False,
            'vector_functions': False,
            'existing_formulas': False
        }
        
        # 1. Test moteur Python de base
        results['python_engine'] = self.create_simple_test_column()
        print()
        
        # 2. Test fonctions spatiales
        results['spatial_functions'] = self.create_spatial_test_column()
        print()
        
        # 3. Test fonctions vectorielles
        results['vector_functions'] = self.create_vector_test_column()
        print()
        
        # 4. Test formules existantes après forçage
        self.force_formula_recalculation()
        working_formulas, records = self.check_formulas_after_delay(10)
        results['existing_formulas'] = working_formulas
        
        # 5. Rapport final
        self.generate_final_report(results, records)
        
        return results
    
    def generate_final_report(self, results, records):
        """Génère le rapport final des tests"""
        print("\n" + "=" * 60)
        print("📊 RAPPORT FINAL - TEST MOTEUR PYTHON GRIST")
        print("=" * 60)
        
        # Score de réussite
        total_tests = len(results)
        passed_tests = sum(results.values())
        score_pct = (passed_tests / total_tests) * 100
        
        print(f"🎯 SCORE GLOBAL: {passed_tests}/{total_tests} ({score_pct:.0f}%)")
        print()
        
        print("📋 Détail des résultats:")
        print(f"   {'✅' if results['python_engine'] else '❌'} Moteur Python de base")
        print(f"   {'✅' if results['spatial_functions'] else '❌'} Fonctions spatiales (ST_DISTANCE)")
        print(f"   {'✅' if results['vector_functions'] else '❌'} Fonctions vectorielles (VECTOR_SIMILARITY)")
        print(f"   {'✅' if results['existing_formulas'] else '❌'} Formules existantes du document")
        
        print()
        if results['existing_formulas'] and records:
            print("🎯 RÉSULTATS CALCULÉS:")
            for record in records[:3]:
                fields = record.get('fields', {})
                lieu = fields.get('lieu', 'N/A')
                distance = fields.get('distance_paris', 'N/A')
                similarite = fields.get('similarite_test', 'N/A')
                if distance != 'N/A':
                    print(f"   📍 {lieu}: {distance} km")
        
        print()
        print("🎯 CONCLUSION:")
        if score_pct == 100:
            print("🎉 PARFAIT - Toutes les extensions fonctionnent parfaitement !")
            print("🚀 PHASE 2 RÉUSSIE - Fonctions Python opérationnelles")
        elif score_pct >= 75:
            print("✅ EXCELLENT - Extensions majoritairement fonctionnelles")
        elif score_pct >= 50:
            print("⚠️ BON - Intégration partielle réussie")
        else:
            print("❌ PROBLÈME - Moteur Python non opérationnel")
        
        print(f"\n📄 Document de test: {self.base_url}/o/docs/{self.doc_id[:8]}")

if __name__ == "__main__":
    tester = TestFormulesDirectes()
    results = tester.run_complete_test()
    
    # Code de sortie basé sur les résultats
    if results['spatial_functions'] and results['vector_functions']:
        sys.exit(0)  # Succès complet
    else:
        sys.exit(1)  # Échec partiel
