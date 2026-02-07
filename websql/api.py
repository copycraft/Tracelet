# websql / api
import requests
from urllib.parse import urljoin
from websql.settings import settings

# Ensure base API ends with /api/v1 (no trailing slash)
BASE_API = "/api/v1"
base = settings.tracelet_api.rstrip("/")  # e.g. http://127.0.0.1:8000

def _build_url(path: str) -> str:
    # Accept both "/entities" or "entities"
    if not path.startswith("/"):
        path = "/" + path
    return urljoin(f"{base}{BASE_API}/", path.lstrip("/"))

def api_get(path: str):
    url = _build_url(path)
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def api_post(path: str, payload: dict):
    url = _build_url(path)
    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.json()

def api_patch(path: str, payload: dict):
    url = _build_url(path)
    r = requests.patch(url, json=payload)
    r.raise_for_status()
    return r.json()

def api_delete(path: str):
    url = _build_url(path)
    r = requests.delete(url)
    r.raise_for_status()
    return r.json()
