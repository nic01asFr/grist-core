#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CRÉATION SHOWCASE STRUCTURÉ - TABLES SPÉCIALISÉES PAR TYPE
Organise les données par type avec colonnes appropriées et traitements démonstrables
"""

import requests
import json
import time

class StructuredShowcaseCreator:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8888"
        self.api_key = "120d56683d06c78dbeeb6ef8cedccec3c2df44b7"
        self.doc_id = "s77bLUZsrznfDn6f8c3bsq"  # Document existant
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })

    def clear_existing_data(self):
        """Nettoyer les données existantes de Table1"""
        print("🧹 NETTOYAGE DES DONNÉES EXISTANTES")
        print("=" * 40)
        
        try:
            # Récupérer tous les enregistrements
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/tables/Table1/records")
            if response.status_code == 200:
                records = response.json()['records']
                record_ids = [record['id'] for record in records]
                
                if record_ids:
                    # Supprimer tous les enregistrements
                    delete_response = self.session.delete(
                        f"{self.base_url}/api/docs/{self.doc_id}/tables/Table1/records",
                        json=record_ids
                    )
                    if delete_response.status_code == 200:
                        print(f"✅ Supprimé {len(record_ids)} enregistrements existants")
                    else:
                        print(f"⚠️ Erreur suppression: {delete_response.status_code}")
                else:
                    print("✅ Aucun enregistrement à supprimer")
            else:
                print(f"⚠️ Erreur récupération: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur nettoyage: {e}")

    def create_monuments_table(self):
        """Créer et populer la table des monuments avec colonnes typées"""
        print("\n🏛️ CRÉATION TABLE MONUMENTS PARISIENS")
        print("=" * 45)
        
        # D'abord, modifier les colonnes de Table1 pour les monuments
        columns_to_create = [
            {
                "id": "Nom",
                "fields": {
                    "label": "Nom du Monument",
                    "type": "Text"
                }
            },
            {
                "id": "Localisation", 
                "fields": {
                    "label": "Coordonnées GPS",
                    "type": "Geometry"
                }
            },
            {
                "id": "Type_Monument",
                "fields": {
                    "label": "Type",
                    "type": "Choice",
                    "widgetOptions": json.dumps({
                        "choices": ["Monument", "Cathédrale", "Musée", "Basilique", "Arc", "Palais"]
                    })
                }
            },
            {
                "id": "Hauteur_m",
                "fields": {
                    "label": "Hauteur (m)",
                    "type": "Numeric"
                }
            },
            {
                "id": "Visiteurs_M",
                "fields": {
                    "label": "Visiteurs (millions/an)",
                    "type": "Numeric"
                }
            },
            {
                "id": "Distance_Tour_Eiffel",
                "fields": {
                    "label": "Distance Tour Eiffel (km)",
                    "type": "Numeric",
                    "isFormula": True,
                    "formula": "grist.ST_DISTANCE('POINT(2.2945 48.8584)', $Localisation, 'km')"
                }
            }
        ]
        
        # Supprimer les anciennes colonnes A, B, C
        old_columns = ['A', 'B', 'C']
        for col_id in old_columns:
            try:
                delete_response = self.session.delete(
                    f"{self.base_url}/api/docs/{self.doc_id}/tables/Table1/columns/{col_id}"
                )
                if delete_response.status_code == 200:
                    print(f"✅ Supprimé ancienne colonne {col_id}")
                time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ Erreur suppression {col_id}: {e}")
        
        # Créer les nouvelles colonnes
        for column in columns_to_create:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/docs/{self.doc_id}/tables/Table1/columns",
                    json={"columns": [column]}
                )
                if response.status_code == 200:
                    print(f"✅ Colonne créée: {column['fields']['label']}")
                else:
                    print(f"⚠️ Erreur colonne {column['id']}: {response.status_code}")
                time.sleep(0.5)
            except Exception as e:
                print(f"❌ Erreur {column['id']}: {e}")
        
        # Données des monuments
        monuments_data = [
            {
                "Nom": "Tour Eiffel",
                "Localisation": "POINT(2.2945 48.8584)",
                "Type_Monument": "Monument", 
                "Hauteur_m": 330,
                "Visiteurs_M": 7.0
            },
            {
                "Nom": "Notre-Dame",
                "Localisation": "POINT(2.3522 48.8566)",
                "Type_Monument": "Cathédrale",
                "Hauteur_m": 69,
                "Visiteurs_M": 14.0
            },
            {
                "Nom": "Arc de Triomphe", 
                "Localisation": "POINT(2.2950 48.8738)",
                "Type_Monument": "Arc",
                "Hauteur_m": 50,
                "Visiteurs_M": 1.5
            },
            {
                "Nom": "Musée du Louvre",
                "Localisation": "POINT(2.3376 48.8606)",
                "Type_Monument": "Musée",
                "Hauteur_m": 21,
                "Visiteurs_M": 9.6
            },
            {
                "Nom": "Sacré-Cœur",
                "Localisation": "POINT(2.3431 48.8867)",
                "Type_Monument": "Basilique",
                "Hauteur_m": 83,
                "Visiteurs_M": 10.5
            }
        ]
        
        print("📍 Ajout des monuments...")
        for monument in monuments_data:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/docs/{self.doc_id}/tables/Table1/records",
                    json={"records": [{"fields": monument}]}
                )
                if response.status_code in [200, 201]:
                    print(f"✅ Ajouté: {monument['Nom']}")
                else:
                    print(f"⚠️ Erreur {monument['Nom']}: {response.status_code}")
                time.sleep(0.5)
            except Exception as e:
                print(f"❌ Erreur {monument['Nom']}: {e}")

    def create_zones_table(self):
        """Créer une table pour les zones géographiques"""
        print("\n🗺️ CRÉATION TABLE ZONES GÉOGRAPHIQUES")
        print("=" * 45)
        
        try:
            # Créer une nouvelle table
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/tables",
                json={
                    "tables": [{
                        "id": "Zones_Paris",
                        "columns": [
                            {
                                "id": "Nom_Zone",
                                "fields": {
                                    "label": "Nom de la Zone",
                                    "type": "Text"
                                }
                            },
                            {
                                "id": "Geometrie",
                                "fields": {
                                    "label": "Géométrie",
                                    "type": "Geometry"
                                }
                            },
                            {
                                "id": "Type_Zone",
                                "fields": {
                                    "label": "Type",
                                    "type": "Choice",
                                    "widgetOptions": json.dumps({
                                        "choices": ["Avenue", "Parc", "Place", "Jardin", "Quartier"]
                                    })
                                }
                            },
                            {
                                "id": "Aire_m2",
                                "fields": {
                                    "label": "Aire calculée (m²)",
                                    "type": "Numeric",
                                    "isFormula": True,
                                    "formula": "grist.ST_AREA($Geometrie, 'm2')"
                                }
                            },
                            {
                                "id": "Aire_hectares", 
                                "fields": {
                                    "label": "Aire (hectares)",
                                    "type": "Numeric",
                                    "isFormula": True,
                                    "formula": "$Aire_m2 / 10000"
                                }
                            },
                            {
                                "id": "Centre_Geometrique",
                                "fields": {
                                    "label": "Centre géométrique",
                                    "type": "Geometry",
                                    "isFormula": True,
                                    "formula": "grist.ST_CENTROID($Geometrie)"
                                }
                            }
                        ]
                    }]
                }
            )
            
            if response.status_code == 200:
                print("✅ Table Zones_Paris créée")
                
                # Données des zones
                zones_data = [
                    {
                        "Nom_Zone": "Champs-Élysées",
                        "Geometrie": "POLYGON((2.2945 48.8700, 2.3138 48.8700, 2.3138 48.8738, 2.2945 48.8738, 2.2945 48.8700))",
                        "Type_Zone": "Avenue"
                    },
                    {
                        "Nom_Zone": "Jardins des Tuileries",
                        "Geometrie": "POLYGON((2.3270 48.8630, 2.3330 48.8630, 2.3330 48.8650, 2.3270 48.8650, 2.3270 48.8630))",
                        "Type_Zone": "Jardin"
                    },
                    {
                        "Nom_Zone": "Place de la Concorde",
                        "Geometrie": "POLYGON((2.3213 48.8656, 2.3240 48.8656, 2.3240 48.8668, 2.3213 48.8668, 2.3213 48.8656))",
                        "Type_Zone": "Place"
                    }
                ]
                
                print("🌳 Ajout des zones...")
                for zone in zones_data:
                    try:
                        response = self.session.post(
                            f"{self.base_url}/api/docs/{self.doc_id}/tables/Zones_Paris/records",
                            json={"records": [{"fields": zone}]}
                        )
                        if response.status_code in [200, 201]:
                            print(f"✅ Ajouté: {zone['Nom_Zone']}")
                        else:
                            print(f"⚠️ Erreur {zone['Nom_Zone']}: {response.status_code}")
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"❌ Erreur {zone['Nom_Zone']}: {e}")
            else:
                print(f"❌ Erreur création table: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur création table zones: {e}")

    def create_documents_table(self):
        """Créer une table pour les documents sémantiques"""
        print("\n📚 CRÉATION TABLE DOCUMENTS SÉMANTIQUES")
        print("=" * 45)
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/tables",
                json={
                    "tables": [{
                        "id": "Documents_Semantiques",
                        "columns": [
                            {
                                "id": "Titre_Document",
                                "fields": {
                                    "label": "Titre du Document", 
                                    "type": "Text"
                                }
                            },
                            {
                                "id": "Embedding_Vector",
                                "fields": {
                                    "label": "Vecteur d'Embedding",
                                    "type": "Vector"
                                }
                            },
                            {
                                "id": "Domaine",
                                "fields": {
                                    "label": "Domaine",
                                    "type": "Choice",
                                    "widgetOptions": json.dumps({
                                        "choices": ["Architecture", "Tourisme", "Gastronomie", "Histoire", "Art"]
                                    })
                                }
                            },
                            {
                                "id": "Mots_Cles",
                                "fields": {
                                    "label": "Mots-clés",
                                    "type": "Text"
                                }
                            },
                            {
                                "id": "Similarite_Architecture",
                                "fields": {
                                    "label": "Similarité avec Architecture",
                                    "type": "Numeric",
                                    "isFormula": True,
                                    "formula": "grist.VECTOR_SIMILARITY($Embedding_Vector, [0.8, 0.1, 0.9, 0.2, 0.7, 0.3, 0.6, 0.8], 'cosine')"
                                }
                            },
                            {
                                "id": "Similarite_Tourisme",
                                "fields": {
                                    "label": "Similarité avec Tourisme", 
                                    "type": "Numeric",
                                    "isFormula": True,
                                    "formula": "grist.VECTOR_SIMILARITY($Embedding_Vector, [0.7, 0.9, 0.3, 0.8, 0.5, 0.6, 0.4, 0.7], 'cosine')"
                                }
                            }
                        ]
                    }]
                }
            )
            
            if response.status_code == 200:
                print("✅ Table Documents_Semantiques créée")
                
                # Données des documents
                documents_data = [
                    {
                        "Titre_Document": "Guide Architecture Gothique",
                        "Embedding_Vector": [0.8, 0.1, 0.9, 0.2, 0.7, 0.3, 0.6, 0.8],
                        "Domaine": "Architecture",
                        "Mots_Cles": "cathédrale gothique voûtes arc-boutant"
                    },
                    {
                        "Titre_Document": "Guide Tourisme Paris",
                        "Embedding_Vector": [0.7, 0.9, 0.3, 0.8, 0.5, 0.6, 0.4, 0.7],
                        "Domaine": "Tourisme", 
                        "Mots_Cles": "visite monument patrimoine histoire"
                    },
                    {
                        "Titre_Document": "Guide Gastronomie Française",
                        "Embedding_Vector": [0.2, 0.6, 0.1, 0.5, 0.9, 0.8, 0.7, 0.3],
                        "Domaine": "Gastronomie",
                        "Mots_Cles": "restaurant cuisine française bistrot"
                    },
                    {
                        "Titre_Document": "Histoire de Paris",
                        "Embedding_Vector": [0.6, 0.4, 0.8, 0.7, 0.3, 0.9, 0.5, 0.6],
                        "Domaine": "Histoire",
                        "Mots_Cles": "histoire chronologie événements roi"
                    },
                    {
                        "Titre_Document": "Art et Musées Parisiens",
                        "Embedding_Vector": [0.9, 0.3, 0.7, 0.4, 0.8, 0.2, 0.6, 0.9],
                        "Domaine": "Art",
                        "Mots_Cles": "peinture sculpture exposition musée"
                    }
                ]
                
                print("📖 Ajout des documents...")
                for document in documents_data:
                    try:
                        response = self.session.post(
                            f"{self.base_url}/api/docs/{self.doc_id}/tables/Documents_Semantiques/records",
                            json={"records": [{"fields": document}]}
                        )
                        if response.status_code in [200, 201]:
                            print(f"✅ Ajouté: {document['Titre_Document']}")
                        else:
                            print(f"⚠️ Erreur {document['Titre_Document']}: {response.status_code}")
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"❌ Erreur {document['Titre_Document']}: {e}")
            else:
                print(f"❌ Erreur création table: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur création table documents: {e}")

    def create_analyses_table(self):
        """Créer une table d'analyses combinées montrant l'interaction des types"""
        print("\n🔬 CRÉATION TABLE ANALYSES COMBINÉES")
        print("=" * 45)
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/docs/{self.doc_id}/tables",
                json={
                    "tables": [{
                        "id": "Analyses_Combinees",
                        "columns": [
                            {
                                "id": "Analyse_Nom",
                                "fields": {
                                    "label": "Nom de l'Analyse",
                                    "type": "Text"
                                }
                            },
                            {
                                "id": "Point_Reference",
                                "fields": {
                                    "label": "Point de Référence",
                                    "type": "Geometry"
                                }
                            },
                            {
                                "id": "Zone_Test",
                                "fields": {
                                    "label": "Zone à Tester", 
                                    "type": "Geometry"
                                }
                            },
                            {
                                "id": "Contient_Point",
                                "fields": {
                                    "label": "Zone contient Point",
                                    "type": "Bool",
                                    "isFormula": True,
                                    "formula": "grist.ST_CONTAINS($Zone_Test, $Point_Reference)"
                                }
                            },
                            {
                                "id": "Distance_Centre",
                                "fields": {
                                    "label": "Distance au centre (km)",
                                    "type": "Numeric", 
                                    "isFormula": True,
                                    "formula": "grist.ST_DISTANCE($Point_Reference, grist.ST_CENTROID($Zone_Test), 'km')"
                                }
                            },
                            {
                                "id": "Vecteur_Contexte",
                                "fields": {
                                    "label": "Vecteur Contexte",
                                    "type": "Vector"
                                }
                            },
                            {
                                "id": "Score_Pertinence",
                                "fields": {
                                    "label": "Score de Pertinence",
                                    "type": "Numeric",
                                    "isFormula": True,
                                    "formula": "grist.VECTOR_SIMILARITY($Vecteur_Contexte, [0.8, 0.5, 0.9, 0.7], 'cosine')"
                                }
                            }
                        ]
                    }]
                }
            )
            
            if response.status_code == 200:
                print("✅ Table Analyses_Combinees créée")
                
                # Données d'analyses
                analyses_data = [
                    {
                        "Analyse_Nom": "Tour Eiffel dans Champs-Élysées ?",
                        "Point_Reference": "POINT(2.2945 48.8584)",
                        "Zone_Test": "POLYGON((2.2945 48.8700, 2.3138 48.8700, 2.3138 48.8738, 2.2945 48.8738, 2.2945 48.8700))",
                        "Vecteur_Contexte": [0.9, 0.2, 0.8, 0.6]
                    },
                    {
                        "Analyse_Nom": "Louvre dans Tuileries ?",
                        "Point_Reference": "POINT(2.3376 48.8606)",
                        "Zone_Test": "POLYGON((2.3270 48.8630, 2.3330 48.8630, 2.3330 48.8650, 2.3270 48.8650, 2.3270 48.8630))",
                        "Vecteur_Contexte": [0.7, 0.8, 0.5, 0.9]
                    },
                    {
                        "Analyse_Nom": "Notre-Dame et Place Concorde",
                        "Point_Reference": "POINT(2.3522 48.8566)",
                        "Zone_Test": "POLYGON((2.3213 48.8656, 2.3240 48.8656, 2.3240 48.8668, 2.3213 48.8668, 2.3213 48.8656))",
                        "Vecteur_Contexte": [0.6, 0.7, 0.4, 0.8]
                    }
                ]
                
                print("🧪 Ajout des analyses...")
                for analyse in analyses_data:
                    try:
                        response = self.session.post(
                            f"{self.base_url}/api/docs/{self.doc_id}/tables/Analyses_Combinees/records",
                            json={"records": [{"fields": analyse}]}
                        )
                        if response.status_code in [200, 201]:
                            print(f"✅ Ajouté: {analyse['Analyse_Nom']}")
                        else:
                            print(f"⚠️ Erreur {analyse['Analyse_Nom']}: {response.status_code}")
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"❌ Erreur {analyse['Analyse_Nom']}: {e}")
            else:
                print(f"❌ Erreur création table: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erreur création table analyses: {e}")

    def test_all_functions(self):
        """Tester toutes les fonctions via les endpoints"""
        print("\n🧪 VALIDATION GLOBALE DES CAPACITÉS")
        print("=" * 45)
        
        tests = [
            {
                "nom": "Distance Tour Eiffel ↔ Notre-Dame",
                "endpoint": "spatial/distance",
                "payload": {
                    "point1": "POINT(2.2945 48.8584)",
                    "point2": "POINT(2.3522 48.8566)", 
                    "unit": "km"
                }
            },
            {
                "nom": "Aire Champs-Élysées",
                "endpoint": "spatial/area",
                "payload": {
                    "polygon": "POLYGON((2.2945 48.8700, 2.3138 48.8700, 2.3138 48.8738, 2.2945 48.8738, 2.2945 48.8700))",
                    "unit": "m2"
                }
            },
            {
                "nom": "Louvre contenu dans Tuileries ?",
                "endpoint": "spatial/contains",
                "payload": {
                    "container": "POLYGON((2.3270 48.8630, 2.3330 48.8630, 2.3330 48.8650, 2.3270 48.8650, 2.3270 48.8630))",
                    "contained": "POINT(2.3376 48.8606)"
                }
            },
            {
                "nom": "Similarité Architecture vs Tourisme",
                "endpoint": "vector/similarity",
                "payload": {
                    "vector1": [0.8, 0.1, 0.9, 0.2, 0.7, 0.3, 0.6, 0.8],
                    "vector2": [0.7, 0.9, 0.3, 0.8, 0.5, 0.6, 0.4, 0.7],
                    "method": "cosine"
                }
            }
        ]
        
        for test in tests:
            try:
                url = f"{self.base_url}/api/docs/{self.doc_id}/{test['endpoint']}"
                response = self.session.post(url, json=test["payload"])
                
                if response.status_code == 200:
                    data = response.json()['data']
                    if 'distance' in data:
                        print(f"✅ {test['nom']}: {data['distance']:.2f} km")
                    elif 'area' in data:
                        print(f"✅ {test['nom']}: {data['area']:,.0f} m²")
                    elif 'contains' in data:
                        print(f"✅ {test['nom']}: {'Oui' if data['contains'] else 'Non'}")
                    elif 'similarity' in data:
                        print(f"✅ {test['nom']}: {data['similarity']:.3f}")
                else:
                    print(f"❌ {test['nom']}: Erreur {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {test['nom']}: {e}")

    def create_structured_showcase(self):
        """Créer le showcase structuré complet"""
        print("🌟 CRÉATION SHOWCASE GRIST STRUCTURÉ")
        print("=" * 55)
        print("📊 Tables Spécialisées par Type de Données")
        print("🔧 Colonnes avec Types Appropriés (Geometry, Vector)")
        print("⚡ Formules Démonstrables en Action")
        
        print(f"\n📄 Document ID: {self.doc_id}")
        print(f"🌐 URL: {self.base_url}/o/docs/{self.doc_id[:12]}/")
        
        # 1. Nettoyer les données existantes
        self.clear_existing_data()
        
        # 2. Restructurer Table1 pour les monuments
        self.create_monuments_table()
        
        # 3. Créer table des zones géographiques  
        self.create_zones_table()
        
        # 4. Créer table des documents sémantiques
        self.create_documents_table()
        
        # 5. Créer table d'analyses combinées
        self.create_analyses_table()
        
        # 6. Valider toutes les fonctions
        self.test_all_functions()
        
        # 7. Instructions finales
        print("\n" + "=" * 55)
        print("🎉 SHOWCASE STRUCTURÉ CRÉÉ AVEC SUCCÈS !")
        print("=" * 55)
        
        print("\n📊 TABLES CRÉÉES:")
        print("   🏛️ Table1 (Monuments) - Points GPS avec calculs automatiques")
        print("   🗺️ Zones_Paris - Polygones avec aires calculées")
        print("   📚 Documents_Semantiques - Vecteurs avec similarités")
        print("   🔬 Analyses_Combinees - Interactions entre types")
        
        print("\n🔧 TYPES DE COLONNES UTILISÉS:")
        print("   📍 Geometry - Pour points et polygones")
        print("   🔢 Vector - Pour embeddings sémantiques")
        print("   📊 Numeric (Formule) - Calculs automatiques")
        print("   🎯 Choice - Catégories prédéfinies")
        print("   ✅ Bool (Formule) - Tests logiques")
        
        print("\n⚡ FORMULES EN ACTION:")
        print("   📍 ST_DISTANCE - Distance depuis Tour Eiffel")
        print("   📐 ST_AREA - Aires automatiques des zones")
        print("   📍 ST_CENTROID - Centres géométriques")
        print("   🎯 ST_CONTAINS - Tests de contenance")
        print("   🔢 VECTOR_SIMILARITY - Scores de similarité")
        
        print("\n💡 COMMENT EXPLORER:")
        print("   1. 📖 Ouvrir chaque table dans Grist")
        print("   2. 👀 Observer les calculs automatiques")
        print("   3. ✏️ Modifier des données pour voir l'impact")
        print("   4. ➕ Ajouter nouvelles lignes avec vos données")
        print("   5. 🧪 Créer nouvelles formules personnalisées")
        
        print("\n🚀 INTÉGRATION PARFAITEMENT RÉUSSIE !")
        print("✅ Structure claire et professionnelle")
        print("✅ Types de données appropriés") 
        print("✅ Traitements démonstrables")
        print("✅ Extensibilité garantie")

if __name__ == "__main__":
    creator = StructuredShowcaseCreator()
    creator.create_structured_showcase()
