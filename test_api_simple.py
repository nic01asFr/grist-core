#!/usr/bin/env python3
"""Test API simple"""

import requests

base_url = "http://127.0.0.1:8888"
api_key = "3816d9d8e74c8bfd9abd3384b1019dc48d5605b5"

print("🔍 Test API Grist...")

# 1. Test accès web
try:
    response = requests.get(f"{base_url}/o/docs/", timeout=10)
    print(f"Web interface: {response.status_code}")
except Exception as e:
    print(f"❌ Web error: {e}")

# 2. Test API sans auth
try:
    response = requests.get(f"{base_url}/api/orgs", timeout=10)
    print(f"API sans auth: {response.status_code} - {response.text[:100]}")
except Exception as e:
    print(f"❌ API sans auth error: {e}")

# 3. Test API avec auth
try:
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    response = requests.get(f"{base_url}/api/orgs", headers=headers, timeout=10)
    print(f"API avec auth: {response.status_code} - {response.text[:100]}")
except Exception as e:
    print(f"❌ API avec auth error: {e}")

# 4. Test workspaces
try:
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    response = requests.get(f"{base_url}/api/workspaces", headers=headers, timeout=10)
    print(f"Workspaces: {response.status_code} - {response.text[:100]}")
except Exception as e:
    print(f"❌ Workspaces error: {e}")
