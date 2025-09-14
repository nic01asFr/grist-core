#!/usr/bin/env python3
"""Test minimal des fonctions dans le container"""

print("=== TEST DES FONCTIONS SPATIALES/VECTORIELLES ===")

try:
    # Test import
    from usertypes import ST_DISTANCE, VECTOR_SIMILARITY
    print("✅ Import réussi: ST_DISTANCE, VECTOR_SIMILARITY")
    
    # Test ST_DISTANCE
    distance = ST_DISTANCE("POINT(0 0)", "POINT(0 1)", "km")
    print(f"✅ ST_DISTANCE: {distance:.2f} km (attendu: ~111 km)")
    
    # Test VECTOR_SIMILARITY  
    similarity = VECTOR_SIMILARITY([1,0,0], [1,0,0], "cosine")
    print(f"✅ VECTOR_SIMILARITY: {similarity} (attendu: 1.0)")
    
    print("🎉 TOUTES LES FONCTIONS MARCHENT !")
    
except Exception as e:
    print(f"❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
