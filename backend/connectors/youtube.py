"""
connectors/youtube.py — Conector YouTube con datos reales via YouTube Data API v3.

API: YouTube Data API v3 (gratuita, 10,000 unidades/día)
  https://console.cloud.google.com/ → APIs & Services → YouTube Data API v3
  Agrega al .env: YOUTUBE_API_KEY=AIza...

Costo de cuota por extracción: 100 (search.list) + 1 (videos.list) = 101 unidades.
Con 10,000 unidades/día alcanzan ~99 extracciones diarias. Se corta en
CUOTA_DIARIA_MAXIMA para dejar margen y no dejar la cuota en 0 el resto del día.
"""
import os
import re
import requests
from datetime import datetime, timezone, date
from .base import ConectorBase

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
BASE_URL = "https://www.googleapis.com/youtube/v3"

CUOTA_DIARIA_MAXIMA = 9000   # de 10,000 reales — deja margen de seguridad
COSTO_SEARCH = 100
COSTO_VIDEOS = 1

CACHE_TTL_SEG = 3600  # 1 hora — evita repetir la misma búsqueda y gastar cuota

_cuota = {"fecha": None, "unidades": 0}
_cache: dict[str, tuple[float, list[dict]]] = {}


def _hoy() -> str:
    return date.today().isoformat()


def _registrar_uso(unidades: int) -> None:
    if _cuota["fecha"] != _hoy():
        _cuota["fecha"] = _hoy()
        _cuota["unidades"] = 0
    _cuota["unidades"] += unidades


def _cuota_disponible(unidades_necesarias: int) -> bool:
    if _cuota["fecha"] != _hoy():
        return True
    return _cuota["unidades"] + unidades_necesarias <= CUOTA_DIARIA_MAXIMA


def _parse_duracion_iso(duracion: str) -> int:
    """Convierte una duración ISO 8601 ('PT4M13S') a segundos."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duracion or "")
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


class ConectorYouTubeReal(ConectorBase):
    """Conector real de YouTube Data API v3."""
    nombre = "YouTube"

    def extraer_raw(self, tags: list[str]) -> list[dict]:
        if not YOUTUBE_API_KEY:
            print("⚠️  YOUTUBE_API_KEY no configurada en backend/.env — sin datos.")
            return []

        query = f"{' '.join(tags)} Loja Ecuador" if tags else "Loja Ecuador turismo"
        cache_key = query.lower().strip()

        cacheado = _cache.get(cache_key)
        if cacheado and (datetime.now(timezone.utc).timestamp() - cacheado[0]) < CACHE_TTL_SEG:
            return cacheado[1]

        if not _cuota_disponible(COSTO_SEARCH + COSTO_VIDEOS):
            print(f"⚠️  Cuota diaria de YouTube agotada ({_cuota['unidades']} unidades usadas) — intenta mañana.")
            return []

        try:
            r_search = requests.get(f"{BASE_URL}/search", params={
                "part": "snippet", "q": query, "type": "video",
                "maxResults": 20, "regionCode": "EC", "relevanceLanguage": "es",
                "key": YOUTUBE_API_KEY,
            }, timeout=10)
            r_search.raise_for_status()
            _registrar_uso(COSTO_SEARCH)

            ids = [item["id"]["videoId"] for item in r_search.json().get("items", [])]
            if not ids:
                _cache[cache_key] = (datetime.now(timezone.utc).timestamp(), [])
                return []

            r_videos = requests.get(f"{BASE_URL}/videos", params={
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(ids), "key": YOUTUBE_API_KEY,
            }, timeout=10)
            r_videos.raise_for_status()
            _registrar_uso(COSTO_VIDEOS)

            resultados = []
            for v in r_videos.json().get("items", []):
                sn = v.get("snippet", {})
                st = v.get("statistics", {})
                cd = v.get("contentDetails", {})
                resultados.append({
                    "video_id"   : v["id"],
                    "title"      : sn.get("title", ""),
                    "channel"    : sn.get("channelTitle", ""),
                    "description": sn.get("description", ""),
                    "views"      : int(st.get("viewCount", 0) or 0),
                    "likes"      : int(st.get("likeCount", 0) or 0),
                    "comments"   : int(st.get("commentCount", 0) or 0),
                    "date"       : sn.get("publishedAt", "")[:10],
                    "tags"       : sn.get("tags", []),
                    "url"        : f"https://youtu.be/{v['id']}",
                    "thumbnail"  : sn.get("thumbnails", {}).get("high", {}).get("url", ""),
                    "duration"   : _parse_duracion_iso(cd.get("duration", "")),
                })

            _cache[cache_key] = (datetime.now(timezone.utc).timestamp(), resultados)
            return resultados

        except requests.RequestException as e:
            print(f"⚠️  Error consultando YouTube API: {e}")
            return []

    def extraer(self, tags: list[str]) -> list[dict]:
        return self.extraer_raw(tags)
