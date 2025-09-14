#!/usr/bin/env python3
"""
Test avec syntaxe correcte: grist.ST_DISTANCE() au lieu de ST_DISTANCE()
"""

import requests
import time
import sys

class TestSyntaxeCorrecte:
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
        
        print("🎯 TEST AVEC SYNTAXE GRIST CORRECTE")
        print("=" * 60)
        print(f"📄 Document: {self.doc_id}")
        print(f"✅ Syntaxe: grist.ST_DISTANCE() au lieu de ST_DISTANCE()")
        print()
    
    def test_grist_st_distance(self):
        """Test grist.ST_DISTANCE avec syntaxe correcte"""
        print("📍 Test grist.ST_DISTANCE()...")
        
        column_data = {
            "columns": [{
                "id": "test_grist_st_distance",
                "fields": {
                    "type": "Numeric", 
                    "label": "Test grist.ST_DISTANCE",
                    "formula": 'grist.ST_DISTANCE("POINT(2.2945 48.8584)", "POINT(2.3522 48.8566)", "km")',
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
                print("   ✅ Colonne créée")
                time.sleep(8)
                
                records = self.get_records()
                if records:
                    result = records[0].get('fields', {}).get('test_grist_st_distance')
                    print(f"   🎯 Résultat: {result} km")
                    
                    if result is not None and isinstance(result, (int, float)) and result > 0:
                        print(f"   🎉 SUCCESS ! Distance Tour Eiffel-Notre Dame: {result:.2f} km")
                        success = True
                    else:
                        print("   ❌ Pas de résultat valide")
                        success = False
                else:
                    success = False
                
                self.delete_column("test_grist_st_distance")
                return success
            else:
                print(f"   ❌ Erreur création: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def test_grist_vector_similarity(self):
        """Test grist.VECTOR_SIMILARITY avec syntaxe correcte"""
        print("🔢 Test grist.VECTOR_SIMILARITY()...")
        
        column_data = {
            "columns": [{
                "id": "test_grist_vector_sim",
                "fields": {
                    "type": "Numeric",
                    "label": "Test grist.VECTOR_SIMILARITY", 
                    "formula": 'grist.VECTOR_SIMILARITY([0.8, 0.2, 0.7], [0.8, 0.2, 0.7], "cosine")',
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
                print("   ✅ Colonne créée")
                time.sleep(8)
                
                records = self.get_records()
                if records:
                    result = records[0].get('fields', {}).get('test_grist_vector_sim')
                    print(f"   🎯 Résultat: {result}")
                    
                    if result is not None and isinstance(result, (int, float)):
                        print(f"   🎉 SUCCESS ! Similarité vecteurs identiques: {result}")
                        success = True
                    else:
                        print("   ❌ Pas de résultat valide")
                        success = False
                else:
                    success = False
                
                self.delete_column("test_grist_vector_sim")
                return success
            else:
                print(f"   ❌ Erreur création: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def test_grist_st_area(self):
        """Test grist.ST_AREA avec un polygone simple"""
        print("📐 Test grist.ST_AREA()...")
        
        # Petit carré d'environ 1km x 1km autour de Paris
        polygon_wkt = 'POLYGON((2.35 48.85, 2.36 48.85, 2.36 48.86, 2.35 48.86, 2.35 48.85))'
        
        column_data = {
            "columns": [{
                "id": "test_grist_st_area",
                "fields": {
                    "type": "Numeric",
                    "label": "Test grist.ST_AREA",
                    "formula": f'grist.ST_AREA("{polygon_wkt}", "m2")',
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
                print("   ✅ Colonne créée")
                time.sleep(8)
                
                records = self.get_records()
                if records:
                    result = records[0].get('fields', {}).get('test_grist_st_area')
                    print(f"   🎯 Résultat: {result} m²")
                    
                    if result is not None and isinstance(result, (int, float)) and result > 0:
                        print(f"   🎉 SUCCESS ! Aire du polygone: {result:,.0f} m²")
                        success = True
                    else:
                        print("   ❌ Pas de résultat valide")
                        success = False
                else:
                    success = False
                
                self.delete_column("test_grist_st_area")
                return success
            else:
                print(f"   ❌ Erreur création: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def fix_existing_formulas(self):
        """Corriger les formules existantes avec grist. prefix"""
        print("🔧 Correction des formules existantes...")
        
        corrections = [
            {
                "column_id": "distance_paris",
                "new_formula": 'grist.ST_DISTANCE($position, "POINT(2.3522 48.8566)", "km")'
            },
            {
                "column_id": "similarite_test", 
                "new_formula": 'grist.VECTOR_SIMILARITY($caracteristiques, [0.8, 0.2, 0.5], "cosine")'
            }
        ]
        
        for correction in corrections:
            try:
                update_data = {
                    "columns": [{
                        "id": correction["column_id"],
                        "fields": {
                            "formula": correction["new_formula"]
                        }
                    }]
                }
                
                response = self.session.patch(
                    f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns",
                    json=update_data
                )
                
                if response.ok:
                    print(f"   ✅ Formule corrigée: {correction['column_id']}")
                else:
                    print(f"   ⚠️ Erreur correction {correction['column_id']}: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ Exception correction {correction['column_id']}: {e}")
        
        print("   ⏳ Attente recalcul (10 secondes)...")
        time.sleep(10)
        
        # Vérifier les résultats
        records = self.get_records()
        if records:
            print("   📊 Résultats après correction:")
            for i, record in enumerate(records[:3], 1):
                fields = record.get('fields', {})
                lieu = fields.get('lieu', f'Record {i}')
                distance = fields.get('distance_paris')
                similarite = fields.get('similarite_test')
                
                print(f"   {i}. {lieu}:")
                print(f"      Distance: {distance} km")
                print(f"      Similarité: {similarite}")
            
            # Vérifier si au moins une formule marche
            working = any(record.get('fields', {}).get('distance_paris') not in [None, '', 'null']
                         for record in records)
            return working
        
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
        print("🚀 LANCEMENT DES TESTS SYNTAXE CORRECTE")
        print()
        
        results = {}
        
        # Test 1: ST_DISTANCE
        results['st_distance'] = self.test_grist_st_distance()
        print()
        
        # Test 2: VECTOR_SIMILARITY
        results['vector_sim'] = self.test_grist_vector_similarity()
        print()
        
        # Test 3: ST_AREA
        results['st_area'] = self.test_grist_st_area()
        print()
        
        # Test 4: Correction des formules existantes
        results['existing_fixed'] = self.fix_existing_formulas()
        print()
        
        # Rapport final
        self.generate_report(results)
        return results
    
    def generate_report(self, results):
        """Génère le rapport final"""
        print("=" * 60)
        print("📊 RAPPORT FINAL - SYNTAXE GRIST CORRECTE")
        print("=" * 60)
        
        total = len(results)
        passed = sum(results.values())
        score = (passed / total) * 100
        
        print(f"🎯 SCORE: {passed}/{total} ({score:.0f}%)")
        print()
        
        status_map = {
            'st_distance': 'grist.ST_DISTANCE()',
            'vector_sim': 'grist.VECTOR_SIMILARITY()', 
            'st_area': 'grist.ST_AREA()',
            'existing_fixed': 'Formules existantes corrigées'
        }
        
        for test, success in results.items():
            status = "✅" if success else "❌"
            name = status_map.get(test, test)
            print(f"   {status} {name}: {'RÉUSSI' if success else 'ÉCHEC'}")
        
        print()
        if score == 100:
            print("🎉 PARFAIT ! TOUTES LES EXTENSIONS FONCTIONNENT !")
            print("🚀 PHASE 2 COMPLÈTEMENT RÉUSSIE !")
            print("✅ Fonctions spatiales et vectorielles opérationnelles")
            print("✅ Syntaxe grist.FONCTION() validée")
        elif score >= 75:
            print("🎉 EXCELLENT ! Extensions majoritairement fonctionnelles")
            print("🚀 PHASE 2 QUASI-RÉUSSIE")
        elif score >= 50:
            print("✅ BON ! Intégration partielle réussie")
        else:
            print("❌ PROBLÈME - Extensions non fonctionnelles")
        
        print(f"\n📄 Document: {self.base_url}/o/docs/{self.doc_id[:8]}")

if __name__ == "__main__":
    tester = TestSyntaxeCorrecte()
    results = tester.run_tests()
    
    if results.get('st_distance', False) and results.get('vector_sim', False):
        sys.exit(0)
    else:
        sys.exit(1)
