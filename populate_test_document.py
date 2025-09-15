#!/usr/bin/env python3
"""
Script pour peupler le document de test avec des données spatiales et vectorielles
"""

import requests
import json
import time

class DocumentPopulator:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8888"
        self.api_key = "b1ef763bbf48590f5b55745f94e80d29548d3bd3"
        self.doc_id = "oUzyVYoKocruw9dNgphVm3"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        print("🏗️ PEUPLEMENT DU DOCUMENT DE TEST")
        print("=" * 50)
        print(f"📄 Document: {self.doc_id}")
        print(f"🔐 API Key: {self.api_key[:20]}...")
        print()
    
    def check_document_access(self):
        """Vérifier l'accès au document"""
        print("🔍 Vérification accès document...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}")
            
            if response.ok:
                doc_data = response.json()
                print(f"   ✅ Document accessible: {doc_data.get('name', 'Sans nom')}")
                return True
            else:
                print(f"   ❌ Erreur d'accès: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return False
    
    def list_tables(self):
        """Lister les tables existantes"""
        print("📋 Tables existantes...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/tables")
            
            if response.ok:
                tables_data = response.json()
                tables = tables_data.get('tables', [])
                
                print(f"   📊 Tables trouvées: {len(tables)}")
                for table in tables:
                    print(f"      📄 {table.get('id', 'N/A')}: {table.get('tableId', 'N/A')}")
                
                return tables
            else:
                print(f"   ❌ Erreur listage tables: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return []
    
    def create_test_columns(self, table_id="Table1"):
        """Créer les colonnes de test avec les types spatiaux"""
        print(f"🏗️ Création colonnes dans {table_id}...")
        
        columns_to_create = [
            {
                "id": "nom",
                "type": "Text",
                "label": "Nom du monument"
            },
            {
                "id": "position",
                "type": "Geometry",
                "label": "Position GPS"
            },
            {
                "id": "caractere_vect",
                "type": "Vector", 
                "label": "Caractéristiques vectorielles"
            },
            {
                "id": "distance_centre",
                "type": "Numeric",
                "label": "Distance au centre",
                "formula": "grist.ST_DISTANCE($position, 'POINT(2.3522 48.8566)', 'km')"
            },
            {
                "id": "similarite_ref",
                "type": "Numeric",
                "label": "Similarité référence",
                "formula": "grist.VECTOR_SIMILARITY($caractere_vect, [0.8, 0.2, 0.9, 0.1, 0.7], 'cosine')"
            }
        ]
        
        created_columns = []
        
        for col in columns_to_create:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/docs/{self.doc_id}/tables/{table_id}/columns",
                    json={"columns": [col]}
                )
                
                if response.ok:
                    print(f"   ✅ Colonne '{col['id']}' ({col['type']}) créée")
                    created_columns.append(col['id'])
                else:
                    print(f"   ❌ Échec colonne '{col['id']}': {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Exception colonne '{col['id']}': {e}")
        
        return created_columns
    
    def populate_test_data(self, table_id="Table1"):
        """Peupler avec des données de test réelles"""
        print(f"📊 Peuplement données dans {table_id}...")
        
        test_records = [
            {
                "nom": "Tour Eiffel",
                "position": "POINT(2.2945 48.8584)",
                "caractere_vect": "[0.9, 0.1, 0.8, 0.2, 0.95]"
            },
            {
                "nom": "Notre-Dame", 
                "position": "POINT(2.3522 48.8566)",
                "caractere_vect": "[0.8, 0.2, 0.9, 0.1, 0.85]"
            },
            {
                "nom": "Arc de Triomphe",
                "position": "POINT(2.2950 48.8738)", 
                "caractere_vect": "[0.7, 0.3, 0.8, 0.2, 0.75]"
            },
            {
                "nom": "Sacré-Cœur",
                "position": "POINT(2.3431 48.8867)",
                "caractere_vect": "[0.6, 0.4, 0.7, 0.3, 0.65]"
            },
            {
                "nom": "Louvre",
                "position": "POINT(2.3376 48.8606)",
                "caractere_vect": "[0.85, 0.15, 0.9, 0.1, 0.8]"
            }
        ]
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/tables/{table_id}/records",
                json={"records": [{"fields": record} for record in test_records]}
            )
            
            if response.ok:
                result = response.json()
                record_ids = result.get('records', [])
                print(f"   ✅ {len(record_ids)} enregistrements créés")
                return True
            else:
                print(f"   ❌ Échec peuplement: {response.status_code}")
                print(f"   Détails: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception peuplement: {e}")
            return False
    
    def verify_data(self, table_id="Table1"):
        """Vérifier les données créées"""
        print(f"🔍 Vérification données {table_id}...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/tables/{table_id}/records")
            
            if response.ok:
                data = response.json()
                records = data.get('records', [])
                
                print(f"   📊 Enregistrements: {len(records)}")
                
                for record in records[:3]:  # Afficher les 3 premiers
                    fields = record.get('fields', {})
                    nom = fields.get('nom', 'N/A')
                    position = fields.get('position', 'N/A')
                    distance = fields.get('distance_centre', 'N/A')
                    similarity = fields.get('similarite_ref', 'N/A')
                    
                    print(f"   📍 {nom}: {position}")
                    print(f"      Distance: {distance}, Similarité: {similarity}")
                
                return len(records)
            else:
                print(f"   ❌ Erreur vérification: {response.status_code}")
                return 0
                
        except Exception as e:
            print(f"   ❌ Exception vérification: {e}")
            return 0
    
    def run_population(self):
        """Exécuter le peuplement complet"""
        print("🚀 DÉMARRAGE PEUPLEMENT")
        print("-" * 40)
        
        # Vérification accès
        if not self.check_document_access():
            print("❌ Abandon - document non accessible")
            return False
        
        # Liste des tables
        tables = self.list_tables()
        if not tables:
            print("❌ Aucune table trouvée")
            return False
        
        table_id = tables[0].get('tableId', 'Table1')
        print(f"🎯 Utilisation table: {table_id}")
        print()
        
        # Création des colonnes
        created_columns = self.create_test_columns(table_id)
        if created_columns:
            print(f"✅ {len(created_columns)} colonnes créées")
            
            # Attendre un peu pour que les colonnes soient prêtes
            print("⏳ Attente stabilisation colonnes...")
            time.sleep(3)
        
        # Peuplement des données
        if self.populate_test_data(table_id):
            print("✅ Données de test ajoutées")
            
            # Attendre pour les formules
            print("⏳ Attente calcul formules...")
            time.sleep(5)
            
            # Vérification
            record_count = self.verify_data(table_id)
            
            if record_count >= 5:
                print("\n🎉 PEUPLEMENT RÉUSSI !")
                print(f"📊 {record_count} enregistrements avec données spatiales/vectorielles")
                print(f"🌐 Prêt pour tests: {self.base_url}")
                return True
            else:
                print("\n⚠️ Peuplement partiel")
                return False
        else:
            print("❌ Échec peuplement données")
            return False

if __name__ == "__main__":
    populator = DocumentPopulator()
    success = populator.run_population()
    
    if success:
        print("\n🧪 Le document est maintenant prêt pour les tests d'endpoints !")
        print("🚀 Exécutez: python test_endpoints_spatiaux.py")
    else:
        print("\n❌ Peuplement échoué - vérifiez les credentials et l'accès")
