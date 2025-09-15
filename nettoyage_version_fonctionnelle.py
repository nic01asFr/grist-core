#!/usr/bin/env python3
"""
Script de nettoyage et remplacement progressif des fonctions mock
par l'intégration Python native dans Grist
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

class GristSpatialIntegrator:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.spatial_endpoints_path = os.path.join(self.base_dir, "app/server/lib/SpatialEndpoints.ts")
        self.backup_dir = os.path.join(self.base_dir, "backups")
        
        # Créer le répertoire de backup
        os.makedirs(self.backup_dir, exist_ok=True)
        
        print("🔄 INTÉGRATEUR SPATIAL GRIST")
        print("=" * 50)
        print(f"📁 Répertoire base: {self.base_dir}")
        print(f"📄 Endpoints: {self.spatial_endpoints_path}")
        print(f"💾 Backups: {self.backup_dir}")
        print()
    
    def create_backup(self, description=""):
        """Créer une sauvegarde horodatée"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"SpatialEndpoints_backup_{timestamp}.ts"
        if description:
            backup_name = f"SpatialEndpoints_{description}_{timestamp}.ts"
        
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        if os.path.exists(self.spatial_endpoints_path):
            shutil.copy2(self.spatial_endpoints_path, backup_path)
            print(f"💾 Backup créé: {backup_name}")
            return backup_path
        else:
            print("❌ Fichier SpatialEndpoints.ts non trouvé")
            return None
    
    def check_typescript_compilation(self):
        """Vérifier que TypeScript compile sans erreur"""
        print("🔍 Vérification compilation TypeScript...")
        
        try:
            # Essayer de compiler juste le fichier modifié
            result = subprocess.run(
                ["npx", "tsc", "--noEmit", self.spatial_endpoints_path],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ Compilation TypeScript réussie")
                return True
            else:
                print(f"❌ Erreurs de compilation TypeScript:")
                print(result.stdout)
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Timeout compilation TypeScript")
            return False
        except FileNotFoundError:
            print("⚠️  npx/tsc non trouvé - compilation non vérifiée")
            return True  # On continue quand même
        except Exception as e:
            print(f"❌ Erreur vérification compilation: {e}")
            return False
    
    def test_current_endpoints(self):
        """Tester les endpoints actuels"""
        print("🧪 Test des endpoints existants...")
        
        try:
            # Vérifier si le container tourne
            result = subprocess.run(
                ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}", "--filter", "name=grist-"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "grist-endpoints-test" in result.stdout:
                print("✅ Container grist-endpoints-test actif")
                
                # Test rapide d'un endpoint
                test_result = subprocess.run(
                    ["python", "test_endpoints_spatiaux.py"],
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if "SCORE ENDPOINTS: 8/8" in test_result.stdout:
                    print("✅ Tous les endpoints fonctionnent")
                    return True
                else:
                    print(f"⚠️  Endpoints partiellement fonctionnels")
                    print("📊 Résumé test:")
                    for line in test_result.stdout.split('\n'):
                        if 'SCORE ENDPOINTS:' in line or '✅' in line or '❌' in line:
                            print(f"   {line}")
                    return False
            else:
                print("⚠️  Container non actif - pas de test possible")
                return False
                
        except Exception as e:
            print(f"❌ Erreur test endpoints: {e}")
            return False
    
    def replace_mock_with_python(self, endpoint_name):
        """Remplacer une fonction mock spécifique par l'intégration Python"""
        print(f"🔄 Remplacement {endpoint_name}...")
        
        with open(self.spatial_endpoints_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        replacements = {
            'area': {
                'mock_call': r'const result = 1000000; // Mock area result \(1km²\)',
                'python_call': 'const result = await callPythonFunction(activeDoc, req, \'ST_AREA\', [polygon, unit]);',
                'comment': '// Version mock pour Phase 3 - TODO: Intégrer avec le sandbox Python',
                'new_comment': '// Intégration Python native - Phase 3+'
            },
            'contains': {
                'mock_call': r'const result = true; // Mock containment result',
                'python_call': 'const result = await callPythonFunction(activeDoc, req, \'ST_CONTAINS\', [container, contained]);',
                'comment': '// Version mock pour Phase 3 - TODO: Intégrer avec le sandbox Python',
                'new_comment': '// Intégration Python native - Phase 3+'
            },
            'vector_similarity': {
                'mock_call': r'const result = mockVECTOR_SIMILARITY\(vector1, vector2, method\);',
                'python_call': 'const result = await callPythonFunction(activeDoc, req, \'VECTOR_SIMILARITY\', [vector1, vector2, method]);',
                'comment': '// Version mock pour Phase 3 - TODO: Intégrer avec le sandbox Python',
                'new_comment': '// Intégration Python native - Phase 3+'
            }
        }
        
        if endpoint_name in replacements:
            repl = replacements[endpoint_name]
            
            # Remplacer l'appel mock par l'appel Python
            content = re.sub(repl['mock_call'], repl['python_call'], content)
            
            # Mettre à jour les commentaires
            content = content.replace(repl['comment'], repl['new_comment'])
            
            with open(self.spatial_endpoints_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ {endpoint_name} remplacé par l'intégration Python")
            return True
        else:
            print(f"❌ Endpoint {endpoint_name} non reconnu")
            return False
    
    def build_and_test_cycle(self, description=""):
        """Cycle complet: backup -> vérification -> build -> test"""
        print(f"\n🔄 CYCLE BUILD & TEST: {description}")
        print("-" * 40)
        
        # 1. Backup
        backup_path = self.create_backup(description.lower().replace(' ', '_'))
        if not backup_path:
            return False
        
        # 2. Vérification TypeScript
        if not self.check_typescript_compilation():
            print("❌ Échec compilation - restauration backup")
            shutil.copy2(backup_path, self.spatial_endpoints_path)
            return False
        
        # 3. Build Docker
        print("🐳 Construction image Docker...")
        try:
            build_result = subprocess.run(
                ["docker", "build", "-f", "Dockerfile.temp", "-t", "grist-spatial-native:latest", "."],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes
            )
            
            if build_result.returncode == 0:
                print("✅ Build Docker réussi")
            else:
                print("❌ Échec build Docker:")
                print(build_result.stderr[-1000:])  # Dernières 1000 chars
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Timeout build Docker")
            return False
        except Exception as e:
            print(f"❌ Erreur build Docker: {e}")
            return False
        
        # 4. Redémarrage container
        print("🔄 Redémarrage container...")
        try:
            # Arrêter le container existant
            subprocess.run(
                ["docker", "stop", "grist-endpoints-test"],
                capture_output=True,
                timeout=30
            )
            subprocess.run(
                ["docker", "rm", "grist-endpoints-test"],
                capture_output=True,
                timeout=30
            )
            
            # Démarrer le nouveau
            start_result = subprocess.run(
                ["docker", "run", "-d", "-p", "8888:8484", 
                 "--name", "grist-native-test", "grist-spatial-native:latest"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if start_result.returncode == 0:
                print("✅ Container redémarré")
                
                # Attendre que le service démarre
                print("⏳ Attente démarrage service (15 secondes)...")
                import time
                time.sleep(15)
                
            else:
                print("❌ Échec redémarrage container")
                return False
                
        except Exception as e:
            print(f"❌ Erreur redémarrage: {e}")
            return False
        
        # 5. Test
        print("🧪 Test des endpoints...")
        return self.test_current_endpoints()
    
    def progressive_replacement(self):
        """Remplacement progressif de tous les endpoints mock"""
        print("\n🎯 REMPLACEMENT PROGRESSIF DES MOCK")
        print("=" * 50)
        
        endpoints_to_replace = [
            ('area', 'Endpoint ST_AREA'),
            ('contains', 'Endpoint ST_CONTAINS'),
            ('vector_similarity', 'Endpoint VECTOR_SIMILARITY')
        ]
        
        successful_replacements = []
        failed_replacements = []
        
        for endpoint_key, endpoint_name in endpoints_to_replace:
            print(f"\n🎯 ÉTAPE: {endpoint_name}")
            print("-" * 30)
            
            # Remplacer le mock
            if not self.replace_mock_with_python(endpoint_key):
                failed_replacements.append(endpoint_name)
                continue
            
            # Test du cycle complet
            if self.build_and_test_cycle(f"replace_{endpoint_key}"):
                successful_replacements.append(endpoint_name)
                print(f"✅ {endpoint_name} intégré avec succès")
            else:
                failed_replacements.append(endpoint_name)
                print(f"❌ {endpoint_name} échec d'intégration")
                
                # Restaurer depuis backup
                latest_backup = max([
                    os.path.join(self.backup_dir, f) 
                    for f in os.listdir(self.backup_dir) 
                    if f.endswith('.ts')
                ], key=os.path.getctime)
                
                shutil.copy2(latest_backup, self.spatial_endpoints_path)
                print("🔄 Backup restauré")
        
        # Rapport final
        self.generate_final_report(successful_replacements, failed_replacements)
    
    def generate_final_report(self, successful, failed):
        """Générer le rapport final du remplacement"""
        print("\n" + "=" * 60)
        print("📊 RAPPORT FINAL - INTÉGRATION PYTHON NATIVE")
        print("=" * 60)
        
        total = len(successful) + len(failed)
        success_rate = (len(successful) / total * 100) if total > 0 else 0
        
        print(f"🎯 SCORE INTÉGRATION: {len(successful)}/{total} ({success_rate:.0f}%)")
        print()
        
        if successful:
            print("✅ ENDPOINTS INTÉGRÉS AVEC SUCCÈS:")
            for endpoint in successful:
                print(f"   ✅ {endpoint}")
        
        if failed:
            print("\n❌ ENDPOINTS EN ÉCHEC:")
            for endpoint in failed:
                print(f"   ❌ {endpoint}")
        
        print(f"\n🌐 Instance active: http://127.0.0.1:8888")
        print(f"📖 API Documentation: /api/docs/:docId/spatial/capabilities")
        
        if success_rate == 100:
            print("\n🎉 INTÉGRATION PYTHON NATIVE COMPLÈTE !")
            print("🚀 Tous les endpoints utilisent maintenant le sandbox Python natif")
        elif success_rate >= 50:
            print(f"\n✅ Intégration majoritairement réussie ({success_rate:.0f}%)")
        else:
            print(f"\n⚠️  Intégration partielle ({success_rate:.0f}%)")

    def run_full_integration(self):
        """Exécuter l'intégration complète"""
        print("🚀 DÉMARRAGE INTÉGRATION PYTHON NATIVE")
        print("=" * 60)
        
        # Test initial
        print("📊 État initial:")
        initial_working = self.test_current_endpoints()
        
        if not initial_working:
            print("⚠️  Endpoints initiaux ne fonctionnent pas - vérifiez l'environnement")
            return False
        
        # Remplacement progressif
        self.progressive_replacement()
        
        return True

if __name__ == "__main__":
    integrator = GristSpatialIntegrator()
    success = integrator.run_full_integration()
    
    sys.exit(0 if success else 1)