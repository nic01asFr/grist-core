#!/usr/bin/env python3
"""
Test direct des fonctions spatiales/vectorielles via API Grist
Document: nEr4gKyXWpVbKj6W7RgS4Z (Test Extensions Spatiales COMPLET)
"""

import requests
import json
import time
import sys

class TestFonctionsDirectes:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8888"
        self.api_key = "3816d9d8e74c8bfd9abd3384b1019dc48d5605b5"
        self.doc_id = "nEr4gKyXWpVbKj6W7RgS4Z"  # Document créé précédemment
        self.table_id = "Table1"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        print("🔬 TEST DIRECT DES FONCTIONS SPATIALES/VECTORIELLES")
        print("=" * 60)
        print(f"📄 Document: {self.doc_id}")
        print(f"🌐 Base URL: {self.base_url}")
        print()
    
    def test_api_connectivity(self):
        """Test la connectivité de base à l'API"""
        print("🔌 Test connectivité API...")
        
        try:
            # Test accès au document
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}")
            if response.ok:
                doc_info = response.json()
                print(f"   ✅ Document accessible: {doc_info.get('name', 'N/A')}")
                return True
            else:
                print(f"   ❌ Erreur accès document: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Exception connectivité: {e}")
            return False
    
    def get_current_data(self):
        """Récupère les données actuelles du document"""
        print("📊 Récupération des données...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/records")
            
            if response.ok:
                data = response.json()
                records = data.get('records', [])
                print(f"   📋 {len(records)} enregistrements trouvés")
                
                for i, record in enumerate(records[:3], 1):
                    fields = record.get('fields', {})
                    lieu = fields.get('lieu', f'Record {i}')
                    position = fields.get('position', 'N/A')
                    distance = fields.get('distance_paris', 'N/A')
                    similarite = fields.get('similarite_test', 'N/A')
                    
                    print(f"   {i}. {lieu}:")
                    print(f"      Position: {position}")
                    print(f"      Distance: {distance}")
                    print(f"      Similarité: {similarite}")
                
                return records
            else:
                print(f"   ❌ Erreur récupération: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"   ❌ Exception récupération: {e}")
            return []
    
    def test_sql_queries_direct(self):
        """Test les requêtes SQL directes"""
        print("🗂️ Test requêtes SQL directes...")
        
        queries = [
            {
                "name": "Données de base",
                "sql": f"SELECT lieu, position, caracteristiques FROM {self.table_id} LIMIT 3",
                "expected": "Récupération des données stockées"
            },
            {
                "name": "Test ST_DISTANCE",
                "sql": f"SELECT lieu, ST_DISTANCE(position, 'POINT(2.3522 48.8566)', 'km') as distance FROM {self.table_id} WHERE lieu = 'Tour Eiffel'",
                "expected": "~4.5 km"
            },
            {
                "name": "Test VECTOR_SIMILARITY",
                "sql": f"SELECT lieu, VECTOR_SIMILARITY(caracteristiques, '[0.8, 0.2, 0.5]', 'cosine') as sim FROM {self.table_id} WHERE lieu = 'Notre-Dame de Paris'",
                "expected": ">0.8"
            },
            {
                "name": "Test ST_AREA (si applicable)",
                "sql": f"SELECT lieu, ST_AREA('POLYGON((2.29 48.85, 2.30 48.85, 2.30 48.86, 2.29 48.86, 2.29 48.85))', 'm2') as aire FROM {self.table_id} LIMIT 1",
                "expected": "Surface en m²"
            }
        ]
        
        results = {}
        
        for query in queries:
            print(f"\n   🔍 {query['name']}:")
            print(f"      SQL: {query['sql']}")
            
            try:
                response = self.session.post(
                    f"{self.base_url}/api/docs/{self.doc_id}/sql",
                    json={"sql": query["sql"]}
                )
                
                if response.ok:
                    result = response.json()
                    records = result.get('records', [])
                    
                    if records:
                        print(f"      ✅ Résultat: {len(records)} ligne(s)")
                        for j, record in enumerate(records[:2], 1):
                            print(f"         {j}. {record}")
                        results[query['name']] = {'success': True, 'data': records}
                    else:
                        print(f"      ⚠️ Aucun résultat")
                        results[query['name']] = {'success': True, 'data': []}
                else:
                    error_msg = response.text
                    print(f"      ❌ Erreur: {response.status_code}")
                    print(f"         {error_msg}")
                    results[query['name']] = {'success': False, 'error': error_msg}
                    
            except Exception as e:
                print(f"      ❌ Exception: {e}")
                results[query['name']] = {'success': False, 'error': str(e)}
        
        return results
    
    def test_formula_updates(self):
        """Test la mise à jour des formules"""
        print("🔄 Test mise à jour des formules...")
        
        try:
            # Forcer le recalcul en modifiant un enregistrement
            update_payload = {
                "records": [
                    {
                        "id": 1,
                        "fields": {
                            "lieu": "Tour Eiffel (MAJ)"
                        }
                    }
                ]
            }
            
            response = self.session.patch(
                f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/records",
                json=update_payload
            )
            
            if response.ok:
                print("   ✅ Enregistrement mis à jour")
                
                # Attendre et revérifier
                print("   ⏳ Attente recalcul (5 secondes)...")
                time.sleep(5)
                
                # Récupérer les nouvelles valeurs
                response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/records/1")
                if response.ok:
                    record = response.json()
                    fields = record.get('fields', {})
                    distance = fields.get('distance_paris')
                    similarite = fields.get('similarite_test')
                    
                    print(f"   📊 Résultats après MAJ:")
                    print(f"      Distance: {distance}")
                    print(f"      Similarité: {similarite}")
                    
                    if distance is not None and distance != '':
                        print("   🎉 FORMULES ACTIVES !")
                        return True
                    else:
                        print("   ⚠️ Formules toujours inactives")
                        return False
                else:
                    print(f"   ❌ Erreur récupération: {response.status_code}")
                    return False
            else:
                print(f"   ❌ Erreur mise à jour: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception MAJ: {e}")
            return False
    
    def test_manual_calculation(self):
        """Test calcul manuel des fonctions"""
        print("🧮 Test calcul manuel des fonctions...")
        
        # Test avec les données que nous connaissons
        test_cases = [
            {
                "name": "Distance Tour Eiffel - Notre-Dame",
                "point1": "POINT(2.2945 48.8584)",
                "point2": "POINT(2.3522 48.8566)",
                "expected_km": "~4.5"
            },
            {
                "name": "Similarité vecteur identique",
                "vector1": "[0.8, 0.2, 0.7, 0.85, 0.3]",
                "vector2": "[0.8, 0.2, 0.7, 0.85, 0.3]",
                "expected": "1.0"
            }
        ]
        
        print("   📋 Cas de test théoriques:")
        for case in test_cases:
            print(f"      • {case['name']}: {case.get('expected_km', case.get('expected'))}")
        
        # Test si on peut exécuter les fonctions directement via l'API
        try:
            # Tentative d'exécution via une colonne temporaire
            temp_formula = 'ST_DISTANCE("POINT(2.2945 48.8584)", "POINT(2.3522 48.8566)", "km")'
            
            create_col_response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns",
                json={
                    "id": "test_temp",
                    "fields": {
                        "type": "Formula",
                        "label": "Test Temporaire",
                        "formula": temp_formula
                    }
                }
            )
            
            if create_col_response.ok:
                print("   ✅ Colonne temporaire créée")
                
                # Attendre calcul
                time.sleep(3)
                
                # Récupérer résultat
                records = self.get_current_data()
                if records:
                    test_result = records[0].get('fields', {}).get('test_temp')
                    print(f"   🎯 Résultat test: {test_result}")
                
                # Supprimer colonne temporaire
                delete_response = self.session.delete(
                    f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns/test_temp"
                )
                if delete_response.ok:
                    print("   🗑️ Colonne temporaire supprimée")
                
                return test_result is not None and test_result != ''
            else:
                print(f"   ❌ Erreur création colonne: {create_col_response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception test manuel: {e}")
            return False
    
    def run_complete_test(self):
        """Exécute la suite complète de tests"""
        print("🚀 DÉBUT DU TEST COMPLET")
        print()
        
        results = {
            'connectivity': False,
            'data_retrieval': False,
            'sql_queries': {},
            'formula_updates': False,
            'manual_calculation': False
        }
        
        # 1. Test connectivité
        results['connectivity'] = self.test_api_connectivity()
        if not results['connectivity']:
            print("❌ ÉCHEC - Connectivité API")
            return results
        
        print()
        
        # 2. Récupération données
        data = self.get_current_data()
        results['data_retrieval'] = len(data) > 0
        
        print()
        
        # 3. Test requêtes SQL
        results['sql_queries'] = self.test_sql_queries_direct()
        
        print()
        
        # 4. Test mise à jour formules
        results['formula_updates'] = self.test_formula_updates()
        
        print()
        
        # 5. Test calcul manuel
        results['manual_calculation'] = self.test_manual_calculation()
        
        # 6. Rapport final
        self.generate_final_report(results)
        
        return results
    
    def generate_final_report(self, results):
        """Génère le rapport final des tests"""
        print("\n" + "=" * 60)
        print("📊 RAPPORT FINAL - TEST FONCTIONS DIRECTES")
        print("=" * 60)
        
        # Score de réussite
        total_tests = 5
        passed_tests = sum([
            results['connectivity'],
            results['data_retrieval'],
            any(q.get('success', False) for q in results['sql_queries'].values()),
            results['formula_updates'],
            results['manual_calculation']
        ])
        
        score_pct = (passed_tests / total_tests) * 100
        
        print(f"🎯 SCORE GLOBAL: {passed_tests}/{total_tests} ({score_pct:.0f}%)")
        print()
        
        print("📋 Détail des résultats:")
        print(f"   {'✅' if results['connectivity'] else '❌'} Connectivité API")
        print(f"   {'✅' if results['data_retrieval'] else '❌'} Récupération données")
        
        # Détail SQL
        sql_success = any(q.get('success', False) for q in results['sql_queries'].values())
        print(f"   {'✅' if sql_success else '❌'} Requêtes SQL de base")
        
        for name, result in results['sql_queries'].items():
            status = '✅' if result.get('success', False) else '❌'
            print(f"      {status} {name}")
        
        print(f"   {'✅' if results['formula_updates'] else '❌'} Mise à jour formules")
        print(f"   {'✅' if results['manual_calculation'] else '❌'} Calcul manuel")
        
        print()
        print("🎯 CONCLUSION:")
        if score_pct >= 80:
            print("🎉 EXCELLENT - Fonctions majoritairement opérationnelles")
        elif score_pct >= 60:
            print("✅ BON - Intégration partielle réussie")
        elif score_pct >= 40:
            print("⚠️ MOYEN - Problèmes d'exécution des formules")
        else:
            print("❌ ÉCHEC - Problèmes majeurs d'intégration")
        
        print(f"\n📄 Document de test: {self.base_url}/o/docs/{self.doc_id[:8]}")

if __name__ == "__main__":
    tester = TestFonctionsDirectes()
    results = tester.run_complete_test()
    
    # Code de sortie basé sur les résultats
    if results['connectivity'] and results['data_retrieval']:
        sys.exit(0)  # Succès de base
    else:
        sys.exit(1)  # Échec
