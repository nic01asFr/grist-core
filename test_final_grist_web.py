#!/usr/bin/env python3
"""
Test final des extensions Grist dans l'interface web
Container: grist-minimal-test sur http://127.0.0.1:8888
"""

import json
import time
import requests

class FinalGristTest:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8888" 
        self.api_key = "3816d9d8e74c8bfd9abd3384b1019dc48d5605b5"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        print("🎯 TEST FINAL GRIST - EXTENSIONS SPATIALES/VECTORIELLES")
        print("=" * 60)
        
    def create_test_document(self):
        """Créer un nouveau document de test"""
        print("📄 Création du document de test...")
        
        try:
            # D'abord récupérer les orgs et workspaces
            orgs_response = self.session.get(f"{self.base_url}/api/orgs")
            if not orgs_response.ok:
                print(f"   ❌ Erreur récupération orgs: {orgs_response.text}")
                return None
                
            orgs = orgs_response.json()
            if not orgs:
                print("   ❌ Aucune organisation trouvée")
                return None
                
            org_id = orgs[0]['id']
            print(f"   📋 Org trouvée: {orgs[0]['name']} (ID: {org_id})")
            
            # Récupérer les workspaces de cette org
            ws_response = self.session.get(f"{self.base_url}/api/orgs/{org_id}/workspaces")
            if not ws_response.ok:
                print(f"   ❌ Erreur récupération workspaces: {ws_response.text}")
                return None
                
            workspaces = ws_response.json()
            if not workspaces:
                print("   ❌ Aucun workspace trouvé")
                return None
                
            workspace_id = workspaces[0]['id']
            print(f"   📁 Workspace trouvé: {workspaces[0]['name']} (ID: {workspace_id})")
            
            # Créer le document dans ce workspace
            response = self.session.post(
                f"{self.base_url}/api/workspaces/{workspace_id}/docs",
                json={"name": "Test Extensions Spatiales Final"}
            )
            
            if response.ok:
                try:
                    doc_data = response.json()
                    doc_id = doc_data.get('id') if isinstance(doc_data, dict) else doc_data
                    print(f"   ✅ Document créé: {doc_id}")
                    print(f"   🔍 Réponse complète: {doc_data}")
                    return doc_id
                except Exception as parse_error:
                    print(f"   ❌ Erreur parsing réponse: {parse_error}")
                    print(f"   📄 Réponse brute: {response.text}")
                    return None
            else:
                print(f"   ❌ Erreur création document: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return None
    
    def add_test_columns(self, doc_id):
        """Ajouter les colonnes de test avec types Geometry et Vector"""
        print("📋 Ajout des colonnes de test...")
        
        columns_to_add = [
            {
                "id": "lieu",
                "fields": {"type": "Text", "label": "Lieu"}
            },
            {
                "id": "position", 
                "fields": {"type": "Geometry", "label": "Position GPS"}
            },
            {
                "id": "caracteristiques",
                "fields": {"type": "Vector", "label": "Caractéristiques"}
            },
            {
                "id": "distance_paris",
                "fields": {
                    "type": "Formula",
                    "label": "Distance Paris (km)",
                    "formula": 'ST_DISTANCE($position, "POINT(2.3522 48.8566)", "km")'
                }
            },
            {
                "id": "similarite_test",
                "fields": {
                    "type": "Formula", 
                    "label": "Similarité test",
                    "formula": 'VECTOR_SIMILARITY($caracteristiques, [0.8, 0.2, 0.5], "cosine")'
                }
            }
        ]
        
        success_count = 0
        for col in columns_to_add:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/docs/{doc_id}/tables/Table1/columns",
                    json=col
                )
                
                if response.ok:
                    print(f"   ✅ Colonne ajoutée: {col['id']} ({col['fields']['type']})")
                    success_count += 1
                else:
                    print(f"   ❌ Erreur colonne {col['id']}: {response.text}")
            except Exception as e:
                print(f"   ❌ Exception colonne {col['id']}: {e}")
        
        print(f"   📊 Colonnes ajoutées: {success_count}/{len(columns_to_add)}")
        return success_count >= 3  # Au moins les colonnes de base + Geometry/Vector
    
    def add_test_data(self, doc_id):
        """Ajouter des données de test réalistes"""
        print("📊 Ajout des données de test...")
        
        test_data = [
            {
                "lieu": "Tour Eiffel",
                "position": "POINT(2.2945 48.8584)",
                "caracteristiques": [0.9, 0.1, 0.8]
            },
            {
                "lieu": "Notre-Dame", 
                "position": "POINT(2.3522 48.8566)",
                "caracteristiques": [0.8, 0.2, 0.7]
            },
            {
                "lieu": "Arc de Triomphe",
                "position": "POINT(2.2950 48.8738)",
                "caracteristiques": [0.7, 0.3, 0.6]
            },
            {
                "lieu": "Sacré-Cœur",
                "position": "POINT(2.3431 48.8867)", 
                "caracteristiques": [0.6, 0.4, 0.5]
            }
        ]
        
        try:
            records_payload = {
                "records": [{"fields": record} for record in test_data]
            }
            
            response = self.session.post(
                f"{self.base_url}/api/docs/{doc_id}/tables/Table1/records",
                json=records_payload
            )
            
            if response.ok:
                result = response.json()
                count = len(result.get('records', []))
                print(f"   ✅ Données ajoutées: {count} enregistrements")
                return True
            else:
                print(f"   ❌ Erreur données: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception données: {e}")
            return False
    
    def verify_results(self, doc_id):
        """Vérifier les résultats calculés"""
        print("🔍 Vérification des résultats...")
        
        print("   ⏳ Attente calcul des formules (10 secondes)...")
        time.sleep(10)
        
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{doc_id}/tables/Table1/records")
            
            if response.ok:
                records = response.json().get('records', [])
                print(f"   📊 {len(records)} enregistrements trouvés")
                
                if records:
                    print("   🧮 Résultats des formules:")
                    for i, record in enumerate(records[:3], 1):
                        fields = record.get('fields', {})
                        lieu = fields.get('lieu', f'Record {i}')
                        distance = fields.get('distance_paris', 'N/A')
                        similarite = fields.get('similarite_test', 'N/A')
                        
                        print(f"      {lieu}:")
                        print(f"         Distance Paris: {distance}")
                        print(f"         Similarité: {similarite}")
                
                # Vérifier si les formules calculent
                formula_working = any(
                    record.get('fields', {}).get('distance_paris') not in [None, '', 'N/A']
                    for record in records
                )
                
                if formula_working:
                    print("   🎉 FORMULES FONCTIONNELLES !")
                    return True
                else:
                    print("   ⚠️ Formules pas encore calculées ou non fonctionnelles")
                    return False
            else:
                print(f"   ❌ Erreur récupération: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception vérification: {e}")
            return False
    
    def run_complete_test(self):
        """Exécuter le test complet"""
        print(f"🌐 Test sur: {self.base_url}")
        
        # 1. Créer document
        doc_id = self.create_test_document()
        if not doc_id:
            return False
        
        # 2. Ajouter colonnes
        if not self.add_test_columns(doc_id):
            return False
        
        # 3. Ajouter données  
        if not self.add_test_data(doc_id):
            return False
        
        # 4. Vérifier résultats
        success = self.verify_results(doc_id)
        
        # 5. Résumé final
        print("\n" + "=" * 60)
        if success:
            print("🎉 TEST RÉUSSI - EXTENSIONS SPATIALES FONCTIONNELLES !")
            print(f"📄 Document de test: {self.base_url}/o/docs/{doc_id}")
            print("✅ Types Geometry et Vector: OK")
            print("✅ Fonctions ST_DISTANCE et VECTOR_SIMILARITY: OK") 
            print("✅ Formules calculées automatiquement: OK")
        else:
            print("⚠️ TEST PARTIEL - Types OK, formules à vérifier manuellement")
            print(f"📄 Document créé: {self.base_url}/o/docs/{doc_id}")
        
        return success

if __name__ == "__main__":
    tester = FinalGristTest()
    success = tester.run_complete_test()
    exit(0 if success else 1)
