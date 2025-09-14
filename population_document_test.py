#!/usr/bin/env python3
"""
Population automatique du document de test avec colonnes et données
pour valider les extensions spatiales et vectorielles
"""

import json
import time
import requests

class GristDocumentPopulator:
    """Population automatique du document de test"""
    
    def __init__(self, config_file='grist_test_config.json'):
        self.config = self.load_config(config_file)
        self.api_key = "f4631937690617681be6860542a5cbdb9794c0ed"
        
        if not self.config:
            raise Exception("Configuration non trouvée - Exécutez creation_document_test_final.py")
        
        self.base_url = self.config['base_url']
        self.doc_id = self.config['doc_id']
        self.table_id = self.config['table_id']
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        print(f"📊 Population du document: {self.doc_id}")
    
    def load_config(self, config_file):
        """Charge la configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
    
    def clear_existing_columns(self):
        """Nettoie les colonnes existantes (garde seulement les essentielles)"""
        print("🧹 Nettoyage des colonnes existantes...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns")
            
            if response.ok:
                columns = response.json().get('columns', [])
                
                # Garder seulement les colonnes système essentielles
                essential_columns = ['id']  # Colonne ID système
                
                for col in columns:
                    col_id = col.get('id')
                    if col_id not in essential_columns:
                        print(f"   🗑️ Suppression colonne: {col_id}")
                        try:
                            delete_response = self.session.delete(
                                f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns/{col_id}"
                            )
                            if delete_response.ok:
                                print(f"      ✅ Supprimée")
                            else:
                                print(f"      ⚠️ Erreur suppression: {delete_response.status_code}")
                        except:
                            print(f"      ⚠️ Ne peut pas supprimer {col_id}")
        except Exception as e:
            print(f"   ⚠️ Erreur nettoyage: {e}")
    
    def add_test_columns(self):
        """Ajoute toutes les colonnes de test nécessaires"""
        print("📋 Ajout des colonnes de test...")
        
        # Définition complète des colonnes de test
        test_columns = [
            # Colonnes de base
            {
                "id": "lieu",
                "fields": {
                    "type": "Text",
                    "label": "Lieu"
                }
            },
            {
                "id": "description", 
                "fields": {
                    "type": "Text",
                    "label": "Description"
                }
            },
            
            # Colonnes avec nouveaux types - CORE DU TEST
            {
                "id": "position",
                "fields": {
                    "type": "Geometry",
                    "label": "Position GPS"
                }
            },
            {
                "id": "caracteristiques",
                "fields": {
                    "type": "Vector", 
                    "label": "Caractéristiques (embedding)"
                }
            },
            
            # Colonnes formules spatiales - TEST DES NOUVELLES FONCTIONS
            {
                "id": "distance_notre_dame",
                "fields": {
                    "type": "Formula",
                    "label": "Distance Notre-Dame (km)",
                    "formula": 'ST_DISTANCE($position, "POINT(2.3522 48.8566)", "km")'
                }
            },
            {
                "id": "dans_paris_centre",
                "fields": {
                    "type": "Formula",
                    "label": "Dans Paris centre",
                    "formula": 'ST_CONTAINS("POLYGON((2.25 48.80, 2.45 48.80, 2.45 48.90, 2.25 48.90, 2.25 48.80))", $position)'
                }
            },
            
            # Colonnes formules vectorielles - TEST DES NOUVELLES FONCTIONS
            {
                "id": "similarite_monument", 
                "fields": {
                    "type": "Formula",
                    "label": "Similarité monument",
                    "formula": 'VECTOR_SIMILARITY($caracteristiques, [0.9, 0.1, 0.8, 0.2, 0.95], "cosine")'
                }
            },
            {
                "id": "similarite_culture",
                "fields": {
                    "type": "Formula", 
                    "label": "Similarité culture",
                    "formula": 'VECTOR_SIMILARITY($caracteristiques, [0.7, 0.3, 0.6, 0.4, 0.75], "cosine")'
                }
            },
            
            # Colonnes formules mixtes - TEST COMBINAISONS
            {
                "id": "score_touristique",
                "fields": {
                    "type": "Formula",
                    "label": "Score touristique", 
                    "formula": '($similarite_monument * 0.6) + ((5 - $distance_notre_dame) / 5 * 0.4)'
                }
            },
            {
                "id": "recommandation",
                "fields": {
                    "type": "Formula",
                    "label": "Recommandation",
                    "formula": 'IF($score_touristique > 0.7, "Recommandé", IF($score_touristique > 0.4, "Intéressant", "Pas prioritaire"))'
                }
            }
        ]
        
        success_count = 0
        failed_columns = []
        
        for col in test_columns:
            col_id = col['id']
            col_type = col['fields']['type']
            col_label = col['fields']['label']
            
            print(f"   📋 Ajout: {col_id} ({col_type}) - {col_label}")
            
            try:
                response = self.session.post(
                    f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns",
                    json=col
                )
                
                if response.ok:
                    print(f"      ✅ Ajoutée avec succès")
                    success_count += 1
                    
                    # Afficher la formule si applicable
                    if 'formula' in col['fields']:
                        formula = col['fields']['formula']
                        print(f"      🧮 Formule: {formula}")
                else:
                    error = response.text
                    print(f"      ❌ Erreur: {error}")
                    failed_columns.append({
                        'id': col_id,
                        'type': col_type,
                        'error': error
                    })
                    
            except Exception as e:
                print(f"      ❌ Exception: {e}")
                failed_columns.append({
                    'id': col_id,
                    'type': col_type, 
                    'error': str(e)
                })
        
        print(f"\n📊 Résumé ajout colonnes:")
        print(f"   ✅ Réussies: {success_count}/{len(test_columns)}")
        print(f"   ❌ Échouées: {len(failed_columns)}")
        
        if failed_columns:
            print("   🔍 Colonnes échouées:")
            for failed in failed_columns:
                print(f"      - {failed['id']} ({failed['type']}): {failed['error'][:50]}...")
        
        return success_count, failed_columns
    
    def add_test_data(self):
        """Ajoute les données de test réalistes"""
        print("📊 Ajout des données de test...")
        
        # Données de test réalistes pour Paris
        test_data = [
            {
                "lieu": "Notre-Dame de Paris",
                "description": "Cathédrale gothique emblématique sur l'île de la Cité",
                "position": "POINT(2.3522 48.8566)",
                "caracteristiques": [0.95, 0.05, 0.90, 0.10, 0.98]  # Monument historique majeur
            },
            {
                "lieu": "Tour Eiffel",
                "description": "Tour de fer emblématique, symbole de Paris",
                "position": "POINT(2.2945 48.8584)",
                "caracteristiques": [0.98, 0.02, 0.95, 0.05, 1.00]  # Monument le plus célèbre
            },
            {
                "lieu": "Musée du Louvre",
                "description": "Plus grand musée d'art et d'antiquités au monde",
                "position": "POINT(2.3380 48.8606)",
                "caracteristiques": [0.85, 0.15, 0.80, 0.20, 0.90]  # Culture et art
            },
            {
                "lieu": "Arc de Triomphe",
                "description": "Monument aux morts, Champs-Élysées",
                "position": "POINT(2.2950 48.8738)",
                "caracteristiques": [0.88, 0.12, 0.85, 0.15, 0.92]  # Monument historique
            },
            {
                "lieu": "Sacré-Cœur",
                "description": "Basilique sur la butte Montmartre",
                "position": "POINT(2.3431 48.8867)",
                "caracteristiques": [0.82, 0.18, 0.78, 0.22, 0.85]  # Monument religieux
            },
            {
                "lieu": "Centre Pompidou",
                "description": "Musée national d'art moderne",
                "position": "POINT(2.3522 48.8606)",
                "caracteristiques": [0.70, 0.30, 0.65, 0.35, 0.75]  # Culture moderne
            },
            {
                "lieu": "Panthéon",
                "description": "Mausolée des grandes personnalités françaises",
                "position": "POINT(2.3461 48.8462)",
                "caracteristiques": [0.80, 0.20, 0.75, 0.25, 0.83]  # Monument historique
            },
            {
                "lieu": "Opéra Garnier",
                "description": "Opéra national de Paris, architecture Second Empire",
                "position": "POINT(2.3317 48.8720)",
                "caracteristiques": [0.75, 0.25, 0.70, 0.30, 0.78]  # Culture et architecture
            },
            {
                "lieu": "Jardin du Luxembourg",
                "description": "Parc public du 6e arrondissement",
                "position": "POINT(2.3367 48.8462)",
                "caracteristiques": [0.40, 0.60, 0.35, 0.65, 0.45]  # Nature et détente
            },
            {
                "lieu": "Marché aux Puces",
                "description": "Plus grand marché d'antiquités au monde",
                "position": "POINT(2.4014 48.9014)",
                "caracteristiques": [0.30, 0.70, 0.25, 0.75, 0.35]  # Commerce populaire
            }
        ]
        
        print(f"   Préparation de {len(test_data)} enregistrements...")
        
        # Afficher aperçu des données
        print("   📋 Aperçu des données:")
        for i, data in enumerate(test_data[:3], 1):
            print(f"      {i}. {data['lieu']}: {data['position']}")
            embedding_preview = str(data['caracteristiques'][:3])[:-1] + "...]"
            print(f"         Embedding: {embedding_preview}")
        print(f"      ... et {len(test_data)-3} autres lieux")
        
        # Format requis par l'API Grist
        records_payload = {
            "records": [{"fields": record} for record in test_data]
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/records",
                json=records_payload
            )
            
            if response.ok:
                result = response.json()
                inserted_count = len(result.get('records', []))
                print(f"   ✅ {inserted_count} enregistrements ajoutés avec succès")
                return True, inserted_count
            else:
                error = response.text
                print(f"   ❌ Erreur insertion: {error}")
                return False, 0
                
        except Exception as e:
            print(f"   ❌ Exception insertion: {e}")
            return False, 0
    
    def wait_for_calculations(self):
        """Attend que les formules se calculent"""
        print("⏳ Attente des calculs de formules...")
        print("   (Les formules peuvent prendre quelques secondes à se calculer)")
        
        for i in range(10):
            print(f"   ⏱️ {i+1}/10 secondes...")
            time.sleep(1)
        
        print("   ✅ Attente terminée")
    
    def verify_results(self):
        """Vérifie que les données et formules ont bien été créées"""
        print("🔍 Vérification des résultats...")
        
        try:
            # Récupérer les données
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/records")
            
            if response.ok:
                records = response.json().get('records', [])
                print(f"   ✅ {len(records)} enregistrements trouvés")
                
                if records:
                    # Analyser le premier enregistrement
                    first_record = records[0]
                    fields = first_record.get('fields', {})
                    
                    print("   📊 Exemple de données (1er enregistrement):")
                    
                    for field_name, value in fields.items():
                        if field_name in ['lieu', 'position']:
                            print(f"      {field_name}: {value}")
                        elif field_name.startswith('distance'):
                            print(f"      {field_name}: {value} (doit être ~0-5 km)")
                        elif field_name.startswith('similarite'):
                            print(f"      {field_name}: {value} (doit être 0-1)")
                        elif field_name.startswith('score'):
                            print(f"      {field_name}: {value} (score composite)")
                        elif field_name == 'recommandation':
                            print(f"      {field_name}: {value}")
                
                # Compter les formules qui ont des valeurs
                calculated_formulas = 0
                total_formula_fields = 0
                
                for record in records[:3]:  # Vérifier les 3 premiers
                    fields = record.get('fields', {})
                    for field_name, value in fields.items():
                        if field_name.startswith(('distance', 'similarite', 'score', 'dans_', 'recommandation')):
                            total_formula_fields += 1
                            if value is not None and value != '':
                                calculated_formulas += 1
                
                if total_formula_fields > 0:
                    calc_rate = calculated_formulas / total_formula_fields * 100
                    print(f"   🧮 Formules calculées: {calculated_formulas}/{total_formula_fields} ({calc_rate:.1f}%)")
                    
                    if calc_rate >= 80:
                        print("   🎉 Excellent ! La plupart des formules fonctionnent")
                    elif calc_rate >= 50:
                        print("   ✅ Bon ! Plusieurs formules fonctionnent")
                    else:
                        print("   ⚠️ Peu de formules calculées - Vérification manuelle requise")
                
                return True, len(records)
            else:
                print(f"   ❌ Erreur récupération: {response.status_code}")
                return False, 0
                
        except Exception as e:
            print(f"   ❌ Erreur vérification: {e}")
            return False, 0

def main():
    """Population complète du document de test"""
    print("🚀 POPULATION AUTOMATIQUE DU DOCUMENT DE TEST")
    print("=" * 50)
    print(f"⏰ Début: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        populator = GristDocumentPopulator()
        
        # Étape 1: Nettoyer les colonnes existantes
        print(f"\n🧹 ÉTAPE 1: Nettoyage")
        populator.clear_existing_columns()
        
        # Étape 2: Ajouter colonnes de test
        print(f"\n📋 ÉTAPE 2: Ajout des colonnes")
        columns_success, failed_columns = populator.add_test_columns()
        
        # Étape 3: Ajouter données de test
        print(f"\n📊 ÉTAPE 3: Ajout des données")
        data_success, record_count = populator.add_test_data()
        
        if data_success:
            # Étape 4: Attendre calculs
            print(f"\n⏳ ÉTAPE 4: Calcul des formules")
            populator.wait_for_calculations()
            
            # Étape 5: Vérifier résultats
            print(f"\n🔍 ÉTAPE 5: Vérification")
            verify_success, final_count = populator.verify_results()
        else:
            verify_success = False
            final_count = 0
        
        # Résumé final
        print(f"\n🎯 RÉSUMÉ FINAL")
        print("=" * 25)
        print(f"✅ Colonnes ajoutées: {columns_success}/10")
        print(f"✅ Données insérées: {record_count} enregistrements")
        print(f"✅ Vérification: {'OK' if verify_success else 'KO'}")
        
        if len(failed_columns) > 0:
            print(f"\n⚠️ TYPES D'EXTENSIONS NON SUPPORTÉS:")
            geometry_failed = any(col['type'] == 'Geometry' for col in failed_columns)
            vector_failed = any(col['type'] == 'Vector' for col in failed_columns)
            
            if geometry_failed:
                print("   ❌ Type Geometry - Extensions spatiales non intégrées")
            if vector_failed:
                print("   ❌ Type Vector - Extensions vectorielles non intégrées")
        
        config = populator.config
        doc_url = f"{config['base_url']}/o/{config['org_id']}/{config['doc_id']}"
        
        if columns_success >= 5 and data_success:
            print(f"\n🎉 DOCUMENT POPULÉ AVEC SUCCÈS !")
            print(f"🌐 Testez maintenant: {doc_url}")
            print("📋 Vérifiez les types Geometry/Vector dans l'interface")
            print("🧮 Vérifiez les formules ST_*/VECTOR_* dans les colonnes")
        else:
            print(f"\n⚠️ Population partielle - Test manuel requis")
            print(f"🌐 Document: {doc_url}")
        
        print(f"\n⏰ Fin: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        return columns_success >= 5
        
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
