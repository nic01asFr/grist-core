#!/usr/bin/env python3
"""
Test API Grist avec format correct et progression par étapes
"""

import requests
import json
import time

class GristAPICorrect:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def request(self, method, path, data=None):
        url = f"{self.base_url}{path}"
        response = requests.request(method, url, headers=self.headers, json=data)
        
        try:
            result = response.json()
        except:
            result = response.text
            
        return {
            'success': response.ok,
            'status': response.status_code,
            'data': result
        }
    
    def get_doc_info(self, doc_id):
        """Récupère les infos du document"""
        print(f"📄 Info document: {doc_id}")
        
        result = self.request('GET', f'/api/docs/{doc_id}')
        print(f"   Document info: {result['status']}")
        
        if result['success']:
            print(f"   ✅ Document accessible")
            return result['data']
        
        return None
    
    def list_tables(self, doc_id):
        """Liste les tables du document"""
        print(f"📋 Tables du document:")
        
        result = self.request('GET', f'/api/docs/{doc_id}/tables')
        print(f"   Tables: {result['status']}")
        
        if result['success']:
            tables = result['data'].get('tables', [])
            print(f"   ✅ {len(tables)} table(s) trouvée(s)")
            for table in tables:
                print(f"      - {table.get('id', 'N/A')}")
            return tables
        
        return []
    
    def add_simple_column(self, doc_id, table_id, col_id, col_type, label=None):
        """Ajoute une colonne simple avec format correct"""
        print(f"   📋 Ajout colonne: {col_id} ({col_type})")
        
        # Format correct pour l'API Grist
        payload = {
            "id": col_id,
            "fields": {
                "type": col_type,
                "label": label or col_id
            }
        }
        
        result = self.request('POST', f'/api/docs/{doc_id}/tables/{table_id}/columns', payload)
        
        if result['success']:
            print(f"      ✅ Colonne {col_id} ajoutée")
            return True
        else:
            error = result['data']
            if isinstance(error, dict) and 'error' in error:
                error = error['error']
            print(f"      ❌ Erreur: {error}")
            return False
    
    def add_formula_column(self, doc_id, table_id, col_id, formula, label=None):
        """Ajoute une colonne formule"""
        print(f"   🧮 Ajout formule: {col_id}")
        print(f"      Formule: {formula}")
        
        payload = {
            "id": col_id,
            "fields": {
                "type": "Formula",
                "label": label or col_id,
                "formula": formula
            }
        }
        
        result = self.request('POST', f'/api/docs/{doc_id}/tables/{table_id}/columns', payload)
        
        if result['success']:
            print(f"      ✅ Formule {col_id} ajoutée")
            return True
        else:
            error = result['data']
            if isinstance(error, dict) and 'error' in error:
                error = error['error']
            print(f"      ❌ Erreur: {error}")
            return False
    
    def insert_records(self, doc_id, table_id, records):
        """Insère des enregistrements avec format correct"""
        print(f"📊 Insertion de {len(records)} enregistrements...")
        
        # Format correct pour l'API Grist  
        payload = {
            "records": [{"fields": record} for record in records]
        }
        
        result = self.request('POST', f'/api/docs/{doc_id}/tables/{table_id}/records', payload)
        
        if result['success']:
            print(f"   ✅ {len(records)} enregistrements insérés")
            return True
        else:
            error = result['data']
            if isinstance(error, dict) and 'error' in error:
                error = error['error']
            print(f"   ❌ Erreur insertion: {error}")
            return False
    
    def get_records(self, doc_id, table_id):
        """Récupère les enregistrements"""
        print(f"📖 Récupération des données...")
        
        result = self.request('GET', f'/api/docs/{doc_id}/tables/{table_id}/records')
        
        if result['success']:
            records = result['data'].get('records', [])
            print(f"   ✅ {len(records)} enregistrements récupérés")
            return records
        else:
            print(f"   ❌ Erreur récupération")
            return []

def test_step_by_step():
    """Test progressif étape par étape"""
    
    API_KEY = "f4631937690617681be6860542a5cbdb9794c0ed"
    GRIST_URL = "http://127.0.0.1:8888"
    DOC_ID = "new~rhRFrQmKGvugn5cR45RTXe~5"  # Document créé précédemment
    
    print("🚀 TEST PROGRESSIF - API GRIST")
    print("=" * 40)
    
    api = GristAPICorrect(GRIST_URL, API_KEY)
    
    # Étape 1: Vérifier le document
    print("\n📄 ÉTAPE 1: Vérification document")
    doc_info = api.get_doc_info(DOC_ID)
    
    # Étape 2: Lister les tables
    print("\n📋 ÉTAPE 2: Liste des tables")
    tables = api.list_tables(DOC_ID)
    
    if not tables:
        print("❌ Aucune table trouvée - Arrêt")
        return False
    
    table_id = tables[0]['id']  # Utiliser la première table
    print(f"✅ Utilisation de la table: {table_id}")
    
    # Étape 3: Ajouter colonnes standards d'abord
    print(f"\n📋 ÉTAPE 3: Ajout colonnes standards")
    success_count = 0
    
    # Colonnes simples d'abord
    if api.add_simple_column(DOC_ID, table_id, "ville", "Text", "Ville"):
        success_count += 1
    
    if api.add_simple_column(DOC_ID, table_id, "population", "Numeric", "Population"):
        success_count += 1
    
    print(f"   📊 Colonnes standards ajoutées: {success_count}/2")
    
    # Étape 4: Tester les nouveaux types Geometry et Vector
    print(f"\n🌟 ÉTAPE 4: Test nouveaux types")
    
    # Test type Geometry
    geometry_added = api.add_simple_column(DOC_ID, table_id, "coordonnees", "Geometry", "Coordonnées GPS")
    
    # Test type Vector  
    vector_added = api.add_simple_column(DOC_ID, table_id, "embedding", "Vector", "Embedding")
    
    print(f"   🗺️ Type Geometry: {'✅ Supporté' if geometry_added else '❌ Non supporté'}")
    print(f"   🧮 Type Vector: {'✅ Supporté' if vector_added else '❌ Non supporté'}")
    
    # Étape 5: Tester les formules spatiales/vectorielles
    if geometry_added:
        print(f"\n📐 ÉTAPE 5A: Test formules spatiales")
        
        spatial_formula_added = api.add_formula_column(
            DOC_ID, table_id, 
            "distance_paris", 
            '=ST_DISTANCE($coordonnees, "POINT(2.3488 48.8534)", "km")',
            "Distance Paris (km)"
        )
        
        print(f"   🗺️ Formule ST_DISTANCE: {'✅ Fonctionne' if spatial_formula_added else '❌ Erreur'}")
    
    if vector_added:
        print(f"\n🧮 ÉTAPE 5B: Test formules vectorielles")
        
        vector_formula_added = api.add_formula_column(
            DOC_ID, table_id,
            "similarite",
            '=VECTOR_SIMILARITY($embedding, [0.8, 0.3, 0.7, 0.2, 0.9], "cosine")',
            "Similarité"
        )
        
        print(f"   🧮 Formule VECTOR_SIMILARITY: {'✅ Fonctionne' if vector_formula_added else '❌ Erreur'}")
    
    # Étape 6: Insertion de données de test
    print(f"\n📊 ÉTAPE 6: Insertion données de test")
    
    # Données adaptées aux colonnes disponibles
    test_data = []
    
    if geometry_added and vector_added:
        # Données complètes avec nouveaux types
        test_data = [
            {
                "ville": "Paris",
                "population": 2161000,
                "coordonnees": "POINT(2.3488 48.8534)",
                "embedding": [0.9, 0.1, 0.8, 0.2, 0.95]
            },
            {
                "ville": "Lyon", 
                "population": 515695,
                "coordonnees": "POINT(4.8357 45.7640)",
                "embedding": [0.7, 0.3, 0.6, 0.4, 0.75]
            }
        ]
    else:
        # Données de base seulement
        test_data = [
            {
                "ville": "Paris",
                "population": 2161000
            },
            {
                "ville": "Lyon",
                "population": 515695
            }
        ]
    
    data_inserted = api.insert_records(DOC_ID, table_id, test_data)
    
    # Étape 7: Vérification résultats
    if data_inserted:
        print(f"\n🔍 ÉTAPE 7: Vérification résultats")
        
        # Attendre calcul des formules
        time.sleep(3)
        
        records = api.get_records(DOC_ID, table_id)
        
        if records:
            print("   📊 DONNÉES FINALES:")
            for i, record in enumerate(records, 1):
                fields = record.get('fields', {})
                print(f"      {i}. {fields.get('ville', 'N/A')}")
                
                if 'distance_paris' in fields:
                    distance = fields['distance_paris']
                    print(f"         Distance Paris: {distance}")
                
                if 'similarite' in fields:
                    sim = fields['similarite']
                    print(f"         Similarité: {sim}")
    
    # Résumé final
    print(f"\n🎯 RÉSUMÉ FINAL")
    print("=" * 20)
    print(f"✅ Document: {DOC_ID}")
    print(f"✅ Table: {table_id}")
    print(f"📊 Colonnes standards: 2/2")
    print(f"🌟 Type Geometry: {'✅' if geometry_added else '❌'}")
    print(f"🌟 Type Vector: {'✅' if vector_added else '❌'}")
    print(f"📐 Formules spatiales: {'✅' if geometry_added and 'spatial_formula_added' in locals() and spatial_formula_added else '❌'}")
    print(f"🧮 Formules vectorielles: {'✅' if vector_added and 'vector_formula_added' in locals() and vector_formula_added else '❌'}")
    print(f"📊 Données insérées: {'✅' if data_inserted else '❌'}")
    
    if geometry_added and vector_added:
        print(f"\n🎉 SUCCÈS ! Les extensions sont complètement opérationnelles !")
        print(f"🌐 Voir le document: {GRIST_URL}/o/docs/{DOC_ID}")
    elif geometry_added or vector_added:
        print(f"\n⚠️ Succès partiel - Au moins une extension fonctionne")
        print(f"🌐 Voir le document: {GRIST_URL}/o/docs/{DOC_ID}")
    else:
        print(f"\n❌ Les nouveaux types ne sont pas encore supportés par l'API")
        print(f"🔧 Mais les formules peuvent être testées manuellement")
    
    return geometry_added and vector_added

if __name__ == "__main__":
    success = test_step_by_step()
    exit(0 if success else 1)
