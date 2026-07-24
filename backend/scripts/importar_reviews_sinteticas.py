"""
scripts/importar_reviews_sinteticas.py — Sube las reviews sintéticas
(generadas para pruebas/demo) a tu base de datos real.

A diferencia de importar_reviews_manual.py, este JSON ya trae el
`lugar_id` real (el ObjectId de tus 15 lugares existentes), así que no
hace falta crear ni mapear nada — solo se sube directo.

USO:
    1. Levanta el backend normalmente:
         uvicorn backend.main:app --reload
    2. Corre este script (desde la raíz del proyecto):
         python -m backend.scripts.importar_reviews_sinteticas
"""
import json
import os
import sys
from pathlib import Path

import requests

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "reviews_sinteticas.json"


def main():
    if not JSON_PATH.exists():
        print(f"No se encontró el JSON en {JSON_PATH}")
        sys.exit(1)

    with open(JSON_PATH, encoding="utf-8") as f:
        reviews = json.load(f)
    print(f"{len(reviews)} reviews sintéticas cargadas.")

    session = requests.Session()
    try:
        session.get(f"{BASE_URL}/api/health", timeout=5).raise_for_status()
    except requests.RequestException:
        print(f"No se pudo conectar al backend en {BASE_URL}. "
              f"¿Corriste 'uvicorn backend.main:app --reload'?")
        sys.exit(1)

    tam_lote = 40
    insertados = actualizados = 0
    for i in range(0, len(reviews), tam_lote):
        lote = reviews[i:i + tam_lote]
        r = session.post(f"{BASE_URL}/api/recursos/bulk", json=lote)
        if r.status_code >= 400:
            print(f"Error en lote {i}-{i+len(lote)}: {r.status_code} {r.text[:500]}")
            continue
        data = r.json()
        insertados += data.get("insertados", 0)
        actualizados += data.get("actualizados", 0)

    print(f"Listo: {insertados} insertadas, {actualizados} actualizadas/repetidas.")


if __name__ == "__main__":
    main()
