#!/usr/bin/env python
"""Test signin endpoint"""
import requests
import json

BASE_URL = 'http://127.0.0.1:8000'

print('Testing signin endpoint...')
response = requests.post(
    f'{BASE_URL}/api/auth/signin',
    json={'email': 'test@gmail.com', 'password': 'Test@12345'},
    headers={'Content-Type': 'application/json'}
)

print(f'Status: {response.status_code}')
if response.status_code == 200:
    data = response.json()
    print('✅ SUCCESS!')
    token = data.get('access_token', 'N/A')
    print(f'Got access token: {token[:50]}...')
    print(f'Token type: {data.get("token_type")}')
else:
    print(f'Error: {response.text}')
