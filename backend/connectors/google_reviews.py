"""
connectors/google_reviews.py — Conector Google Reviews vía SerpApi
(motor google_maps_reviews).

API: SerpApi (https://serpapi.com) — servicio de pago por uso, NO requiere
tarjeta de Google Cloud. Agrega al .env: SERPAPI_KEY=tu_key

A diferencia de YouTube (que busca por palabras clave libres), Google Maps
identifica un lugar por su `data_id` (o `place_id`), no por nombre. Por eso
cada lugar del catálogo debe tener guardado su `google_data_id` (se edita
desde la pantalla Lugares, en el sistema). Sin ese dato no se pueden traer
sus reviews.

Este conector recorre los lugares del catálogo que ya tienen un
`google_data_id` configurado y trae las reviews de cada uno. El parámetro
`tags` (que en YouTube es una búsqueda libre) aquí se usa como filtro
opcional por nombre de lugar — ej. tags=["cisne"] solo trae reviews de
lugares cuyo nombre contenga "cisne". Si viene vacío, trae de TODOS los
lugares con `google_data_id` configurado.

Costo/cuota: 1 búsqueda de SerpApi por lugar, sin paginar (máx. 20 reviews
por lugar y por extracción, que es lo que Google devuelve en la primera
página). Traer más requeriría seguir `next_page_token` y gastaría más
cuota de tu cuenta SerpApi.
"""
import os
import requests
from .base import ConectorBase
from ..database import get_col, COL_LUGAR

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
BASE_URL = "https://serpapi.com/search.json"

MAX_REVIEWS_POR_LUGAR = 20  # una sola página, sin paginar


class ConectorGoogleReviews(ConectorBase):
    """Conector real de Google Reviews vía SerpApi (engine google_maps_reviews)."""
    nombre = "GoogleReviews"

    def _lugares_a_consultar(self, tags: list[str]) -> list[dict]:
        col = get_col(COL_LUGAR)
        lugares = list(col.find({
            "google_data_id": {"$exists": True, "$nin": [None, ""]}
        }))
        if not tags:
            return lugares
        tags_lower = [t.lower() for t in tags]
        return [l for l in lugares if any(t in l.get("nombre", "").lower() for t in tags_lower)]

    def extraer_raw(self, tags: list[str]) -> list[dict]:
        if not SERPAPI_KEY:
            print("⚠️  SERPAPI_KEY no configurada en backend/.env — sin datos.")
            return []

        lugares = self._lugares_a_consultar(tags)
        if not lugares:
            print("⚠️  Ningún lugar tiene 'google_data_id' configurado (o ninguno coincide con los tags).")
            return []

        resultados = []
        for lugar in lugares:
            try:
                r = requests.get(BASE_URL, params={
                    "engine" : "google_maps_reviews",
                    "data_id": lugar["google_data_id"],
                    "hl"     : "es",
                    "api_key": SERPAPI_KEY,
                }, timeout=15)
                r.raise_for_status()
                data = r.json()
            except requests.RequestException as e:
                print(f"⚠️  Error consultando SerpApi para '{lugar.get('nombre')}': {e}")
                continue

            if "error" in data:
                print(f"⚠️  SerpApi devolvió error para '{lugar.get('nombre')}': {data['error']}")
                continue

            for rev in (data.get("reviews") or [])[:MAX_REVIEWS_POR_LUGAR]:
                usuario = rev.get("user", {}) or {}
                resultados.append({
                    "review_id"     : rev.get("review_id", ""),
                    "lugar_id"      : str(lugar["_id"]),
                    "lugar_nombre"  : lugar.get("nombre", ""),
                    "autor"         : usuario.get("name", "—"),
                    "es_local_guide": bool(usuario.get("local_guide", False)),
                    "rating"        : rev.get("rating"),
                    "texto"         : rev.get("snippet", "") or "",
                    "likes"         : rev.get("likes", 0) or 0,
                    "fecha_iso"     : rev.get("iso_date"),
                    "link"          : rev.get("link", ""),
                })

        return resultados

    def extraer(self, tags: list[str]) -> list[dict]:
        return self.extraer_raw(tags)
