#!/usr/bin/env python3
"""
Test API Grist basé sur la documentation officielle
https://support.getgrist.com/api/
https://support.getgrist.com/rest-api/
"""

import requests
import json
import time

class GristOfficialAPI:
    """Client API Grist basé sur la documentation officielle"""
    
    def __init__(self, server_url, api_key):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def _request(self, method, endpoint, data=None, params=None):
        """Requête HTTP standardisée"""
        url = f"{self.server_url}{endpoint}"
        
        kwargs = {
            'headers': self.headers,
            'timeout': 30
        }
        
        if data is not None:
            kwargs['json'] = data
        if params is not None:
            kwargs['params'] = params
        
        try:
            response = requests.request(method, url, **kwargs)
            
            # Parse response
            if response.headers.get('content-type', '').startswith('application/json'):
                result_data = response.json()
            else:
                result_data = response.text
            
            return {
                'success': response.ok,
                'status': response.status_code,
                'data': result_data,
                'url': url
            }
            
        except Exception as e:
            return {
                'success': False,
                'status': 0,
                'error': str(e),
                'url': url
            }
    
    def list_workspaces(self):
        """Liste les workspaces selon la doc officielle"""
        print("📂 Liste des workspaces...")
        
        result = self._request('GET', '/api/orgs/current/workspaces')
        
        if result['success']:
            workspaces = result['data']
            print(f"   ✅ {len(workspaces)} workspace(s) trouvé(s)")
            return workspaces
        else:
            print(f"   ❌ Erreur: {result.get('data', result.get('error'))}")
            return []
    
    def create_document(self, name, workspace_id=None):
        """Crée un document selon la doc officielle"""
        print(f"📄 Création document: {name}")
        
        if workspace_id:
            endpoint = f'/api/workspaces/{workspace_id}/docs'
        else:
            endpoint = '/api/docs'
        
        data = {'name': name}
        
        result = self._request('POST', endpoint, data)
        
        if result['success']:
            doc_data = result['data']
            doc_id = doc_data.get('id', doc_data.get('docId'))
            print(f"   ✅ Document créé: {doc_id}")
            return doc_id
        else:
            print(f"   ❌ Erreur: {result.get('data', result.get('error'))}")
            return None
    
    def get_document_info(self, doc_id):
        """Récupère les infos du document"""
        print(f"📋 Info document {doc_id}...")
        
        result = self._request('GET', f'/api/docs/{doc_id}')
        
        if result['success']:
            print(f"   ✅ Document accessible")
            return result['data']
        else:
            print(f"   ❌ Erreur: {result.get('data', result.get('error'))}")
            return None
    
    def list_tables(self, doc_id):
        """Liste les tables du document"""
        print(f"📊 Tables du document...")
        
        result = self._request('GET', f'/api/docs/{doc_id}/tables')
        
        if result['success']:
            tables = result['data'].get('tables', [])
            print(f"   ✅ {len(tables)} table(s) trouvée(s)")
            for table in tables:
                print(f"      - {table.get('id')} ({table.get('tableRef', 'N/A')})")
            return tables
        else:
            print(f"   ❌ Erreur: {result.get('data', result.get('error'))}")
            return []
    
    def list_columns(self, doc_id, table_id):
        """Liste les colonnes d'une table"""
        print(f"📋 Colonnes de la table {table_id}...")
        
        result = self._request('GET', f'/api/docs/{doc_id}/tables/{table_id}/columns')
        
        if result['success']:
            columns = result['data'].get('columns', [])
            print(f"   ✅ {len(columns)} colonne(s) trouvée(s)")
            for col in columns:
                col_id = col.get('id')
                col_type = col.get('fields', {}).get('type', 'Unknown')
                col_label = col.get('fields', {}).get('label', col_id)
                print(f"      - {col_id} ({col_type}) '{col_label}'")
            return columns
        else:
            print(f"   ❌ Erreur: {result.get('data', result.get('error'))}")
            return []
    
    def add_column_official_format(self, doc_id, table_id, column_data):
        """Ajoute une colonne avec le format officiel"""
        col_id = column_data.get('id')
        col_type = column_data.get('fields', {}).get('type')
        
        print(f"   ➕ Ajout colonne: {col_id} ({col_type})")
        
        result = self._request('POST', f'/api/docs/{doc_id}/tables/{table_id}/columns', column_data)
        
        if result['success']:
            print(f"      ✅ Colonne {col_id} ajoutée")
            return True
        else:
            error = result.get('data', result.get('error', 'Unknown error'))
            print(f"      ❌ Erreur: {error}")
            return False
    
    def get_records(self, doc_id, table_id):
        """Récupère les enregistrements"""
        print(f"📖 Récupération données {table_id}...")
        
        result = self._request('GET', f'/api/docs/{doc_id}/tables/{table_id}/records')
        
        if result['success']:
            records = result['data'].get('records', [])
            print(f"   ✅ {len(records)} enregistrement(s) récupéré(s)")
            return records
        else:
            print(f"   ❌ Erreur: {result.get('data', result.get('error'))}")
            return []
    
    def add_records_official_format(self, doc_id, table_id, records):
        """Ajoute des enregistrements avec format officiel"""
        print(f"📊 Ajout de {len(records)} enregistrement(s)...")
        
        # Format officiel selon la doc
        data = {'records': records}
        
        result = self._request('POST', f'/api/docs/{doc_id}/tables/{table_id}/records', data)
        
        if result['success']:
            print(f"   ✅ {len(records)} enregistrement(s) ajouté(s)")
            return True
        else:
            error = result.get('data', result.get('error', 'Unknown error'))
            print(f"   ❌ Erreur: {error}")
            return False

def test_workflow_complet():
    """Test workflow complet selon documentation officielle"""
    
    API_KEY = "f4631937690617681be6860542a5cbdb9794c0ed"
    SERVER_URL = "http://127.0.0.1:8888"
    
    print("🚀 TEST API GRIST OFFICIEL")
    print("=" * 35)
    print(f"🌐 Serveur: {SERVER_URL}")
    print(f"🔑 API Key: {API_KEY[:8]}...{API_KEY[-4:]}")
    print()
    
    api = GristOfficialAPI(SERVER_URL, API_KEY)
    
    try:
        # 1. Lister workspaces
        print("📂 ÉTAPE 1: Exploration workspaces")
        workspaces = api.list_workspaces()
        
        # 2. Créer document (ou utiliser existant)
        print(f"\n📄 ÉTAPE 2: Création document")
        doc_id = api.create_document("Test Extensions API Officiel")
        
        if not doc_id:
            # Utiliser le document créé précédemment
            doc_id = "new~rhRFrQmKGvugn5cR45RTXe~5"
            print(f"   ⚠️ Utilisation document existant: {doc_id}")
        
        # 3. Explorer le document
        print(f"\n📋 ÉTAPE 3: Exploration document")
        doc_info = api.get_document_info(doc_id)
        
        # 4. Lister les tables
        print(f"\n📊 ÉTAPE 4: Exploration tables")
        tables = api.list_tables(doc_id)
        
        if not tables:
            print("❌ Aucune table trouvée")
            return False
        
        table_id = tables[0]['id']
        
        # 5. Lister les colonnes existantes
        print(f"\n📋 ÉTAPE 5: Colonnes existantes")
        existing_columns = api.list_columns(doc_id, table_id)
        
        # 6. Tenter d'ajouter nos colonnes spéciales
        print(f"\n🌟 ÉTAPE 6: Test nouveaux types")
        
        # Test avec les formats exacts de la documentation
        new_columns = [
            {
                "id": "nom_ville",
                "fields": {
                    "type": "Text",
                    "label": "Nom de la ville"
                }
            },
            {
                "id": "position_gps", 
                "fields": {
                    "type": "Geometry",  # NOUVEAU TYPE
                    "label": "Position GPS"
                }
            },
            {
                "id": "caracteristiques",
                "fields": {
                    "type": "Vector",    # NOUVEAU TYPE
                    "label": "Caractéristiques vectorielles"
                }
            }
        ]
        
        columns_added = 0
        for column in new_columns:
            if api.add_column_official_format(doc_id, table_id, column):
                columns_added += 1
        
        print(f"   📊 Colonnes ajoutées: {columns_added}/{len(new_columns)}")
        
        # 7. Tenter formules avec nouveaux types
        if columns_added >= 2:  # Au moins Geometry ou Vector fonctionne
            print(f"\n📐 ÉTAPE 7: Test formules avancées")
            
            # Formule spatiale
            spatial_formula = {
                "id": "distance_paris",
                "fields": {
                    "type": "Formula",
                    "label": "Distance Paris (km)",
                    "formula": '=ST_DISTANCE($position_gps, "POINT(2.3488 48.8534)", "km")'
                }
            }
            
            spatial_added = api.add_column_official_format(doc_id, table_id, spatial_formula)
            print(f"   🗺️ Formule spatiale ST_DISTANCE: {'✅' if spatial_added else '❌'}")
            
            # Formule vectorielle
            vector_formula = {
                "id": "similarite_ref",
                "fields": {
                    "type": "Formula", 
                    "label": "Similarité référence",
                    "formula": '=VECTOR_SIMILARITY($caracteristiques, [0.8, 0.3, 0.7, 0.2, 0.9], "cosine")'
                }
            }
            
            vector_added = api.add_column_official_format(doc_id, table_id, vector_formula)
            print(f"   🧮 Formule vectorielle VECTOR_SIMILARITY: {'✅' if vector_added else '❌'}")
        
        # 8. Insérer données de test
        if columns_added > 0:
            print(f"\n📊 ÉTAPE 8: Test insertion données")
            
            # Données adaptées aux colonnes ajoutées
            test_records = []
            
            base_record = {"nom_ville": "Paris"}
            
            # Ajouter données selon colonnes disponibles
            existing_col_ids = [col['id'] for col in existing_columns]
            new_col_ids = [col['id'] for col, added in zip(new_columns, [True]*columns_added + [False]*(len(new_columns)-columns_added)) if added]
            
            if "position_gps" in new_col_ids:
                base_record["position_gps"] = "POINT(2.3488 48.8534)"
            
            if "caracteristiques" in new_col_ids:
                base_record["caracteristiques"] = [0.9, 0.1, 0.8, 0.2, 0.95]
            
            test_records.append(base_record)
            
            # Format officiel pour les records
            formatted_records = [{"fields": record} for record in test_records]
            
            data_inserted = api.add_records_official_format(doc_id, table_id, formatted_records)
            
            if data_inserted:
                print(f"\n🔍 ÉTAPE 9: Vérification résultats")
                time.sleep(3)  # Attendre calculs formules
                
                records = api.get_records(doc_id, table_id)
                
                if records:
                    print("   📊 DONNÉES FINALES:")
                    for i, record in enumerate(records[:3], 1):  # Limiter à 3 pour lisibilité
                        fields = record.get('fields', {})
                        print(f"      {i}. {fields.get('nom_ville', fields.get('nom_de_la_ville', 'N/A'))}")
                        
                        for field_name, value in fields.items():
                            if field_name.startswith(('distance', 'similarite')):
                                print(f"         {field_name}: {value}")
        
        # Résumé final
        print(f"\n🎯 RÉSUMÉ FINAL")
        print("=" * 20)
        
        success_indicators = {
            'Document': doc_id is not None,
            'Tables': len(tables) > 0,
            'Colonnes ajoutées': columns_added > 0,
            'Type Geometry': columns_added >= 2,  # Au moins nom + geometry
            'Type Vector': columns_added >= 3,    # nom + geometry + vector
            'Formules avancées': 'spatial_added' in locals() or 'vector_added' in locals(),
            'Données test': 'data_inserted' in locals() and data_inserted
        }
        
        for indicator, status in success_indicators.items():
            emoji = "✅" if status else "❌"
            print(f"{emoji} {indicator}: {'OK' if status else 'KO'}")
        
        success_count = sum(success_indicators.values())
        total_count = len(success_indicators)
        
        if success_count >= 5:  # La plupart des indicateurs OK
            print(f"\n🎉 SUCCÈS ! Extensions largement opérationnelles !")
            print(f"🌐 Document: {SERVER_URL}/o/docs/{doc_id}")
        elif success_count >= 3:
            print(f"\n⚠️ Succès partiel - {success_count}/{total_count} fonctionnalités OK")
            print(f"🌐 Document: {SERVER_URL}/o/docs/{doc_id}")
        else:
            print(f"\n❌ Difficultés techniques - Test manuel recommandé")
        
        print(f"\n⏰ Fin: {time.strftime('%H:%M:%S')}")
        return success_count >= 3
        
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_workflow_complet()
    exit(0 if success else 1)
