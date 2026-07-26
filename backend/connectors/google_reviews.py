"""
connectors/google_reviews.py — Conector Google Reviews vía SerpApi
(motor google_maps_reviews).

API: SerpApi (https://serpapi.com) — servicio de pago por uso, NO requiere
tarjeta de Google Cloud. Agrega al .env: SERPAPI_KEY=tu_key

Soporta VARIAS keys a la vez, separadas por coma:
    SERPAPI_KEY=key1,key2,key3
Cada cuenta gratuita de SerpApi da ~200 búsquedas/mes; con 3 keys (3
cuentas distintas) se dispone de ~600 búsquedas en total. El conector usa
la primera key hasta que se agota (SerpApi responde 429 "Your account has
run out of searches"), y ahí pasa sola a la siguiente, sin intervención
manual. Si una key es inválida (401), también se salta a la siguiente.

A diferencia de YouTube (que busca por palabras clave libres), Google Maps
identifica un lugar por su `data_id` (o `place_id`), no por nombre. Por eso
cada lugar del catálogo debe tener guardado su `google_data_id` (se edita
desde la pantalla Lugares, en el sistema). Sin ese dato no se pueden traer
sus reviews.

Este conector recorre los lugares del catálogo que ya tienen un
`google_data_id` configurado y trae TODAS las reviews de cada uno,
paginando con `next_page_token` hasta que Google/SerpApi ya no devuelva
más páginas. El parámetro `tags` (que en YouTube es una búsqueda libre)
aquí se usa como filtro opcional por nombre de lugar — ej. tags=["cisne"]
solo trae reviews de lugares cuyo nombre contenga "cisne". Si viene
vacío, trae de TODOS los lugares con `google_data_id` configurado.

⚠️ COSTO/CUOTA: SerpApi cobra por búsqueda, y cada página de reviews (20
como máximo) cuenta como una búsqueda. Un lugar con 1,440 reviews implica
~72 búsquedas; hacerlo para varios lugares con muchas reviews puede
consumir una cantidad considerable de tu cuota/créditos. Este conector
NO pone un tope de negocio a propósito (se pidió traer todo el
histórico), solo un límite de seguridad técnico (MAX_PAGINAS_POR_LUGAR)
para evitar que un bug o un bucle de paginación infinito de SerpApi deje
el proceso corriendo para siempre.
"""
import os
import time
import requests
from .base import ConectorBase
from ..database import get_col, COL_LUGAR

_keys_raw = os.getenv("SERPAPI_KEY", "")
SERPAPI_KEYS = [k.strip() for k in _keys_raw.split(",") if k.strip()]
BASE_URL = "https://serpapi.com/search.json"

MAX_PAGINAS_POR_LUGAR = 500   # límite de SEGURIDAD (~10,000 reviews), no de negocio
PAUSA_ENTRE_PAGINAS_SEG = 0.3  # pequeña pausa para no saturar la API


class ConectorGoogleReviews(ConectorBase):
    """Conector real de Google Reviews vía SerpApi (engine google_maps_reviews)."""
    nombre = "GoogleReviews"

    def __init__(self):
        self._indice_key = 0  # cuál de las SERPAPI_KEYS se está usando ahora mismo

    def _key_actual(self) -> str | None:
        if not SERPAPI_KEYS:
            return None
        if self._indice_key >= len(SERPAPI_KEYS):
            return None
        return SERPAPI_KEYS[self._indice_key]

    def _rotar_key(self, motivo: str):
        self._indice_key += 1
        if self._indice_key < len(SERPAPI_KEYS):
            print(f"  ↻ Cambiando a la siguiente SERPAPI_KEY ({motivo}). "
                  f"Ahora usando key #{self._indice_key + 1} de {len(SERPAPI_KEYS)}.")
        else:
            print(f"  ⚠️  Se agotaron las {len(SERPAPI_KEYS)} SERPAPI_KEY configuradas ({motivo}).")

    def _lugares_a_consultar(self, tags: list[str]) -> list[dict]:
        col = get_col(COL_LUGAR)
        lugares = list(col.find({
            "google_data_id": {"$exists": True, "$nin": [None, ""]}
        }))
        if not tags:
            return lugares
        tags_lower = [t.lower() for t in tags]
        return [l for l in lugares if any(t in l.get("nombre", "").lower() for t in tags_lower)]

    def _reviews_de_un_lugar(self, lugar: dict) -> list[dict]:
        resultados = []
        next_page_token = None
        pagina = 0

        while pagina < MAX_PAGINAS_POR_LUGAR:
            key_actual = self._key_actual()
            if key_actual is None:
                print(f"  ⚠️  Sin keys disponibles — se detiene la extracción de '{lugar.get('nombre')}' aquí.")
                break

            params = {
                "engine" : "google_maps_reviews",
                "data_id": lugar["google_data_id"],
                "hl"     : "es",
                "api_key": key_actual,
            }
            if next_page_token:
                params["next_page_token"] = next_page_token

            try:
                r = requests.get(BASE_URL, params=params, timeout=20)
                data = r.json()
            except requests.RequestException as e:
                print(f"⚠️  Error consultando SerpApi para '{lugar.get('nombre')}' "
                      f"(página {pagina + 1}): {e}")
                break

            # 429 = cuota agotada de esta key. 401 = key inválida. En ambos casos,
            # rotamos a la siguiente key SIN perder la página en la que íbamos
            # (next_page_token ya lo tenemos, solo reintentamos con otra key).
            if r.status_code == 429 or (isinstance(data.get("error"), str) and "run out of searches" in data["error"].lower()):
                self._rotar_key(f"key #{self._indice_key + 1} agotó su cuota")
                continue
            if r.status_code == 401:
                self._rotar_key(f"key #{self._indice_key + 1} inválida")
                continue

            if "error" in data:
                print(f"⚠️  SerpApi devolvió error para '{lugar.get('nombre')}' "
                      f"(página {pagina + 1}): {data['error']}")
                break

            reviews_pagina = data.get("reviews") or []
            for rev in reviews_pagina:
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
                    "imagenes"      : rev.get("images", []) or [],
                })

            pagina += 1
            print(f"  · {lugar.get('nombre')}: página {pagina} "
                  f"({len(reviews_pagina)} reviews, {len(resultados)} acumuladas, "
                  f"key #{self._indice_key + 1})")

            next_page_token = (data.get("serpapi_pagination") or {}).get("next_page_token")
            if not next_page_token:
                break  # ya no hay más páginas

            time.sleep(PAUSA_ENTRE_PAGINAS_SEG)

        if pagina >= MAX_PAGINAS_POR_LUGAR:
            print(f"⚠️  '{lugar.get('nombre')}' alcanzó el límite de seguridad de "
                  f"{MAX_PAGINAS_POR_LUGAR} páginas — se detuvo la paginación por si acaso, "
                  f"aunque probablemente aún haya más reviews.")

        return resultados

    def extraer_raw(self, tags: list[str]) -> list[dict]:
        if not SERPAPI_KEYS:
            print("⚠️  SERPAPI_KEY no configurada en backend/.env — sin datos.")
            return []

        lugares = self._lugares_a_consultar(tags)
        if not lugares:
            print("⚠️  Ningún lugar tiene 'google_data_id' configurado (o ninguno coincide con los tags).")
            return []

        print(f"Extrayendo TODAS las reviews de {len(lugares)} lugar(es), "
              f"con {len(SERPAPI_KEYS)} key(s) de SerpApi disponibles. "
              f"Esto puede tardar y consumir bastante cuota de SerpApi.")

        resultados = []
        for lugar in lugares:
            resultados.extend(self._reviews_de_un_lugar(lugar))

        print(f"Total extraído: {len(resultados)} reviews de {len(lugares)} lugar(es).")
        return resultados

    def extraer(self, tags: list[str]) -> list[dict]:
        return self.extraer_raw(tags)
