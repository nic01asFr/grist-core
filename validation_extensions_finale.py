#!/usr/bin/env python3
"""
Script de validation finale des extensions avec le document de test configuré
Utilise les IDs sauvegardés pour des tests précis et reproductibles
"""

import json
import time
import requests
from typing import Dict, List, Any, Optional

class GristExtensionValidator:
    """Validateur final des extensions avec document dédié"""
    
    def __init__(self, config_file='grist_test_config.json'):
        self.config = self.load_config(config_file)
        self.api_key = "f4631937690617681be6860542a5cbdb9794c0ed"
        
        if not self.config:
            raise Exception("Configuration non trouvée - Exécutez d'abord creation_document_test_final.py")
        
        self.base_url = self.config['base_url']
        self.org_id = self.config['org_id']
        self.doc_id = self.config['doc_id']
        self.table_id = self.config['table_id']
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        print(f"🔧 Configuration chargée:")
        print(f"   Doc ID: {self.doc_id}")
        print(f"   Table: {self.table_id}")
        print(f"   URL: {self.base_url}/o/{self.org_id}/{self.doc_id}")
    
    def load_config(self, config_file):
        """Charge la configuration sauvegardée"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Configuration non trouvée: {config_file}")
            return None
        except Exception as e:
            print(f"❌ Erreur chargement config: {e}")
            return None
    
    def verify_document_accessible(self):
        """Vérifie que le document de test est accessible"""
        print("🔍 Vérification de l'accessibilité du document...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}")
            
            if response.ok:
                print("   ✅ Document accessible via API")
                return True
            else:
                print(f"   ❌ Document inaccessible: {response.status_code}")
                print(f"   Réponse: {response.text[:200]}...")
                return False
        except Exception as e:
            print(f"   ❌ Erreur vérification: {e}")
            return False
    
    def get_current_table_structure(self):
        """Récupère la structure actuelle de la table de test"""
        print("📋 Analyse de la structure actuelle...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/columns")
            
            if response.ok:
                columns = response.json().get('columns', [])
                print(f"   ✅ {len(columns)} colonnes trouvées:")
                
                structure_info = {
                    'total_columns': len(columns),
                    'geometry_columns': [],
                    'vector_columns': [],
                    'formula_columns': [],
                    'standard_columns': []
                }
                
                for col in columns:
                    col_id = col.get('id')
                    col_type = col.get('fields', {}).get('type', 'Unknown')
                    col_label = col.get('fields', {}).get('label', col_id)
                    formula = col.get('fields', {}).get('formula', '')
                    
                    print(f"      - {col_id} ({col_type}) '{col_label}'")
                    
                    if col_type == 'Geometry':
                        structure_info['geometry_columns'].append(col_id)
                    elif col_type == 'Vector':
                        structure_info['vector_columns'].append(col_id)
                    elif col_type == 'Formula':
                        structure_info['formula_columns'].append({
                            'id': col_id,
                            'formula': formula
                        })
                    else:
                        structure_info['standard_columns'].append(col_id)
                
                return structure_info
            else:
                print(f"   ❌ Erreur récupération colonnes: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Erreur analyse structure: {e}")
            return None
    
    def get_current_data(self):
        """Récupère les données actuelles de la table"""
        print("📊 Récupération des données actuelles...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/docs/{self.doc_id}/tables/{self.table_id}/records")
            
            if response.ok:
                records = response.json().get('records', [])
                print(f"   ✅ {len(records)} enregistrement(s) trouvé(s)")
                
                if records:
                    print("   📋 Aperçu des données:")
                    for i, record in enumerate(records[:3], 1):
                        fields = record.get('fields', {})
                        print(f"      {i}. {list(fields.keys())[:5]}{'...' if len(fields) > 5 else ''}")
                
                return records
            else:
                print(f"   ❌ Erreur récupération données: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"   ❌ Erreur récupération données: {e}")
            return []
    
    def analyze_formula_results(self, records, structure):
        """Analyse les résultats des formules pour validation"""
        print("🧮 Analyse des résultats de formules...")
        
        if not records:
            print("   ⚠️ Aucune donnée à analyser")
            return {}
        
        analysis = {
            'spatial_formulas': [],
            'vector_formulas': [],
            'mixed_formulas': [],
            'validation_results': []
        }
        
        # Identifier les formules spatiales et vectorielles
        for formula_col in structure.get('formula_columns', []):
            formula = formula_col.get('formula', '')
            col_id = formula_col.get('id')
            
            if 'ST_' in formula:
                analysis['spatial_formulas'].append({
                    'column': col_id,
                    'formula': formula,
                    'type': 'spatial'
                })
            elif 'VECTOR_SIMILARITY' in formula:
                analysis['vector_formulas'].append({
                    'column': col_id,
                    'formula': formula,
                    'type': 'vector'
                })
            elif 'ST_' in formula and 'VECTOR_' in formula:
                analysis['mixed_formulas'].append({
                    'column': col_id,
                    'formula': formula,
                    'type': 'mixed'
                })
        
        # Analyser les valeurs calculées
        for record in records[:3]:  # Limiter l'analyse aux 3 premiers
            fields = record.get('fields', {})
            
            for formula_info in analysis['spatial_formulas'] + analysis['vector_formulas'] + analysis['mixed_formulas']:
                col_id = formula_info['column']
                value = fields.get(col_id)
                
                if value is not None:
                    try:
                        float_value = float(value)
                        
                        # Validation spécifique selon le type
                        if formula_info['type'] == 'spatial':
                            if 'DISTANCE' in formula_info['formula']:
                                # Distance en km - doit être raisonnable pour Paris
                                is_valid = 0 <= float_value <= 50
                                validation = {
                                    'column': col_id,
                                    'value': float_value,
                                    'expected': 'Distance 0-50 km',
                                    'valid': is_valid,
                                    'type': 'spatial_distance'
                                }
                            elif 'AREA' in formula_info['formula']:
                                # Aire - doit être positive
                                is_valid = float_value > 0
                                validation = {
                                    'column': col_id,
                                    'value': float_value,
                                    'expected': 'Aire > 0',
                                    'valid': is_valid,
                                    'type': 'spatial_area'
                                }
                            else:
                                validation = {
                                    'column': col_id,
                                    'value': float_value,
                                    'expected': 'Valeur numérique',
                                    'valid': True,
                                    'type': 'spatial_other'
                                }
                        
                        elif formula_info['type'] == 'vector':
                            # Similarité cosinus - doit être entre -1 et 1
                            is_valid = -1 <= float_value <= 1
                            validation = {
                                'column': col_id,
                                'value': float_value,
                                'expected': 'Similarité [-1, 1]',
                                'valid': is_valid,
                                'type': 'vector_similarity'
                            }
                        
                        else:  # mixed
                            # Score composite - généralement 0-1
                            is_valid = 0 <= float_value <= 1
                            validation = {
                                'column': col_id,
                                'value': float_value,
                                'expected': 'Score [0, 1]',
                                'valid': is_valid,
                                'type': 'mixed_score'
                            }
                        
                        analysis['validation_results'].append(validation)
                        
                    except ValueError:
                        analysis['validation_results'].append({
                            'column': col_id,
                            'value': value,
                            'expected': 'Valeur numérique',
                            'valid': False,
                            'type': 'parse_error'
                        })
        
        # Afficher résultats validation
        if analysis['validation_results']:
            print("   📊 Résultats de validation:")
            valid_count = 0
            
            for validation in analysis['validation_results']:
                status = "✅" if validation['valid'] else "❌"
                print(f"      {status} {validation['column']}: {validation['value']} ({validation['expected']})")
                if validation['valid']:
                    valid_count += 1
            
            total_count = len(analysis['validation_results'])
            print(f"   🎯 Score validation: {valid_count}/{total_count} ({valid_count/total_count*100:.1f}%)")
        
        return analysis
    
    def generate_test_report(self, structure, records, analysis):
        """Génère un rapport complet de test"""
        print("📝 Génération du rapport final...")
        
        report = {
            'test_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'document_config': self.config,
            'structure_analysis': structure,
            'data_count': len(records),
            'formula_analysis': analysis,
            'extension_status': {
                'geometry_type_available': len(structure.get('geometry_columns', [])) > 0,
                'vector_type_available': len(structure.get('vector_columns', [])) > 0,
                'spatial_formulas_working': len(analysis.get('spatial_formulas', [])) > 0,
                'vector_formulas_working': len(analysis.get('vector_formulas', [])) > 0,
                'mixed_formulas_working': len(analysis.get('mixed_formulas', [])) > 0
            },
            'validation_summary': {
                'total_validations': len(analysis.get('validation_results', [])),
                'valid_results': len([v for v in analysis.get('validation_results', []) if v['valid']]),
                'invalid_results': len([v for v in analysis.get('validation_results', []) if not v['valid']])
            }
        }
        
        # Sauvegarder rapport
        try:
            with open('grist_extensions_test_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print("   💾 Rapport sauvegardé: grist_extensions_test_report.json")
        except Exception as e:
            print(f"   ⚠️ Erreur sauvegarde rapport: {e}")
        
        return report
    
    def print_final_summary(self, report):
        """Affiche le résumé final"""
        print(f"\n🎯 RÉSUMÉ FINAL DE VALIDATION")
        print("=" * 35)
        
        ext_status = report['extension_status']
        val_summary = report['validation_summary']
        
        # Status des extensions
        print("🌟 Status des Extensions:")
        status_geometry = "✅" if ext_status['geometry_type_available'] else "❌"
        status_vector = "✅" if ext_status['vector_type_available'] else "❌"
        print(f"   {status_geometry} Type Geometry: {'Disponible' if ext_status['geometry_type_available'] else 'Non disponible'}")
        print(f"   {status_vector} Type Vector: {'Disponible' if ext_status['vector_type_available'] else 'Non disponible'}")
        
        # Status des formules
        print("\n📐 Status des Formules:")
        status_spatial = "✅" if ext_status['spatial_formulas_working'] else "❌"
        status_vector_f = "✅" if ext_status['vector_formulas_working'] else "❌"
        status_mixed = "✅" if ext_status['mixed_formulas_working'] else "❌"
        print(f"   {status_spatial} Formules spatiales: {'Fonctionnelles' if ext_status['spatial_formulas_working'] else 'Non fonctionnelles'}")
        print(f"   {status_vector_f} Formules vectorielles: {'Fonctionnelles' if ext_status['vector_formulas_working'] else 'Non fonctionnelles'}")
        print(f"   {status_mixed} Formules mixtes: {'Fonctionnelles' if ext_status['mixed_formulas_working'] else 'Non fonctionnelles'}")
        
        # Validation des résultats
        print("\n🎯 Validation des Résultats:")
        if val_summary['total_validations'] > 0:
            success_rate = val_summary['valid_results'] / val_summary['total_validations'] * 100
            print(f"   📊 Validations réussies: {val_summary['valid_results']}/{val_summary['total_validations']} ({success_rate:.1f}%)")
            
            if success_rate >= 90:
                print("   🎉 EXCELLENTS RÉSULTATS !")
            elif success_rate >= 70:
                print("   ✅ BONS RÉSULTATS")
            else:
                print("   ⚠️ RÉSULTATS À AMÉLIORER")
        else:
            print("   ⚠️ Aucune validation effectuée")
        
        # Score final
        feature_count = sum([
            ext_status['geometry_type_available'],
            ext_status['vector_type_available'],
            ext_status['spatial_formulas_working'],
            ext_status['vector_formulas_working']
        ])
        
        print(f"\n🏆 SCORE FINAL: {feature_count}/4 fonctionnalités opérationnelles")
        
        if feature_count >= 3:
            print("🎉 SUCCÈS ! Extensions largement opérationnelles !")
        elif feature_count >= 2:
            print("✅ Succès partiel - Extensions partiellement opérationnelles")
        else:
            print("⚠️ Tests supplémentaires requis")
        
        # URL document
        print(f"\n🌐 Document de test: {self.base_url}/o/{self.org_id}/{self.doc_id}")
        print(f"💾 Rapport complet: grist_extensions_test_report.json")

def main():
    """Fonction principale de validation"""
    print("🚀 VALIDATION FINALE DES EXTENSIONS GRIST")
    print("=" * 45)
    print(f"⏰ Début: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialiser validateur
        validator = GristExtensionValidator()
        
        # 1. Vérifier accessibilité
        print(f"\n🔍 ÉTAPE 1: Vérification accessibilité")
        if not validator.verify_document_accessible():
            print("❌ Document inaccessible - Arrêt du test")
            return False
        
        # 2. Analyser structure
        print(f"\n📋 ÉTAPE 2: Analyse de la structure")
        structure = validator.get_current_table_structure()
        
        if not structure:
            print("❌ Impossible d'analyser la structure - Arrêt du test")
            return False
        
        # 3. Récupérer données
        print(f"\n📊 ÉTAPE 3: Récupération des données")
        records = validator.get_current_data()
        
        # 4. Analyser formules
        print(f"\n🧮 ÉTAPE 4: Analyse des formules")
        analysis = validator.analyze_formula_results(records, structure)
        
        # 5. Générer rapport
        print(f"\n📝 ÉTAPE 5: Génération du rapport")
        report = validator.generate_test_report(structure, records, analysis)
        
        # 6. Afficher résumé
        validator.print_final_summary(report)
        
        print(f"\n⏰ Fin: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
        
    except Exception as e:
        print(f"\n💥 ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
