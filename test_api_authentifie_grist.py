#!/usr/bin/env python3
"""
Test complet authentifié des extensions Grist avec API Key
Création, population et validation automatique des fonctionnalités spatiales et vectorielles
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any, Optional

class GristAuthenticatedTester:
    """Testeur authentifié pour les extensions Grist"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8888", api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        print(f"🔑 API Key configurée: {api_key[:8]}...{api_key[-4:]}")
    
    def request(self, method: str, path: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Requête API avec authentification"""
        url = f"{self.base_url}{path}"
        
        try:
            kwargs = {}
            if data is not None:
                kwargs['json'] = data
            if params is not None:
                kwargs['params'] = params
                
            response = self.session.request(method, url, **kwargs)
            
            # Parse response
            try:
                result_data = response.json()
            except json.JSONDecodeError:
                result_data = response.text
            
            return {
                'success': response.ok,
                'status': response.status_code,
                'data': result_data,
                'url': url
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'status': 0,
                'error': str(e),
                'url': url
            }
    
    def list_workspaces_and_docs(self):
        """Liste les workspaces et documents disponibles"""
        print("📂 Découverte des workspaces et documents...")
        
        # Essayer plusieurs endpoints pour lister les documents
        endpoints = [
            '/api/orgs',
            '/api/orgs/docs',  
            '/api/docs',
            '/api/workspaces'
        ]
        
        for endpoint in endpoints:
            result = self.request('GET', endpoint)
            print(f"   {endpoint}: {result['status']} - {result.get('data', {}).keys() if isinstance(result.get('data'), dict) else 'Non-dict'}")
            
            if result['success']:
                data = result['data']
                if isinstance(data, list) and len(data) > 0:
                    print(f"      ✅ {len(data)} items trouvés")
                    return data
                elif isinstance(data, dict) and any(key in data for key in ['docs', 'workspaces', 'orgs']):
                    print(f"      ✅ Données structurées trouvées")
                    return data
        
        print("   ⚠️ Aucun endpoint de documents standard trouvé")
        return None
    
    def create_document(self, name: str, workspace_id: str = None) -> Optional[str]:
        """Crée un nouveau document"""
        print(f"📄 Création du document: {name}")
        
        # Essayer différentes méthodes de création
        creation_attempts = [
            # Méthode 1: Org docs
            {'endpoint': '/api/orgs/docs', 'data': {'name': name}},
            # Méthode 2: Workspace spécifique
            {'endpoint': f'/api/workspaces/{workspace_id}/docs' if workspace_id else '/api/docs', 'data': {'name': name}},
            # Méthode 3: Simple docs
            {'endpoint': '/api/docs', 'data': {'name': name}},
        ]
        
        for attempt in creation_attempts:
            if not attempt['endpoint']:
                continue
                
            result = self.request('POST', attempt['endpoint'], attempt['data'])
            print(f"   Tentative {attempt['endpoint']}: {result['status']}")
            
            if result['success']:
                doc_data = result['data']
                if isinstance(doc_data, dict):
                    doc_id = doc_data.get('id') or doc_data.get('docId')
                    if doc_id:
                        print(f"   ✅ Document créé: {doc_id}")
                        return doc_id
                elif isinstance(doc_data, str):
                    print(f"   ✅ Document créé: {doc_data}")
                    return doc_data
            else:
                error_msg = result.get('data', {})
                if isinstance(error_msg, dict):
                    error_msg = error_msg.get('error', str(error_msg))
                print(f"   ❌ Erreur: {error_msg}")
        
        print("   ❌ Échec création document")
        return None
    
    def add_columns_to_document(self, doc_id: str, table_id: str = 'Table1'):
        """Ajoute les colonnes de test au document"""
        print(f"📋 Ajout des colonnes au document {doc_id}")
        
        # Colonnes de test spatiales et vectorielles
        columns = [
            # Colonnes de base
            {
                "id": "nom_lieu",
                "fields": {
                    "label": "Nom du lieu",
                    "type": "Text"
                }
            },
            # Colonne Geometry - NOUVEAU TYPE
            {
                "id": "coordonnees_gps",
                "fields": {
                    "label": "Coordonnées GPS",
                    "type": "Geometry"
                }
            },
            # Colonne Vector - NOUVEAU TYPE  
            {
                "id": "caracteristiques_embedding",
                "fields": {
                    "label": "Embedding Caractéristiques",
                    "type": "Vector"
                }
            },
            # Formules spatiales - NOUVELLES FONCTIONS
            {
                "id": "distance_paris_km",
                "fields": {
                    "label": "Distance Paris (km)",
                    "type": "Formula",
                    "formula": '=ST_DISTANCE($coordonnees_gps, "POINT(2.3488 48.8534)", "km")'
                }
            },
            # Formules vectorielles - NOUVELLES FONCTIONS
            {
                "id": "similarite_reference",
                "fields": {
                    "label": "Similarité avec référence",
                    "type": "Formula", 
                    "formula": '=VECTOR_SIMILARITY($caracteristiques_embedding, [0.8, 0.3, 0.7, 0.2, 0.9], "cosine")'
                }
            },
            # Formule composite - COMBINAISON SPATIAL + VECTOR
            {
                "id": "score_pertinence",
                "fields": {
                    "label": "Score de pertinence",
                    "type": "Formula",
                    "formula": '=($similarite_reference * 0.7) + ((100 - $distance_paris_km) / 100 * 0.3)'
                }
            }
        ]
        
        success_count = 0
        
        for i, column in enumerate(columns, 1):
            print(f"   📋 Colonne {i}/{len(columns)}: {column['fields']['label']} ({column['fields']['type']})")
            
            result = self.request('POST', f'/api/docs/{doc_id}/tables/{table_id}/columns', column)
            
            if result['success']:
                print(f"      ✅ Ajoutée avec succès")
                success_count += 1
                
                # Afficher la formule si c'est une formule
                if column['fields']['type'] == 'Formula':
                    print(f"      🧮 Formule: {column['fields']['formula']}")
            else:
                error = result.get('data', {})
                if isinstance(error, dict):
                    error = error.get('error', str(error))
                print(f"      ❌ Erreur: {error}")
        
        print(f"   📊 Colonnes ajoutées: {success_count}/{len(columns)}")
        return success_count == len(columns)
    
    def populate_test_data(self, doc_id: str, table_id: str = 'Table1'):
        """Peuple le document avec des données de test"""
        print(f"📊 Population des données de test...")
        
        # Données de test réalistes
        test_records = [
            {
                "nom_lieu": "Tour Eiffel",
                "coordonnees_gps": "POINT(2.2945 48.8584)",
                "caracteristiques_embedding": [0.9, 0.1, 0.8, 0.2, 0.95]  # Monument parisien emblématique
            },
            {
                "nom_lieu": "Musée du Louvre", 
                "coordonnees_gps": "POINT(2.3380 48.8606)",
                "caracteristiques_embedding": [0.85, 0.25, 0.75, 0.15, 0.9]  # Musée culturel
            },
            {
                "nom_lieu": "Arc de Triomphe",
                "coordonnees_gps": "POINT(2.2950 48.8738)",
                "caracteristiques_embedding": [0.88, 0.22, 0.78, 0.18, 0.92]  # Monument historique
            },
            {
                "nom_lieu": "Opéra Bastille",
                "coordonnees_gps": "POINT(2.3697 48.8532)",
                "caracteristiques_embedding": [0.7, 0.4, 0.6, 0.3, 0.75]  # Culture moderne
            },
            {
                "nom_lieu": "Place de la République",
                "coordonnees_gps": "POINT(2.3665 48.8676)",
                "caracteristiques_embedding": [0.5, 0.6, 0.4, 0.5, 0.6]  # Espace public
            },
            {
                "nom_lieu": "Gare du Nord",
                "coordonnees_gps": "POINT(2.3550 48.8800)",
                "caracteristiques_embedding": [0.3, 0.8, 0.2, 0.7, 0.4]  # Infrastructure transport
            }
        ]
        
        print(f"   Insertion de {len(test_records)} enregistrements...")
        
        # Préparer données pour l'API
        api_records = [{"fields": record} for record in test_records]
        
        result = self.request('POST', f'/api/docs/{doc_id}/tables/{table_id}/records', {
            "records": api_records
        })
        
        if result['success']:
            inserted_data = result['data']
            if isinstance(inserted_data, dict) and 'records' in inserted_data:
                count = len(inserted_data['records'])
                print(f"   ✅ {count} enregistrements insérés avec succès")
                
                # Afficher aperçu des données
                print("   📋 Aperçu des données insérées:")
                for i, record in enumerate(test_records[:3], 1):
                    print(f"      {i}. {record['nom_lieu']}: {record['coordonnees_gps']}")
                if len(test_records) > 3:
                    print(f"      ... et {len(test_records)-3} autres")
                
                return True
            else:
                print(f"   ⚠️ Données insérées mais format inattendu: {type(inserted_data)}")
                return True
        else:
            error = result.get('data', {})
            if isinstance(error, dict):
                error = error.get('error', str(error))
            print(f"   ❌ Erreur insertion: {error}")
            return False
    
    def validate_formulas(self, doc_id: str, table_id: str = 'Table1'):
        """Valide que les formules fonctionnent correctement"""
        print(f"🧮 Validation des formules calculées...")
        
        # Attendre que les formules se calculent
        print("   ⏳ Attente calcul des formules (5 secondes)...")
        time.sleep(5)
        
        # Récupérer les données avec formules calculées
        result = self.request('GET', f'/api/docs/{doc_id}/tables/{table_id}/records')
        
        if result['success']:
            data = result['data']
            if isinstance(data, dict) and 'records' in data:
                records = data['records']
                print(f"   ✅ {len(records)} enregistrements récupérés")
                
                # Analyser les résultats
                print("\n   📊 RÉSULTATS DES FORMULES:")
                print("   " + "="*50)
                
                validation_results = []
                
                for i, record in enumerate(records, 1):
                    fields = record.get('fields', {})
                    nom = fields.get('nom_lieu', f'Ligne {i}')
                    
                    print(f"\n   🏛️ {nom}:")
                    
                    # Vérifier distance Paris
                    distance = fields.get('distance_paris_km')
                    if distance is not None:
                        distance_val = float(distance) if isinstance(distance, (int, float, str)) and str(distance).replace('.','').replace('-','').isdigit() else None
                        if distance_val is not None:
                            print(f"      📏 Distance Paris: {distance_val:.2f} km")
                            # Validation logique (Paris intra-muros = < 10km du centre)
                            if 0 <= distance_val <= 15:
                                validation_results.append(('Distance', True, f"{distance_val:.2f} km"))
                            else:
                                validation_results.append(('Distance', False, f"{distance_val:.2f} km (hors plage attendue)"))
                        else:
                            print(f"      ⚠️ Distance Paris: {distance} (non numérique)")
                            validation_results.append(('Distance', False, 'Non numérique'))
                    else:
                        print(f"      ❌ Distance Paris: Non calculée")
                        validation_results.append(('Distance', False, 'Non calculée'))
                    
                    # Vérifier similarité
                    similarite = fields.get('similarite_reference')
                    if similarite is not None:
                        sim_val = float(similarite) if isinstance(similarite, (int, float, str)) and str(similarite).replace('.','').replace('-','').isdigit() else None
                        if sim_val is not None:
                            print(f"      🧮 Similarité: {sim_val:.4f}")
                            # Validation plage cosinus [-1, 1]
                            if -1 <= sim_val <= 1:
                                validation_results.append(('Similarité', True, f"{sim_val:.4f}"))
                            else:
                                validation_results.append(('Similarité', False, f"{sim_val:.4f} (hors plage [-1,1])"))
                        else:
                            print(f"      ⚠️ Similarité: {similarite} (non numérique)")
                            validation_results.append(('Similarité', False, 'Non numérique'))
                    else:
                        print(f"      ❌ Similarité: Non calculée")
                        validation_results.append(('Similarité', False, 'Non calculée'))
                    
                    # Vérifier score composite
                    score = fields.get('score_pertinence')
                    if score is not None:
                        score_val = float(score) if isinstance(score, (int, float, str)) and str(score).replace('.','').replace('-','').isdigit() else None
                        if score_val is not None:
                            print(f"      🎯 Score pertinence: {score_val:.4f}")
                            validation_results.append(('Score', True, f"{score_val:.4f}"))
                        else:
                            print(f"      ⚠️ Score: {score} (non numérique)")
                            validation_results.append(('Score', False, 'Non numérique'))
                    else:
                        print(f"      ❌ Score: Non calculé")
                        validation_results.append(('Score', False, 'Non calculé'))
                
                # Résumé validation
                print(f"\n   📈 RÉSUMÉ VALIDATION:")
                print("   " + "="*30)
                
                success_by_type = {}
                for test_type, success, value in validation_results:
                    if test_type not in success_by_type:
                        success_by_type[test_type] = {'success': 0, 'total': 0}
                    success_by_type[test_type]['total'] += 1
                    if success:
                        success_by_type[test_type]['success'] += 1
                
                all_success = True
                for test_type, stats in success_by_type.items():
                    success_rate = stats['success'] / stats['total'] * 100
                    status = "✅" if success_rate == 100 else "⚠️" if success_rate >= 50 else "❌"
                    print(f"   {status} {test_type}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
                    if success_rate < 100:
                        all_success = False
                
                return all_success, len(records), validation_results
            else:
                print(f"   ❌ Format de données inattendu: {type(data)}")
                return False, 0, []
        else:
            error = result.get('data', {})
            if isinstance(error, dict):
                error = error.get('error', str(error))
            print(f"   ❌ Erreur récupération données: {error}")
            return False, 0, []

def main():
    """Test principal avec API authentifiée"""
    
    # Configuration
    API_KEY = "f4631937690617681be6860542a5cbdb9794c0ed"
    GRIST_URL = "http://127.0.0.1:8888"
    
    print("🚀 TEST AUTHENTIFIÉ COMPLET - EXTENSIONS GRIST")
    print("=" * 60)
    print(f"🌐 URL Grist: {GRIST_URL}")
    print(f"🔑 API Key: {API_KEY[:8]}...{API_KEY[-4:]}")
    print(f"⏰ Début: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = GristAuthenticatedTester(GRIST_URL, API_KEY)
    
    try:
        # Phase 1: Découverte
        print("🔍 PHASE 1: Découverte de l'environnement")
        print("-" * 40)
        workspace_data = tester.list_workspaces_and_docs()
        
        # Phase 2: Création document
        print("\n📄 PHASE 2: Création du document de test")
        print("-" * 40)
        doc_id = tester.create_document("Test Extensions Spatiales Vectorielles Auto")
        
        if not doc_id:
            print("❌ Impossible de créer un document - Arrêt du test")
            return False
        
        # Phase 3: Configuration colonnes
        print(f"\n📋 PHASE 3: Configuration des colonnes")
        print("-" * 40)
        columns_added = tester.add_columns_to_document(doc_id)
        
        if not columns_added:
            print("⚠️ Pas toutes les colonnes ajoutées - Continuation avec limitations")
        
        # Phase 4: Population données
        print(f"\n📊 PHASE 4: Population des données de test")
        print("-" * 40)
        data_inserted = tester.populate_test_data(doc_id)
        
        if not data_inserted:
            print("❌ Échec insertion données - Arrêt du test")
            return False
        
        # Phase 5: Validation formules  
        print(f"\n🧮 PHASE 5: Validation des formules")
        print("-" * 40)
        formulas_valid, record_count, validations = tester.validate_formulas(doc_id)
        
        # Résultats finaux
        print(f"\n🎯 RÉSULTATS FINAUX")
        print("=" * 25)
        
        print(f"✅ Document créé: {doc_id}")
        print(f"{'✅' if columns_added else '⚠️'} Colonnes configurées: {'Toutes' if columns_added else 'Partielles'}")
        print(f"{'✅' if data_inserted else '❌'} Données insérées: {'OK' if data_inserted else 'Échec'}")
        print(f"{'✅' if formulas_valid else '⚠️'} Formules validées: {'OK' if formulas_valid else 'Partielles'}")
        print(f"📊 Enregistrements testés: {record_count}")
        
        if formulas_valid and data_inserted and record_count > 0:
            print(f"\n🎉 SUCCÈS COMPLET ! EXTENSIONS PARFAITEMENT FONCTIONNELLES !")
            print("=" * 55)
            print("🌟 Les types Geometry et Vector sont opérationnels")
            print("🔧 Les formules ST_* et VECTOR_* fonctionnent")
            print("⚡ Les calculs se font automatiquement")
            print("🎯 L'intégration est réussie")
            print(f"🌐 Document accessible: {GRIST_URL}/o/docs/{doc_id}")
        else:
            print(f"\n⚠️ Test partiel - Vérification manuelle recommandée")
            print(f"🌐 Document: {GRIST_URL}/o/docs/{doc_id}")
        
        print(f"\n⏰ Fin: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        return formulas_valid and data_inserted
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
