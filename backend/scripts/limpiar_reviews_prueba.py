"""
scripts/limpiar_reviews_prueba.py — Borra TODOS los recursos con
plataforma "GoogleReviews" de la base de datos.

Contexto: antes de tener el conector real de SerpApi funcionando, la
colección "recurso" tenía ~760 documentos de GoogleReviews sembrados como
mock (ver docstring de reclasificar_huerfanos.py), más otros ~138 que se
agregaron durante las pruebas de este módulo (118 sintéticas + 20 de un
JSON de ejemplo). Ninguno de esos es una reseña real de Google.

Este script los borra TODOS (sin importar su id_externo), para dejar la
colección limpia antes de correr la extracción real con el conector de
SerpApi.

⚠️ Es una operación destructiva e irreversible. Por seguridad, el script
NO borra nada la primera vez que lo corres — solo te muestra cuántos
documentos borraría. Debes confirmar explícitamente con --confirmar.

Uso:
  # 1. Ver cuántos se borrarían (no borra nada todavía)
  python -m backend.scripts.limpiar_reviews_prueba

  # 2. Confirmar y borrar de verdad
  python -m backend.scripts.limpiar_reviews_prueba --confirmar
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

from ..database import get_col, COL_RECURSO


def main():
    confirmar = "--confirmar" in sys.argv

    col = get_col(COL_RECURSO)
    filtro = {"origen.plataforma": "GoogleReviews"}

    total = col.count_documents(filtro)

    if total == 0:
        print("No hay ningún recurso con plataforma 'GoogleReviews' en la base. Nada que borrar.")
        return

    if not confirmar:
        print(f"Se encontraron {total} recursos con plataforma 'GoogleReviews'.")
        print("Esto incluye tanto los datos mock/sintéticos como cualquier otra cosa "
              "que tenga esa plataforma exacta en este momento.")
        print()
        print("NO se ha borrado nada todavía. Para confirmar el borrado, corre:")
        print("  python -m backend.scripts.limpiar_reviews_prueba --confirmar")
        return

    resultado = col.delete_many(filtro)
    print(f"Listo: se borraron {resultado.deleted_count} recursos de GoogleReviews.")
    print("La colección queda lista para recibir solo datos reales del conector SerpApi.")


if __name__ == "__main__":
    main()
