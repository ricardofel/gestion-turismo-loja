"""
connectors/flickr.py — Conector Flickr con datos reales via Flickr API.

API: Flickr API (100% gratuita, límites generosos ~3600 req/hora)
  https://www.flickr.com/services/api/
  Agrega al .env: FLICKR_API_KEY=...
"""
import os
import requests
from datetime import datetime, timezone
from .base import ConectorBase

FLICKR_API_KEY = os.getenv("FLICKR_API_KEY", "")
BASE_URL = "https://api.flickr.com/services/rest/"
BBOX_LOJA = "-79.35,-4.45,-79.05,-3.75"  # bounding box de Loja, Ecuador

CACHE_TTL_SEG = 3600  # 1 hora — evita repetir la misma búsqueda

_cache: dict[str, tuple[float, list[dict]]] = {}


class ConectorFlickrReal(ConectorBase):
    """Conector real de Flickr API."""
    nombre = "Flickr"

    def extraer_raw(self, tags: list[str]) -> list[dict]:
        if not FLICKR_API_KEY:
            print("⚠️  FLICKR_API_KEY no configurada en backend/.env — sin datos.")
            return []

        texto = " ".join(tags) if tags else "Loja Ecuador turismo"
        cache_key = texto.lower().strip()

        cacheado = _cache.get(cache_key)
        if cacheado and (datetime.now(timezone.utc).timestamp() - cacheado[0]) < CACHE_TTL_SEG:
            return cacheado[1]

        try:
            r = requests.get(BASE_URL, params={
                "method"  : "flickr.photos.search",
                "api_key" : FLICKR_API_KEY,
                "text"    : texto,
                "bbox"    : BBOX_LOJA,
                "extras"  : "description,date_taken,geo,tags,views,count_faves,owner_name,url_m",
                "format"  : "json", "nojsoncallback": 1,
                "per_page": 20, "sort": "relevance",
            }, timeout=10)
            r.raise_for_status()
            data = r.json()

            if data.get("stat") != "ok":
                print(f"⚠️  Flickr API error: {data.get('message', 'desconocido')}")
                return []

            resultados = []
            for p in data.get("photos", {}).get("photo", []):
                lat = p.get("latitude")
                resultados.append({
                    "photo_id"   : p["id"],
                    "title"      : p.get("title", ""),
                    "description": (p.get("description") or {}).get("_content", ""),
                    "owner"      : p.get("ownername", ""),
                    "tags"       : (p.get("tags") or "").split(),
                    "views"      : int(p.get("views", 0) or 0),
                    "favorites"  : int(p.get("count_faves", 0) or 0),
                    "date_taken" : (p.get("datetaken") or "")[:10],
                    "geo"        : {"lat": float(lat), "lon": float(p.get("longitude", 0))}
                                   if lat not in (None, "0") else {},
                    "place"      : "Loja, Ecuador",
                    "url_m"      : p.get("url_m", ""),
                })

            _cache[cache_key] = (datetime.now(timezone.utc).timestamp(), resultados)
            return resultados

        except requests.RequestException as e:
            print(f"⚠️  Error consultando Flickr API: {e}")
            return []

    def extraer(self, tags: list[str]) -> list[dict]:
        return self.extraer_raw(tags)
