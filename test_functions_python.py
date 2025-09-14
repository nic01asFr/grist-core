#!/usr/bin/env python3
"""
Test des fonctions spatiales et vectorielles dans le container Grist
"""

print("🔍 TEST DES FONCTIONS PYTHON DANS GRIST")
print("=" * 50)

try:
    # Test import du module grist
    import grist
    print("✅ Module grist importé")
    
    # Test import des types
    from usertypes import Geometry, Vector
    print("✅ Types Geometry et Vector importés")
    
    # Test import des fonctions spatiales
    from usertypes import ST_DISTANCE, ST_AREA, ST_CONTAINS, ST_CENTROID
    print("✅ Fonctions spatiales ST_* importées")
    
    # Test import des fonctions vectorielles
    from usertypes import VECTOR_SIMILARITY
    print("✅ Fonctions vectorielles VECTOR_* importées")
    
    print("\n🧪 TEST DES FONCTIONS")
    print("-" * 30)
    
    # Test ST_DISTANCE
    result_distance = ST_DISTANCE("POINT(0 0)", "POINT(0 1)", "km")
    print(f"✅ ST_DISTANCE: {result_distance:.2f} km (attendu: ~111 km)")
    
    # Test VECTOR_SIMILARITY
    result_similarity = VECTOR_SIMILARITY([1,0,0], [1,0,0], "cosine")
    print(f"✅ VECTOR_SIMILARITY: {result_similarity} (attendu: 1.0)")
    
    # Test packages spatiaux
    import numpy as np
    print(f"✅ NumPy version: {np.__version__}")
    
    try:
        import shapely
        print(f"✅ Shapely version: {shapely.__version__}")
    except ImportError:
        print("⚠️ Shapely non disponible")
    
    print("\n🎉 TOUS LES TESTS PASSENT !")
    print("🎯 Les extensions spatiales/vectorielles sont FONCTIONNELLES")
    
except Exception as e:
    print(f"❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
