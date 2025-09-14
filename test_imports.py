#!/usr/bin/env python3
"""
Test script temporaire pour valider les imports des nouveaux types
"""
import sys
import os

# Ajouter le répertoire sandbox au path
sys.path.insert(0, 'sandbox')

try:
    print("🧪 Test 1: Import des modules...")
    from grist.usertypes import Geometry, Vector, _type_defaults, BaseColumnType
    print("✅ Import Geometry et Vector réussi")
    
    print("\n🧪 Test 2: Vérification type defaults...")
    print(f"✅ Geometry dans _type_defaults: {'Geometry' in _type_defaults}")
    print(f"✅ Vector dans _type_defaults: {'Vector' in _type_defaults}")
    print(f"✅ Geometry default: {_type_defaults.get('Geometry')}")
    print(f"✅ Vector default: {_type_defaults.get('Vector')}")
    
    print("\n🧪 Test 3: Vérification classes...")
    print(f"✅ Type Geometry: {Geometry.typename()}")
    print(f"✅ Type Vector: {Vector.typename()}")
    print(f"✅ Geometry hérite BaseColumnType: {issubclass(Geometry, BaseColumnType)}")
    print(f"✅ Vector hérite BaseColumnType: {issubclass(Vector, BaseColumnType)}")
    
    print("\n🧪 Test 4: Instanciation...")
    geom = Geometry()
    vec = Vector()
    vec_dim = Vector(dimensions=3)
    print(f"✅ Geometry() instanciation: {geom.__class__.__name__}")
    print(f"✅ Vector() instanciation: {vec.__class__.__name__}")
    print(f"✅ Vector(dimensions=3): {vec_dim.dimensions}")
    
    print("\n🧪 Test 5: Conversion de base...")
    # Test Geometry
    point_wkt = Geometry.do_convert('POINT(2.3 48.8)')
    print(f"✅ Geometry WKT: {point_wkt}")
    
    geojson = {'type': 'Point', 'coordinates': [2.3, 48.8]}
    point_from_json = Geometry.do_convert(geojson)
    print(f"✅ Geometry GeoJSON->WKT: {point_from_json}")
    
    # Test Vector
    vec_array = Vector.do_convert([1, 2, 3])
    print(f"✅ Vector array: {vec_array}")
    
    vec_json = Vector.do_convert('[1.0, 2.0, 3.0]')
    print(f"✅ Vector JSON: {vec_json}")
    
    vec_csv = Vector.do_convert('1.0, 2.0, 3.0')
    print(f"✅ Vector CSV: {vec_csv}")
    
    print("\n🎉 TOUS LES TESTS PYTHON PASSENT !")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
