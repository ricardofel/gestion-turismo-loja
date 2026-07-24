"""
scripts/importar_reviews_manual.py — Importa las reseñas de Google Reviews
que ya vienen pre-extraídas en un JSON, hacia la API del proyecto.

Por qué existe este script (y no se usa el conector de SerpApi para esto):
estos datos ya fueron extraídos antes, manualmente, y llegan casi listos
en formato RecursoSchema. Lo único que no calza es:

  1. El campo `formato` viene como "Texto" (con mayúscula) pero el schema
     usa minúsculas: "texto". Se normaliza aquí.
  2. Los `lugar_id` del JSON son códigos propios (ej. "LOC_CISNE_01"), no
     el ObjectId real de un lugar en tu base. Este script resuelve eso
     creando/buscando esos lugares en el catálogo real vía tu propia API
     (/api/lugares) y sustituye el código por el ObjectId real.
  3. `metadata.autor` viene como texto plano y `is_local_guide` viene
     suelto en metricas — se reacomoda a la forma {name, verified} que
     usan los demás endpoints de estadísticas de reviews
     (/api/stats/reviews-resumen, /api/stats/reviews-por-lugar).

Solo importa las reseñas de Google Reviews del JSON — las de YouTube que
trae el mismo archivo se ignoran (para eso ya está el conector en vivo).

USO:
    1. Levanta el backend normalmente:
         uvicorn backend.main:app --reload
    2. Corre este script (desde la raíz del proyecto):
         python -m backend.scripts.importar_reviews_manual
"""
import json
import os
import sys
from pathlib import Path

import requests

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "reviews_manual.json"

# NOTA: nombres inferidos del texto de las reseñas la primera vez que se
# procesó este JSON. Revísalos y ajústalos aquí si alguno no es correcto.
LUGAR_CODIGO_A_DATOS = {
    "LOC_CISNE_01":     {"nombre": "Basílica de la Virgen del Cisne",       "tipo_lugar": "Santuario"},
    "LOC_JIPIRO_02":    {"nombre": "Parque Jipiro",                        "tipo_lugar": "Parque"},
    "LOC_MUSEOMUS_03":  {"nombre": "Museo de la Música",                   "tipo_lugar": "Museo"},
    "LOC_BOTANICO_04":  {"nombre": "Jardín Botánico Reinaldo Espinosa",    "tipo_lugar": "Jardín Botánico"},
    "LOC_ZOO_05":       {"nombre": "Parque Zoológico Orillas del Zamora",  "tipo_lugar": "Zoológico"},
    "LOC_MERCADO_06":   {"nombre": "Mercados del Centro Histórico",        "tipo_lugar": "Mercado"},
    "LOC_TEATRO_07":    {"nombre": "Teatro Benjamín Carrión Mora",         "tipo_lugar": "Teatro"},
    "LOC_PANECILLO_08": {"nombre": "Mirador El Panecillo",                 "tipo_lugar": "Mirador"},
    "LOC_TERMINAL_09":  {"nombre": "Terminal Terrestre de Loja",           "tipo_lugar": "Terminal Terrestre"},
}


def cargar_reviews(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        datos = json.load(f)
    return [d for d in datos if d.get("origen", {}).get("plataforma") == "Google Reviews"]


def asegurar_lugares(session: requests.Session) -> dict[str, str]:
    resp = session.get(f"{BASE_URL}/api/lugares")
    resp.raise_for_status()
    existentes = {l["nombre"].strip().lower(): l["_id"] for l in resp.json()["data"]}

    codigo_a_id: dict[str, str] = {}
    creados = 0
    for codigo, datos in LUGAR_CODIGO_A_DATOS.items():
        clave = datos["nombre"].strip().lower()
        if clave in existentes:
            codigo_a_id[codigo] = existentes[clave]
            continue
        r = session.post(f"{BASE_URL}/api/lugares", json={
            "nombre"        : datos["nombre"],
            "tipo_lugar"    : datos["tipo_lugar"],
            "direccion_texto": datos["nombre"],
        })
        r.raise_for_status()
        nuevo_id = r.json()["id"]
        codigo_a_id[codigo] = nuevo_id
        existentes[clave] = nuevo_id
        creados += 1

    print(f"Lugares: {len(codigo_a_id)} resueltos ({creados} creados, "
          f"{len(codigo_a_id) - creados} ya existían).")
    return codigo_a_id


def transformar(raw: dict, codigo_a_id: dict[str, str]) -> dict:
    origen = dict(raw["origen"])
    origen["formato"] = "reseña"
    origen["plataforma"] = "GoogleReviews"  # el JSON trae "Google Reviews" (con espacio); Atlas exige sin espacio

    meta_orig = raw.get("metadata", {})
    metricas_orig = meta_orig.get("metricas", {})

    doc = {
        "origen"              : origen,
        "estado_procesamiento": raw.get("estado_procesamiento", "Crudo"),
        "fecha_publicacion"   : raw.get("fecha_publicacion"),
        "edicion_id"          : None,
        "lugar_id"            : codigo_a_id.get(raw.get("lugar_id")),
        "metadata": {
            "metricas": {
                "rating": metricas_orig.get("rating"),
                "likes" : 0,
            },
            "autor": {
                "name"    : meta_orig.get("autor", "—"),
                "verified": bool(metricas_orig.get("is_local_guide", False)),
            },
            "texto_original"  : meta_orig.get("texto_original", ""),
            "hashtags"        : meta_orig.get("hashtags", []),
            "urls"            : {"review": ""},
            "idioma"          : "es",
            "es_anuncio"      : False,
            "es_patrocinado"  : False,
            "hora_publicacion": "",
        },
    }
    return doc


def subir_bulk(session: requests.Session, recursos: list[dict]) -> dict:
    r = session.post(f"{BASE_URL}/api/recursos/bulk", json=recursos)
    if r.status_code >= 400:
        print(f"Error subiendo el lote: {r.status_code} {r.text[:800]}")
        return {"insertados": 0, "actualizados": 0}
    return r.json()


def main():
    if not JSON_PATH.exists():
        print(f"No se encontró el JSON en {JSON_PATH}")
        sys.exit(1)

    reviews = cargar_reviews(JSON_PATH)
    print(f"{len(reviews)} reseñas de Google Reviews encontradas en el JSON "
          f"(se ignoran las de YouTube del mismo archivo).")

    session = requests.Session()
    try:
        session.get(f"{BASE_URL}/api/health", timeout=5).raise_for_status()
    except requests.RequestException:
        print(f"No se pudo conectar al backend en {BASE_URL}. "
              f"¿Corriste 'uvicorn backend.main:app --reload'?")
        sys.exit(1)

    codigo_a_id = asegurar_lugares(session)
    transformados = [transformar(r, codigo_a_id) for r in reviews]

    resultado = subir_bulk(session, transformados)
    print(f"Reviews: {resultado.get('insertados', 0)} insertadas, "
          f"{resultado.get('actualizados', 0)} actualizadas/repetidas.")


if __name__ == "__main__":
    main()
