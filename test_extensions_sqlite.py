#!/usr/bin/env python3
"""
Test des extensions SQLite disponibles dans le container Grist
"""

import sqlite3
import os

def test_sqlite_extensions():
    """Test des extensions SQLite disponibles"""
    print("🔍 TEST DES EXTENSIONS SQLITE")
    print("=" * 40)
    
    try:
        # Connexion à SQLite
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        print(f"✅ SQLite version: {sqlite3.sqlite_version}")
        print(f"✅ Python sqlite3 version: {sqlite3.version}")
        
        # Activer le chargement d'extensions
        try:
            conn.enable_load_extension(True)
            print("✅ Extension loading enabled")
        except Exception as e:
            print(f"❌ Cannot enable extensions: {e}")
            return
        
        # Test des extensions spatiales courantes
        extensions_to_test = [
            'mod_spatialite',
            'spatialite',
            'libspatialite.so',
            'mod_spatialite.so',
            '/usr/lib/x86_64-linux-gnu/mod_spatialite.so',
        ]
        
        print("\n🧪 TEST D'EXTENSIONS SPATIALES:")
        spatial_found = False
        
        for ext in extensions_to_test:
            try:
                cursor.execute(f"SELECT load_extension('{ext}')")
                print(f"   ✅ {ext} - CHARGÉE AVEC SUCCÈS")
                spatial_found = True
                break
            except Exception as e:
                print(f"   ❌ {ext} - {str(e)[:50]}...")
        
        if not spatial_found:
            print("   ⚠️ Aucune extension spatiale trouvée")
        
        # Test des fonctions disponibles dans SQLite standard
        print("\n🧮 TEST DES FONCTIONS SQLITE STANDARD:")
        
        test_functions = [
            ("ABS(-5)", "5"),
            ("ROUND(3.14159, 2)", "3.14"),
            ("LENGTH('hello')", "5"),
            ("UPPER('test')", "TEST"),
        ]
        
        for func_test, expected in test_functions:
            try:
                cursor.execute(f"SELECT {func_test}")
                result = cursor.fetchone()[0]
                print(f"   ✅ {func_test} = {result}")
            except Exception as e:
                print(f"   ❌ {func_test} - {e}")
        
        # Test des fonctions géométriques personnalisées (si disponibles)
        print("\n🌍 TEST DES FONCTIONS SPATIALES:")
        
        spatial_functions = [
            "ST_Distance",
            "ST_Area", 
            "ST_Contains",
            "ST_Centroid",
            "GeomFromText",
            "AsText"
        ]
        
        for func in spatial_functions:
            try:
                # Test simple pour voir si la fonction existe
                cursor.execute(f"SELECT {func}('POINT(0 0)', 'POINT(1 1)')")
                result = cursor.fetchone()
                print(f"   ✅ {func} - disponible")
            except Exception as e:
                error_msg = str(e)
                if "no such function" in error_msg:
                    print(f"   ❌ {func} - fonction non trouvée")
                else:
                    print(f"   ⚠️ {func} - {error_msg[:30]}...")
        
        # Test des fonctions vectorielles personnalisées
        print("\n🔢 TEST DES FONCTIONS VECTORIELLES:")
        
        vector_functions = [
            "VECTOR_SIMILARITY",
            "VECTOR_DISTANCE", 
            "COSINE_SIMILARITY",
        ]
        
        for func in vector_functions:
            try:
                cursor.execute(f"SELECT {func}('[1,0,0]', '[0,1,0]')")
                result = cursor.fetchone()
                print(f"   ✅ {func} - disponible")
            except Exception as e:
                error_msg = str(e)
                if "no such function" in error_msg:
                    print(f"   ❌ {func} - fonction non trouvée")
                else:
                    print(f"   ⚠️ {func} - {error_msg[:30]}...")
        
        conn.close()
        
    except Exception as e:
        print(f"💥 ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()

def test_python_spatial_packages():
    """Test des packages Python spatiaux"""
    print("\n🐍 TEST DES PACKAGES PYTHON SPATIAUX")
    print("=" * 40)
    
    packages_to_test = [
        'shapely',
        'geopandas', 
        'pyproj',
        'fiona',
        'rtree',
        'spatialite',
        'pyspatialite',
        'sqlite3',
        'numpy',
    ]
    
    for package in packages_to_test:
        try:
            __import__(package)
            print(f"   ✅ {package} - disponible")
        except ImportError:
            print(f"   ❌ {package} - non installé")
        except Exception as e:
            print(f"   ⚠️ {package} - erreur: {e}")

def check_grist_sandbox():
    """Vérification de l'environnement sandbox Grist"""
    print("\n🏖️ TEST DE L'ENVIRONNEMENT GRIST")
    print("=" * 40)
    
    # Vérifier si on est dans le sandbox
    grist_paths = [
        '/grist',
        '/grist/sandbox',
        '/grist/sandbox/grist',
    ]
    
    for path in grist_paths:
        if os.path.exists(path):
            print(f"   ✅ {path} - trouvé")
            if os.path.isdir(path):
                files = os.listdir(path)[:5]  # Premiers 5 fichiers
                print(f"      Fichiers: {', '.join(files)}")
        else:
            print(f"   ❌ {path} - non trouvé")
    
    # Vérifier les modules Grist
    try:
        import sys
        sys.path.append('/grist/sandbox')
        sys.path.append('/grist/sandbox/grist')
        
        import grist
        print("   ✅ Module grist importé")
        
        # Tenter d'importer les types personnalisés
        try:
            from usertypes import Geometry, Vector
            print("   ✅ Types Geometry et Vector importés")
        except Exception as e:
            print(f"   ❌ Types personnalisés: {e}")
            
        try:
            from usertypes import ST_DISTANCE, VECTOR_SIMILARITY
            print("   ✅ Fonctions ST_DISTANCE et VECTOR_SIMILARITY importées")
        except Exception as e:
            print(f"   ❌ Fonctions personnalisées: {e}")
            
    except Exception as e:
        print(f"   ❌ Module grist: {e}")

if __name__ == "__main__":
    test_sqlite_extensions()
    test_python_spatial_packages() 
    check_grist_sandbox()
    
    print("\n🎯 RÉSUMÉ")
    print("=" * 40)
    print("Ce script teste l'environnement SQLite et Python")
    print("pour identifier les extensions manquantes.")
