#!/usr/bin/env python3
"""
Test des différentes structures d'URL pour accéder aux documents via workspace
"""

import requests

def test_workspace_access():
    base_url = "http://127.0.0.1:8888"
    api_key = "b1ef763bbf48590f5b55745f94e80d29548d3bd3"
    workspace_id = 2  # ID numérique trouvé
    doc_string_id = "oUzyVYoKocruw9dNgphVm3"
    
    session = requests.Session()
    session.headers.update({
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    })
    
    print("🧪 TEST STRUCTURES URL WORKSPACE/DOCUMENT")
    print("=" * 50)
    
    # Test 1: Documents dans workspace via API
    print(f"📂 Test 1: Workspace {workspace_id} documents...")
    try:
        response = session.get(f"{base_url}/api/orgs/docs/workspaces/{workspace_id}/docs")
        if response.ok:
            docs = response.json()
            print(f"   ✅ Documents trouvés: {len(docs)}")
            for doc in docs:
                print(f"      📄 {doc.get('id')} - {doc.get('name')}")
                
                # Récupérer l'ID numérique interne si disponible
                if 'docId' in doc:
                    print(f"         docId: {doc.get('docId')}")
                    
        else:
            print(f"   ❌ Erreur: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print()
    
    # Test 2: Accès direct document
    print(f"📄 Test 2: Accès document direct...")
    test_urls = [
        f"/api/docs/{doc_string_id}",
        f"/api/docs/{workspace_id}",  # Si l'ID workspace était le doc ID
        f"/api/orgs/docs/workspaces/{workspace_id}/docs/{doc_string_id}",
    ]
    
    for url in test_urls:
        try:
            response = session.get(f"{base_url}{url}")
            print(f"   {url}")
            if response.ok:
                print(f"      ✅ Status: {response.status_code}")
            else:
                print(f"      ❌ Status: {response.status_code}")
        except Exception as e:
            print(f"      ❌ Exception: {e}")
    
    print()
    
    # Test 3: Capabilities endpoint avec différentes structures
    print(f"🔌 Test 3: Endpoints capabilities...")
    capability_urls = [
        f"/api/docs/{doc_string_id}/spatial/capabilities",
        f"/api/docs/{workspace_id}/spatial/capabilities", 
    ]
    
    for url in capability_urls:
        try:
            response = session.get(f"{base_url}{url}")
            print(f"   {url}")
            if response.ok:
                data = response.json()
                print(f"      ✅ Status: {response.status_code}")
                print(f"      📊 Version: {data.get('data', {}).get('version', 'N/A')}")
            else:
                print(f"      ❌ Status: {response.status_code}")
        except Exception as e:
            print(f"      ❌ Exception: {e}")
    
    print()
    
    # Recommandation finale
    print("🎯 RECOMMANDATION:")
    print(f"   📄 Document ID à utiliser: {doc_string_id}")
    print(f"   📂 Workspace ID: {workspace_id}")
    print(f"   🔗 URL Spatial API: /api/docs/{doc_string_id}/spatial/*")

if __name__ == "__main__":
    test_workspace_access()
