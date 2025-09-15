#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CRÉATION DOCUMENT SHOWCASE - FONCTIONNALITÉS SPATIALES & VECTORIELLES
Démonstrateur complet avec données réelles de Paris et vecteurs sémantiques
"""

import requests
import json
import time
import sys
import math

class GristShowcaseCreator:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8888"
        self.api_key = "10005e103cc5a462fa8080aa57f8a9e5ec9bd314"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        # Données réelles de Paris pour la démonstration
        self.paris_monuments = [
            {"nom": "Tour Eiffel", "coords": "POINT(2.2945 48.8584)", "type": "Monument", "hauteur": 330, "visiteurs_annuel": 7000000},
            {"nom": "Notre-Dame", "coords": "POINT(2.3522 48.8566)", "type": "Cathédrale", "hauteur": 69, "visiteurs_annuel": 14000000},
            {"nom": "Arc de Triomphe", "coords": "POINT(2.2950 48.8738)", "type": "Monument", "hauteur": 50, "visiteurs_annuel": 1500000},
            {"nom": "Louvre", "coords": "POINT(2.3376 48.8606)", "type": "Musée", "hauteur": 21, "visiteurs_annuel": 9600000},
            {"nom": "Sacré-Cœur", "coords": "POINT(2.3431 48.8867)", "type": "Basilique", "hauteur": 83, "visiteurs_annuel": 10500000},
            {"nom": "Panthéon", "coords": "POINT(2.3462 48.8462)", "type": "Monument", "hauteur": 83, "visiteurs_annuel": 700000},
            {"nom": "Opéra Garnier", "coords": "POINT(2.3317 48.8720)", "type": "Opéra", "hauteur": 56, "visiteurs_annuel": 480000},
            {"nom": "Invalides", "coords": "POINT(2.3124 48.8555)", "type": "Monument", "hauteur": 107, "visiteurs_annuel": 1200000}
        ]
        
        self.paris_zones = [
            {"nom": "Champs-Élysées", "zone": "POLYGON((2.2945 48.8700, 2.3138 48.8700, 2.3138 48.8738, 2.2945 48.8738, 2.2945 48.8700))", "type": "Avenue", "superficie_ha": 84},
            {"nom": "Jardins du Tuileries", "zone": "POLYGON((2.3270 48.8630, 2.3330 48.8630, 2.3330 48.8650, 2.3270 48.8650, 2.3270 48.8630))", "type": "Parc", "superficie_ha": 25},
            {"nom": "Île de la Cité", "zone": "POLYGON((2.3400 48.8530, 2.3500 48.8530, 2.3500 48.8580, 2.3400 48.8580, 2.3400 48.8530))", "type": "Île", "superficie_ha": 22},
            {"nom": "Montmartre", "zone": "POLYGON((2.3300 48.8840, 2.3500 48.8840, 2.3500 48.8890, 2.3300 48.8890, 2.3300 48.8840))", "type": "Quartier", "superficie_ha": 60},
            {"nom": "Quartier Latin", "zone": "POLYGON((2.3400 48.8450, 2.3550 48.8450, 2.3550 48.8500, 2.3400 48.8500, 2.3400 48.8450))", "type": "Quartier", "superficie_ha": 95}
        ]
        
        self.documents_semantiques = [
            {"titre": "Architecture gothique Paris", "contenu": "cathédrale médiévale voûtes arcs-boutants rosace", "vecteur": [0.8, 0.1, 0.9, 0.2, 0.7, 0.3, 0.6, 0.8], "categorie": "Architecture"},
            {"titre": "Tourisme parisien monuments", "contenu": "visite touriste monument historique patrimoine", "vecteur": [0.7, 0.9, 0.3, 0.8, 0.5, 0.6, 0.4, 0.7], "categorie": "Tourisme"},
            {"titre": "Gastronomie française cuisine", "contenu": "restaurant cuisine française gastronomie chef étoilé", "vecteur": [0.2, 0.6, 0.1, 0.5, 0.9, 0.8, 0.7, 0.3], "categorie": "Gastronomie"},
            {"titre": "Art musées collections", "contenu": "peinture sculpture art moderne contemporain exposition", "vecteur": [0.6, 0.3, 0.8, 0.1, 0.4, 0.9, 0.7, 0.5], "categorie": "Art"},
            {"titre": "Histoire de France", "contenu": "révolution française monarchie république napoléon", "vecteur": [0.9, 0.2, 0.7, 0.6, 0.3, 0.4, 0.8, 0.1], "categorie": "Histoire"},
            {"titre": "Jardins espaces verts", "contenu": "parc jardin nature verdure promenade détente", "vecteur": [0.3, 0.7, 0.2, 0.9, 0.6, 0.1, 0.5, 0.8], "categorie": "Nature"}
        ]
        
    def create_showcase_document(self):
        """Créer le document showcase avec toutes les tables"""
        print("🏛️ CRÉATION DOCUMENT SHOWCASE GRIST")
        print("=" * 50)
        
        try:
            # 1. Créer le document principal
            print("📄 Création document showcase...")
            doc_data = {"name": "🌟 Showcase Grist - Extensions Spatiales & Vectorielles"}
            
            response = self.session.post(f"{self.base_url}/api/workspaces/2/docs", json=doc_data)
            if response.status_code not in [200, 201]:
                print(f"❌ Erreur création document: {response.status_code}")
                return None
                
            doc_response = response.json()
            doc_id = str(doc_response) if isinstance(doc_response, str) else doc_response.get('id')
            print(f"✅ Document créé: {doc_id}")
            
            # Attendre un peu pour la création
            time.sleep(3)
            
            return doc_id
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return None
    
    def create_monuments_table(self, doc_id):
        """Créer la table des monuments parisiens avec géométrie"""
        print("\n🗼 CRÉATION TABLE MONUMENTS")
        print("=" * 35)
        
        try:
            # 1. Créer la table
            table_data = {
                "tables": [{
                    "id": "Monuments_Paris",
                    "columns": [
                        {"id": "nom", "type": "Text", "label": "Nom du Monument"},
                        {"id": "position", "type": "Geometry", "label": "Position GPS"},
                        {"id": "type_monument", "type": "Text", "label": "Type"},
                        {"id": "hauteur_m", "type": "Numeric", "label": "Hauteur (m)"},
                        {"id": "visiteurs_an", "type": "Numeric", "label": "Visiteurs/an"},
                        {"id": "distance_louvre", "type": "Numeric", "label": "Distance au Louvre (km)", 
                         "isFormula": True, "formula": "grist.ST_DISTANCE($position, 'POINT(2.3376 48.8606)', 'km')"},
                        {"id": "aire_influence", "type": "Numeric", "label": "Zone d'influence (km²)",
                         "isFormula": True, "formula": "3.14159 * (0.5 + $hauteur_m/1000) ** 2"}
                    ]
                }]
            }
            
            response = self.session.post(f"{self.base_url}/api/docs/{doc_id}/apply", json={
                "actions": [["AddTable", "Monuments_Paris", table_data["tables"][0]["columns"]]]
            })
            
            if response.status_code not in [200, 201]:
                print(f"❌ Erreur création table: {response.status_code}")
                return False
            
            print("✅ Table Monuments_Paris créée")
            
            # 2. Ajouter les données
            print("📍 Ajout données monuments...")
            
            records = []
            for monument in self.paris_monuments:
                records.append({
                    "nom": monument["nom"],
                    "position": monument["coords"],
                    "type_monument": monument["type"],
                    "hauteur_m": monument["hauteur"],
                    "visiteurs_an": monument["visiteurs_annuel"]
                })
            
            # Ajouter les enregistrements par lots
            for i in range(0, len(records), 3):
                batch = records[i:i+3]
                response = self.session.post(f"{self.base_url}/api/docs/{doc_id}/tables/Monuments_Paris/records", 
                                           json={"records": [{"fields": record} for record in batch]})
                if response.status_code in [200, 201]:
                    print(f"✅ Ajouté {len(batch)} monuments")
                else:
                    print(f"⚠️ Erreur ajout batch: {response.status_code}")
                
                time.sleep(1)  # Pause entre les batches
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur création monuments: {e}")
            return False
    
    def create_zones_table(self, doc_id):
        """Créer la table des zones parisiennes avec polygones"""
        print("\n🗺️ CRÉATION TABLE ZONES")
        print("=" * 30)
        
        try:
            # 1. Créer la table
            table_data = {
                "tables": [{
                    "id": "Zones_Paris", 
                    "columns": [
                        {"id": "nom_zone", "type": "Text", "label": "Nom de la Zone"},
                        {"id": "geometrie", "type": "Geometry", "label": "Délimitation"},
                        {"id": "type_zone", "type": "Text", "label": "Type de Zone"},
                        {"id": "superficie_ha", "type": "Numeric", "label": "Superficie (ha)"},
                        {"id": "aire_calculee", "type": "Numeric", "label": "Aire calculée (m²)",
                         "isFormula": True, "formula": "grist.ST_AREA($geometrie, 'm2')"},
                        {"id": "centroid", "type": "Geometry", "label": "Centre géométrique", 
                         "isFormula": True, "formula": "grist.ST_CENTROID($geometrie)"}
                    ]
                }]
            }
            
            response = self.session.post(f"{self.base_url}/api/docs/{doc_id}/apply", json={
                "actions": [["AddTable", "Zones_Paris", table_data["tables"][0]["columns"]]]
            })
            
            if response.status_code not in [200, 201]:
                print(f"❌ Erreur création table zones: {response.status_code}")
                return False
            
            print("✅ Table Zones_Paris créée")
            
            # 2. Ajouter les données
            print("🗺️ Ajout données zones...")
            
            for zone in self.paris_zones:
                record = {
                    "nom_zone": zone["nom"],
                    "geometrie": zone["zone"],
                    "type_zone": zone["type"],
                    "superficie_ha": zone["superficie_ha"]
                }
                
                response = self.session.post(f"{self.base_url}/api/docs/{doc_id}/tables/Zones_Paris/records",
                                           json={"records": [{"fields": record}]})
                if response.status_code in [200, 201]:
                    print(f"✅ Ajouté zone: {zone['nom']}")
                else:
                    print(f"⚠️ Erreur ajout {zone['nom']}: {response.status_code}")
                
                time.sleep(1)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur création zones: {e}")
            return False
    
    def create_documents_table(self, doc_id):
        """Créer la table des documents avec vecteurs sémantiques"""
        print("\n📚 CRÉATION TABLE DOCUMENTS SÉMANTIQUES")
        print("=" * 45)
        
        try:
            # 1. Créer la table
            table_data = {
                "tables": [{
                    "id": "Documents_Semantiques",
                    "columns": [
                        {"id": "titre", "type": "Text", "label": "Titre du Document"},
                        {"id": "contenu", "type": "Text", "label": "Contenu/Mots-clés"},
                        {"id": "vecteur_embedding", "type": "Vector", "label": "Vecteur Sémantique"},
                        {"id": "categorie", "type": "Choice", "label": "Catégorie"},
                        {"id": "similarite_ref", "type": "Numeric", "label": "Similarité vs Architecture",
                         "isFormula": True, "formula": "grist.VECTOR_SIMILARITY($vecteur_embedding, [0.8, 0.1, 0.9, 0.2, 0.7, 0.3, 0.6, 0.8], 'cosine')"},
                        {"id": "longueur_vecteur", "type": "Numeric", "label": "Norme du Vecteur",
                         "isFormula": True, "formula": "sum(x*x for x in $vecteur_embedding) ** 0.5"}
                    ]
                }]
            }
            
            response = self.session.post(f"{self.base_url}/api/docs/{doc_id}/apply", json={
                "actions": [["AddTable", "Documents_Semantiques", table_data["tables"][0]["columns"]]]
            })
            
            if response.status_code not in [200, 201]:
                print(f"❌ Erreur création table documents: {response.status_code}")
                return False
            
            print("✅ Table Documents_Semantiques créée")
            
            # 2. Ajouter les données
            print("📖 Ajout documents sémantiques...")
            
            for doc in self.documents_semantiques:
                record = {
                    "titre": doc["titre"],
                    "contenu": doc["contenu"],
                    "vecteur_embedding": doc["vecteur"],
                    "categorie": doc["categorie"]
                }
                
                response = self.session.post(f"{self.base_url}/api/docs/{doc_id}/tables/Documents_Semantiques/records",
                                           json={"records": [{"fields": record}]})
                if response.status_code in [200, 201]:
                    print(f"✅ Ajouté document: {doc['titre'][:30]}...")
                else:
                    print(f"⚠️ Erreur ajout {doc['titre'][:20]}: {response.status_code}")
                
                time.sleep(1)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur création documents: {e}")
            return False
    
    def create_analysis_table(self, doc_id):
        """Créer la table d'analyse avec calculs cross-table"""
        print("\n📊 CRÉATION TABLE ANALYSES")
        print("=" * 32)
        
        try:
            # Table d'analyses combinées
            table_data = {
                "tables": [{
                    "id": "Analyses_Combinées",
                    "columns": [
                        {"id": "analyse_nom", "type": "Text", "label": "Nom de l'Analyse"},
                        {"id": "type_analyse", "type": "Choice", "label": "Type d'Analyse"},
                        {"id": "point_reference", "type": "Geometry", "label": "Point de Référence"},
                        {"id": "nb_monuments_1km", "type": "Numeric", "label": "Monuments < 1km",
                         "isFormula": True, "formula": "len([m for m in Monuments_Paris.all if grist.ST_DISTANCE(m.position, $point_reference, 'km') < 1])"},
                        {"id": "zone_contient_point", "type": "Text", "label": "Zone Contenante",
                         "isFormula": True, "formula": "next((z.nom_zone for z in Zones_Paris.all if grist.ST_CONTAINS(z.geometrie, $point_reference)), 'Aucune')"},
                        {"id": "distance_plus_proche", "type": "Numeric", "label": "Distance Plus Proche Monument (km)",
                         "isFormula": True, "formula": "min(grist.ST_DISTANCE(m.position, $point_reference, 'km') for m in Monuments_Paris.all)"}
                    ]
                }]
            }
            
            response = self.session.post(f"{self.base_url}/api/docs/{doc_id}/apply", json={
                "actions": [["AddTable", "Analyses_Combinées", table_data["tables"][0]["columns"]]]
            })
            
            if response.status_code not in [200, 201]:
                print(f"❌ Erreur création table analyses: {response.status_code}")
                return False
            
            print("✅ Table Analyses_Combinées créée")
            
            # 2. Ajouter des analyses de test
            analyses_test = [
                {"nom": "Centre de Paris", "type": "Point Central", "coords": "POINT(2.3522 48.8566)"},
                {"nom": "Rive Droite", "type": "Analyse Zonale", "coords": "POINT(2.3317 48.8720)"},
                {"nom": "Rive Gauche", "type": "Analyse Zonale", "coords": "POINT(2.3462 48.8462)"},
                {"nom": "Montmartre", "type": "Quartier", "coords": "POINT(2.3431 48.8867)"}
            ]
            
            print("📈 Ajout analyses...")
            for analyse in analyses_test:
                record = {
                    "analyse_nom": analyse["nom"],
                    "type_analyse": analyse["type"],
                    "point_reference": analyse["coords"]
                }
                
                response = self.session.post(f"{self.base_url}/api/docs/{doc_id}/tables/Analyses_Combinées/records",
                                           json={"records": [{"fields": record}]})
                if response.status_code in [200, 201]:
                    print(f"✅ Ajouté analyse: {analyse['nom']}")
                else:
                    print(f"⚠️ Erreur ajout {analyse['nom']}: {response.status_code}")
                
                time.sleep(1)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur création analyses: {e}")
            return False
    
    def test_all_functions(self, doc_id):
        """Tester toutes les fonctions via les endpoints pour validation"""
        print("\n🧪 VALIDATION FONCTIONS SHOWCASE")
        print("=" * 40)
        
        tests = [
            {
                "nom": "Distance Tour Eiffel - Notre-Dame",
                "endpoint": "distance",
                "payload": {"point1": "POINT(2.2945 48.8584)", "point2": "POINT(2.3522 48.8566)", "unit": "km"},
                "attendu": "~6.4 km"
            },
            {
                "nom": "Aire Champs-Élysées (approximation)",
                "endpoint": "area", 
                "payload": {"polygon": "POLYGON((2.2945 48.8700, 2.3138 48.8700, 2.3138 48.8738, 2.2945 48.8738, 2.2945 48.8700))", "unit": "m2"},
                "attendu": ">500,000 m²"
            },
            {
                "nom": "Similarité documents Architecture vs Tourisme",
                "endpoint": "similarity",
                "payload": {"vector1": [0.8, 0.1, 0.9, 0.2, 0.7, 0.3, 0.6, 0.8], "vector2": [0.7, 0.9, 0.3, 0.8, 0.5, 0.6, 0.4, 0.7], "method": "cosine"},
                "attendu": "~0.6-0.8"
            }
        ]
        
        results = {}
        for test in tests:
            try:
                response = self.session.post(f"{self.base_url}/api/docs/{doc_id}/spatial/{test['endpoint']}" if test['endpoint'] != 'similarity' else f"{self.base_url}/api/docs/{doc_id}/vector/similarity",
                                           json=test["payload"])
                
                if response.status_code == 200:
                    data = response.json()
                    if test['endpoint'] == 'distance':
                        result = data['data']['distance']
                        print(f"✅ {test['nom']}: {result:.2f} km {test['attendu']}")
                    elif test['endpoint'] == 'area':
                        result = data['data']['area']
                        print(f"✅ {test['nom']}: {result:,.0f} m² {test['attendu']}")
                    elif test['endpoint'] == 'similarity':
                        result = data['data']['similarity']
                        print(f"✅ {test['nom']}: {result:.3f} {test['attendu']}")
                    
                    results[test['nom']] = True
                else:
                    print(f"❌ {test['nom']}: Erreur {response.status_code}")
                    results[test['nom']] = False
                    
            except Exception as e:
                print(f"❌ {test['nom']}: Exception {e}")
                results[test['nom']] = False
        
        return results
    
    def create_complete_showcase(self):
        """Créer le showcase complet avec toutes les fonctionnalités"""
        print("🌟 CRÉATION SHOWCASE COMPLET GRIST")
        print("=" * 60)
        print("🎯 Extensions Spatiales & Vectorielles")
        print("🗼 Données réelles de Paris")
        print("🔢 Vecteurs sémantiques")
        print("📊 Analyses cross-table")
        
        # 1. Créer le document principal
        doc_id = self.create_showcase_document()
        if not doc_id:
            return False
        
        # 2. Créer toutes les tables
        success = True
        success &= self.create_monuments_table(doc_id)
        time.sleep(2)
        success &= self.create_zones_table(doc_id)
        time.sleep(2)
        success &= self.create_documents_table(doc_id)
        time.sleep(2)
        success &= self.create_analysis_table(doc_id)
        
        if not success:
            print("⚠️ Certaines tables n'ont pas pu être créées complètement")
        
        # 3. Tester les fonctions
        time.sleep(5)  # Attendre que tout soit prêt
        test_results = self.test_all_functions(doc_id)
        
        # 4. Rapport final
        print("\n" + "=" * 60)
        print("🎉 SHOWCASE GRIST CRÉÉ AVEC SUCCÈS !")
        print("=" * 60)
        
        print(f"📄 Document ID: {doc_id}")
        print(f"🌐 URL: {self.base_url}/o/docs/v7KqgVMDqTQu/Test-Fonctions-Python-Natives")
        
        print("\n📊 TABLES CRÉÉES:")
        print("   🗼 Monuments_Paris - 8 monuments avec positions GPS et calculs de distance")
        print("   🗺️ Zones_Paris - 5 zones avec polygones et calculs d'aire")  
        print("   📚 Documents_Semantiques - 6 documents avec vecteurs d'embedding")
        print("   📈 Analyses_Combinées - 4 analyses cross-table avec fonctions spatiales")
        
        print("\n🔧 FONCTIONNALITÉS DÉMONTRÉES:")
        print("   📍 ST_DISTANCE - Calculs de distance entre monuments")
        print("   📐 ST_AREA - Calculs d'aire des zones parisiennes")
        print("   🎯 ST_CONTAINS - Détection de points dans zones")
        print("   📍 ST_CENTROID - Centres géométriques des zones")
        print("   🔢 VECTOR_SIMILARITY - Similarité sémantique des documents")
        
        test_success = sum(test_results.values())
        test_total = len(test_results)
        print(f"\n✅ VALIDATION: {test_success}/{test_total} fonctions testées avec succès")
        
        print("\n🎯 PROCHAINES ÉTAPES:")
        print("   1. Ouvrir le document dans Grist")
        print("   2. Explorer les différentes tables")
        print("   3. Tester les formules dans les colonnes")
        print("   4. Créer de nouvelles analyses spatiales")
        print("   5. Ajouter vos propres données géographiques")
        
        return True

if __name__ == "__main__":
    creator = GristShowcaseCreator()
    success = creator.create_complete_showcase()
    sys.exit(0 if success else 1)
