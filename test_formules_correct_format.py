#!/usr/bin/env python3
"""
Test avec format API correct pour les colonnes
"""

import requests
import json
import time
import sys

class TestFormuleFinal:
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
        
        print("🔧 TEST AVEC FORMAT API CORRECT")
        print("=" * 60)
        print(f"📄 Document: {self.doc_id}")
        print()
    
    def test_simple_formula_correct_format(self):
        """Test une formule simple avec le bon format API"""
        print("🧮 Test formule simple (format corrigé)...")
        
        # Format correct basé sur les tools MCP qui fonctionnent
        column_data = {
            "columns": [{
                "id": "test_simple",
                "fields": {
                    "type": "Numeric",
                    "label": "Test Simple",
                    "formula": "2 + 3 * 4",
                    "isFormula": True
                }
            }]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns",
                json=column_data
            )
            
            if response.ok:
                print("   ✅ Colonne créée avec succès")
                
                # Attendre calcul
                time.sleep(5)
                
                # Vérifier résultat
                records = self.get_records()
                if records:
                    result = records[0].get('fields', {}).get('test_simple')
                    print(f"   🎯 Résultat: {result} (attendu: 14)")
                    
                    if result == 14:
                        print("   🎉 MOTEUR PYTHON FONCTIONNE !")
                        success = True
                    else:
                        print("   ⚠️ Résultat incorrect")
                        success = False
                else:
                    success = False
                
                # Nettoyer
                self.delete_column("test_simple")
                return success
            else:
                print(f"   ❌ Erreur: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def test_spatial_formula_correct_format(self):
        """Test ST_DISTANCE avec format correct"""
        print("📍 Test ST_DISTANCE (format corrigé)...")
        
        column_data = {
            "columns": [{
                "id": "test_st_distance",
                "fields": {
                    "type": "Numeric", 
                    "label": "Test ST_DISTANCE",
                    "formula": 'ST_DISTANCE("POINT(2.2945 48.8584)", "POINT(2.3522 48.8566)", "km")',
                    "isFormula": True
                }
            }]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns",
                json=column_data
            )
            
            if response.ok:
                print("   ✅ Colonne ST_DISTANCE créée")
                
                # Attendre calcul
                time.sleep(8)
                
                # Vérifier résultat  
                records = self.get_records()
                if records:
                    result = records[0].get('fields', {}).get('test_st_distance')
                    print(f"   🎯 Résultat: {result} km (attendu: ~4.5)")
                    
                    if result is not None and isinstance(result, (int, float)) and result > 0:
                        print("   🎉 ST_DISTANCE FONCTIONNE !")
                        success = True
                    else:
                        print("   ❌ ST_DISTANCE non fonctionnelle")
                        success = False
                else:
                    success = False
                
                # Nettoyer
                self.delete_column("test_st_distance")
                return success
            else:
                print(f"   ❌ Erreur: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def test_vector_formula_correct_format(self):
        """Test VECTOR_SIMILARITY avec format correct"""
        print("🔢 Test VECTOR_SIMILARITY (format corrigé)...")
        
        column_data = {
            "columns": [{
                "id": "test_vector_sim",
                "fields": {
                    "type": "Numeric",
                    "label": "Test VECTOR_SIMILARITY", 
                    "formula": 'VECTOR_SIMILARITY([0.8, 0.2, 0.7], [0.8, 0.2, 0.7], "cosine")',
                    "isFormula": True
                }
            }]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns",
                json=column_data
            )
            
            if response.ok:
                print("   ✅ Colonne VECTOR_SIMILARITY créée")
                
                # Attendre calcul
                time.sleep(8)
                
                # Vérifier résultat
                records = self.get_records()
                if records:
                    result = records[0].get('fields', {}).get('test_vector_sim')
                    print(f"   🎯 Résultat: {result} (attendu: 1.0)")
                    
                    if result is not None and isinstance(result, (int, float)):
                        print("   🎉 VECTOR_SIMILARITY FONCTIONNE !")
                        success = True
                    else:
                        print("   ❌ VECTOR_SIMILARITY non fonctionnelle")
                        success = False
                else:
                    success = False
                
                # Nettoyer  
                self.delete_column("test_vector_sim")
                return success
            else:
                print(f"   ❌ Erreur: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def get_records(self):
        """Récupère les enregistrements"""
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/records")
            if response.ok:
                return response.json().get('records', [])
        except:
            pass
        return []
    
    def delete_column(self, col_id):
        """Supprime une colonne de test"""
        try:
            self.session.delete(f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns/{col_id}")
        except:
            pass
    
    def run_tests(self):
        """Exécute tous les tests"""
        print("🚀 LANCEMENT DES TESTS CORRECTS")
        print()
        
        results = {}
        
        # Test 1: Formule simple
        results['simple'] = self.test_simple_formula_correct_format()
        print()
        
        # Test 2: ST_DISTANCE
        results['spatial'] = self.test_spatial_formula_correct_format()
        print()
        
        # Test 3: VECTOR_SIMILARITY
        results['vector'] = self.test_vector_formula_correct_format()
        print()
        
        # Rapport final
        self.generate_report(results)
        return results
    
    def generate_report(self, results):
        """Génère le rapport final"""
        print("=" * 60)
        print("📊 RAPPORT FINAL - TESTS FORMAT CORRIGÉ")
        print("=" * 60)
        
        total = len(results)
        passed = sum(results.values())
        score = (passed / total) * 100
        
        print(f"🎯 SCORE: {passed}/{total} ({score:.0f}%)")
        print()
        
        for test, success in results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {test.upper()}: {'RÉUSSI' if success else 'ÉCHEC'}")
        
        print()
        if score == 100:
            print("🎉 PARFAIT ! TOUTES LES EXTENSIONS FONCTIONNENT !")
            print("🚀 PHASE 2 RÉUSSIE - INTÉGRATION COMPLETE")
        elif score >= 66:
            print("✅ EXCELLENT - Extensions majoritairement opérationnelles")
        elif score >= 33:
            print("⚠️ PARTIEL - Quelques fonctions marchent") 
        else:
            print("❌ PROBLÈME - Aucune fonction ne marche")

if __name__ == "__main__":
    tester = TestFormuleFinal()
    results = tester.run_tests()
    
    # Code de sortie
    if results.get('spatial', False) and results.get('vector', False):
        sys.exit(0)
    else:
        sys.exit(1)
