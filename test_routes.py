#!/usr/bin/env python
import logging
import asyncio
logging.basicConfig(level=logging.INFO)

from asgi_dev import app, on_startup

print("\n" + "="*60)
print("Triggering startup event...")
print("="*60)

# Manually trigger startup (since we're not running uvicorn)
try:
    asyncio.run(on_startup())
except:
    # on_startup might not be async, try direct call
    on_startup()

print("\n" + "="*60)
print("Routes mounted in asgi_dev:")
print("="*60)

# Check OpenAPI spec
openapi = app.openapi()
if openapi and 'paths' in openapi:
    paths = sorted(openapi['paths'].keys())
    
    # Show relevant endpoints
    print("\nKey endpoints:")
    for path in paths:
        if '/profile' in path or '/me' in path or '/auth' in path or '/login' in path:
            print(f"  ✅ {path}")
    
    print(f"\nTotal endpoints: {len(paths)}")
    
    print("\n" + "="*60)
    if '/api/v1/profile/' in paths:
        print("✅ Profile endpoint IS MOUNTED")
    else:
        print("❌ Profile endpoint is MISSING") 
        
    if '/api/v1/auth/me' in paths or '/v1/auth/me' in paths:
        print("✅ Auth /me endpoint IS MOUNTED")
    else:
        print("❌ Auth /me endpoint is MISSING")
    
    if '/api/v1/auth/login' in paths:
        print("✅ Auth /login endpoint IS MOUNTED")
    else:
        print("❌ Auth /login endpoint is MISSING")
    print("="*60)
else:
    print("❌ Could not get OpenAPI spec")
