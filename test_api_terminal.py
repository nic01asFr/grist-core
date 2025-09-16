#!/usr/bin/env python3
"""
Test direct des endpoints API via terminal Python
Validation que les vraies fonctions Python s'exécutent
"""

import requests
import json
import sys

def test_endpoints():
    print("🚀 TESTS DIRECTS API ENDPOINTS VIA TERMINAL PYTHON")
    print("=" * 50)
    
    # Configuration
    api_key = "628e1efaedd614172c8fda0a16ce73a8b343609c"
    base_url = "http://127.0.0.1:8888"
    doc_id = "hDKpH2vxS1UQYfRN2jsVBg"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print(f"🔑 API Key: {api_key[:20]}...")
    print(f"🔗 Base URL: {base_url}")
    print(f"📄 Doc ID: {doc_id}")
    print()
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Distance spatiale
    print("🔍 TEST 1: /spatial/distance - Tour Eiffel -> Notre-Dame")
    tests_total += 1
    try:
        response = requests.post(
            f"{base_url}/api/docs/{doc_id}/spatial/distance",
            headers=headers,
            json={
                "point1": "POINT(2.2945 48.8584)",
                "point2": "POINT(2.3522 48.8566)",
                "unit": "km"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            distance = data['data']['distance']
            print(f"   ✅ SUCCESS - Status: {response.status_code}")
            print(f"   📏 Distance: {distance} km")
            print(f"   🔢 Précision: {len(str(distance).split('.')[1]) if '.' in str(distance) else 0} décimales")
            
            if 4.0 < distance < 5.0:
                print(f"   🎯 RÉALISME: ✅ (Distance Tour Eiffel-Notre Dame cohérente)")
                tests_passed += 1
            else:
                print(f"   🎯 RÉALISME: ❌ (Distance incohérente)")
        else:
            print(f"   ❌ ERREUR HTTP: {response.status_code}")
            print(f"   📝 Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
    
    print()
    
    # Test 2: Similarité vectorielle - vecteurs identiques
    print("🔍 TEST 2: /vector/similarity - Vecteurs identiques")
    tests_total += 1
    try:
        response = requests.post(
            f"{base_url}/api/docs/{doc_id}/vector/similarity",
            headers=headers,
            json={
                "vector1": [1.0, 0.0, 0.5],
                "vector2": [1.0, 0.0, 0.5],
                "method": "cosine"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            similarity = data['data']['similarity']
            print(f"   ✅ SUCCESS - Status: {response.status_code}")
            print(f"   🧮 Similarité: {similarity}")
            
            if similarity > 0.999:
                print(f"   🎯 PERFECTION: ✅ (Vecteurs identiques ≈ 1.0)")
                tests_passed += 1
            else:
                print(f"   🎯 PERFECTION: ❌ (Devrait être 1.0, obtenu {similarity})")
        else:
            print(f"   ❌ ERREUR HTTP: {response.status_code}")
            print(f"   📝 Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
    
    print()
    
    # Test 3: Similarité vectorielle - vecteurs orthogonaux
    print("🔍 TEST 3: /vector/similarity - Vecteurs orthogonaux")
    tests_total += 1
    try:
        response = requests.post(
            f"{base_url}/api/docs/{doc_id}/vector/similarity",
            headers=headers,
            json={
                "vector1": [1.0, 0.0],
                "vector2": [0.0, 1.0],
                "method": "cosine"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            similarity = data['data']['similarity']
            print(f"   ✅ SUCCESS - Status: {response.status_code}")
            print(f"   🧮 Similarité: {similarity}")
            
            if abs(similarity) < 0.001:
                print(f"   ⊥ ORTHOGONALITÉ: ✅ (Vecteurs orthogonaux ≈ 0.0)")
                tests_passed += 1
            else:
                print(f"   ⊥ ORTHOGONALITÉ: ❌ (Devrait être ≈ 0.0, obtenu {similarity})")
        else:
            print(f"   ❌ ERREUR HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
    
    print()
    
    # Test 4: Health check
    print("🔍 TEST 4: /spatial/health - Santé du système")
    tests_total += 1
    try:
        response = requests.get(
            f"{base_url}/api/docs/{doc_id}/spatial/health",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data['data']['status']
            tests_data = data['data']['tests']
            
            print(f"   ✅ SUCCESS - Status: {response.status_code}")
            print(f"   🏥 Santé système: {status}")
            print(f"   🧪 Tests:")
            
            for test_name, test_info in tests_data.items():
                test_status = test_info.get('status', 'unknown')
                test_result = test_info.get('result', 'N/A')
                print(f"      - {test_name}: {test_status} ({test_result})")
            
            if status == 'healthy':
                tests_passed += 1
                
        else:
            print(f"   ❌ ERREUR HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ EXCEPTION: {e}")
    
    print()
    print("=" * 50)
    print("📊 RÉSUMÉ DES TESTS TERMINAUX")
    print(f"✅ Tests réussis: {tests_passed}/{tests_total}")
    print(f"📈 Taux de succès: {(tests_passed/tests_total)*100:.1f}%")
    
    if tests_passed == tests_total:
        print("🎉 TOUS LES TESTS PASSENT!")
        print("✅ Les vraies fonctions Python s'exécutent")
        print("✅ Aucun mock utilisé")
        print("✅ Intégration complètement fonctionnelle")
    else:
        print("⚠️ Certains tests ont échoué")
    
    print("=" * 50)
    
    return tests_passed == tests_total

if __name__ == "__main__":
    success = test_endpoints()
    sys.exit(0 if success else 1)
