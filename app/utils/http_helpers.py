from __future__ import annotations

from typing import Any, Dict, Optional

import httpx


async def safe_get_json(url: str, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
    """
    Outbound GET expecting JSON.
    Returns dict on success, None on any failure.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            if resp.status_code < 200 or resp.status_code >= 300:
                return None
            ct = resp.headers.get("content-type", "")
            if "application/json" not in ct:
                return None
            return resp.json()
    except httpx.RequestError:
        return None
    except Exception:
        return None


async def safe_post_json(url: str, payload: Dict[str, Any], timeout: float = 5.0) -> Optional[Dict[str, Any]]:
    """
    Outbound POST expecting JSON response.
    Returns dict on success, None on any failure.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code < 200 or resp.status_code >= 300:
                return None
            ct = resp.headers.get("content-type", "")
            if "application/json" not in ct:
                return None
            return resp.json()
    except httpx.RequestError:
        return None
    except Exception:
        return None
