#!/usr/bin/env python3
"""
Script pour vérifier la structure réelle des IDs de document dans Grist
"""

import requests
import json

def check_document_structure():
    base_url = "http://127.0.0.1:8888"
    api_key = "b1ef763bbf48590f5b55745f94e80d29548d3bd3"
    current_doc_id = "oUzyVYoKocruw9dNgphVm3"
    
    session = requests.Session()
    session.headers.update({
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    })
    
    print("🔍 ANALYSE STRUCTURE DOCUMENT GRIST")
    print("=" * 50)
    
    # 1. Vérifier les organisations
    print("📋 Organisations disponibles...")
    try:
        response = session.get(f"{base_url}/api/orgs")
        if response.ok:
            orgs = response.json()
            print(f"   Organisations trouvées: {len(orgs)}")
            for org in orgs:
                print(f"   📁 Org ID: {org.get('id')} - {org.get('name', 'Sans nom')}")
        else:
            print(f"   ❌ Erreur orgs: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception orgs: {e}")
    
    print()
    
    # 2. Vérifier les espaces de travail
    print("📂 Espaces de travail...")
    try:
        # Essayer avec l'org par défaut "docs"
        response = session.get(f"{base_url}/api/orgs/docs/workspaces")
        if response.ok:
            workspaces = response.json()
            print(f"   Espaces trouvés: {len(workspaces)}")
            for ws in workspaces:
                print(f"   📂 Workspace ID: {ws.get('id')} - {ws.get('name', 'Sans nom')}")
        else:
            print(f"   ❌ Erreur workspaces: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception workspaces: {e}")
    
    print()
    
    # 3. Vérifier les documents dans l'espace de travail
    print("📄 Documents disponibles...")
    try:
        # Essayer de lister les documents de différentes manières
        response = session.get(f"{base_url}/api/orgs/docs/workspaces/0/docs")
        if response.ok:
            docs = response.json()
            print(f"   Documents trouvés: {len(docs)}")
            for doc in docs:
                doc_id = doc.get('id')
                doc_name = doc.get('name', 'Sans nom')
                print(f"   📄 Doc ID: {doc_id} ({type(doc_id)}) - {doc_name}")
        else:
            print(f"   ❌ Erreur docs workspace 0: {response.status_code}")
            
            # Essayer workspace 1
            response = session.get(f"{base_url}/api/orgs/docs/workspaces/1/docs")
            if response.ok:
                docs = response.json()
                print(f"   Documents workspace 1: {len(docs)}")
                for doc in docs:
                    doc_id = doc.get('id')
                    doc_name = doc.get('name', 'Sans nom')
                    print(f"   📄 Doc ID: {doc_id} ({type(doc_id)}) - {doc_name}")
            else:
                print(f"   ❌ Erreur docs workspace 1: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception docs: {e}")
    
    print()
    
    # 4. Vérifier le document actuel
    print(f"🎯 Document actuel: {current_doc_id}")
    try:
        response = session.get(f"{base_url}/api/docs/{current_doc_id}")
        if response.ok:
            doc_info = response.json()
            print("   📊 Informations du document:")
            print(f"      ID: {doc_info.get('id')} ({type(doc_info.get('id'))})")
            print(f"      Nom: {doc_info.get('name')}")
            print(f"      URL ID: {doc_info.get('urlId')}")
            
            # Extraire l'ID numérique s'il existe
            if 'id' in doc_info:
                numeric_id = doc_info['id']
                print(f"\n🔢 ID NUMÉRIQUE À UTILISER: {numeric_id}")
                
                # Tester l'accès avec l'ID numérique
                test_response = session.get(f"{base_url}/api/docs/{numeric_id}")
                if test_response.ok:
                    print(f"   ✅ Accès avec ID numérique: RÉUSSI")
                    return numeric_id
                else:
                    print(f"   ❌ Accès avec ID numérique: ÉCHEC ({test_response.status_code})")
        else:
            print(f"   ❌ Erreur accès document: {response.status_code}")
            print(f"   Détails: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception document: {e}")
    
    return None

if __name__ == "__main__":
    numeric_doc_id = check_document_structure()
    
    if numeric_doc_id:
        print(f"\n🎯 UTILISER L'ID NUMÉRIQUE: {numeric_doc_id}")
        print(f"🔗 URL d'exemple: /api/docs/{numeric_doc_id}/spatial/capabilities")
    else:
        print(f"\n⚠️  Garder l'ID string actuel: oUzyVYoKocruw9dNgphVm3")
