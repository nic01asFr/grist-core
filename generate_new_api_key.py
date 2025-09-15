#!/usr/bin/env python3
"""
Aide pour générer une nouvelle API key pour le container
"""

import requests
import json

def check_instance_access():
    base_url = "http://127.0.0.1:8888"
    
    print("🔑 GÉNÉRATION NOUVELLE API KEY")
    print("=" * 40)
    print(f"🌐 Instance: {base_url}")
    print()
    
    # Test accès sans API key à la page d'accueil
    try:
        response = requests.get(base_url, timeout=10)
        if response.ok:
            print(f"✅ Instance accessible sur {base_url}")
            print("📋 Instructions pour générer une nouvelle API key:")
            print()
            print("1. 🌐 Ouvrir: http://127.0.0.1:8888")
            print("2. 🔐 Créer un compte ou se connecter")
            print("3. ⚙️  Aller dans Profile Settings")
            print("4. 🔑 Générer une nouvelle API Key")
            print("5. 📄 Créer un nouveau document de test")
            print()
            print("📊 Une fois fait, mettre à jour:")
            print("   - API Key dans test_endpoints_spatiaux.py")
            print("   - Document ID (utiliser l'ID numérique)")
            print()
            return True
        else:
            print(f"❌ Instance non accessible: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
        return False
    
def test_direct_endpoint():
    base_url = "http://127.0.0.1:8888"
    
    print("🧪 TEST ENDPOINT SANS AUTHENTIFICATION")
    print("-" * 40)
    
    # Test de l'endpoint capabilities sans API key
    try:
        response = requests.get(f"{base_url}/api/docs/2/spatial/capabilities", timeout=10)
        print(f"📋 GET /api/docs/2/spatial/capabilities")
        print(f"   Status: {response.status_code}")
        if response.ok:
            data = response.json()
            print(f"   ✅ Endpoint accessible sans API key!")
            print(f"   📊 Version: {data.get('data', {}).get('version', 'N/A')}")
            return True
        else:
            print(f"   ❌ Erreur: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur de connexion: {e}")
        return False

if __name__ == "__main__":
    print("🔍 DIAGNOSTIC ACCÈS INSTANCE GRIST")
    print("=" * 50)
    
    # Vérifier l'accès de base
    if check_instance_access():
        print()
        # Tester l'endpoint sans authentification
        test_direct_endpoint()
    
    print()
    print("🎯 ACTIONS RECOMMANDÉES:")
    print("1. Vérifier que l'instance est accessible sur http://127.0.0.1:8888")
    print("2. Générer une nouvelle API key depuis l'interface web")
    print("3. Créer un nouveau document et noter son ID numérique")
    print("4. Mettre à jour le script de test avec les nouveaux credentials")
