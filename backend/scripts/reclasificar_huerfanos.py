"""
scripts/reclasificar_huerfanos.py — Backfill de recursos sembrados sin lugar/edición.

Contexto: antes de activar el ETL real, se sembraron ~2200 recursos mock
directo en MongoDB (sin pasar por el pipeline), así que quedaron sin
lugar_id ni edicion_id. Este script los pasa por la misma detección que usa
el ETL real (detectar_lugar / detectar_edicion de backend/etl/pipeline.py)
y actualiza los que encuentren coincidencia. No inventa lugares nuevos —
esa decisión sigue siendo manual (vía el flujo de "lugares nuevos
detectados"), pero sí puede crear ediciones nuevas automáticamente si el
recurso corresponde a un evento conocido en un año sin edición registrada
(mismo comportamiento que el ETL real desde este cambio).

Uso:
  python -m backend.scripts.reclasificar_huerfanos
"""
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

from bson import ObjectId
from pymongo import UpdateOne
from ..database import get_col, COL_RECURSO, COL_LUGAR, COL_EDICION, COL_EVENTO
from ..etl.pipeline import detectar_lugar, detectar_edicion


def main():
    col_recurso = get_col(COL_RECURSO)

    huerfanos = list(col_recurso.find({
        "$or": [{"lugar_id": None}, {"edicion_id": None}]
    }))
    print(f"Recursos huérfanos encontrados: {len(huerfanos)}")

    lugares_catalogo = list(get_col(COL_LUGAR).find({}))
    ediciones        = list(get_col(COL_EDICION).find({}))
    eventos          = list(get_col(COL_EVENTO).find({}))
    ediciones_antes  = len(ediciones)

    ops = []
    con_lugar = con_edicion = sin_coincidencia = 0

    for r in huerfanos:
        cambios = {}

        if not r.get("lugar_id"):
            lugar_id = detectar_lugar(r, lugares_catalogo)
            if lugar_id:
                cambios["lugar_id"] = ObjectId(lugar_id)
                con_lugar += 1

        if not r.get("edicion_id"):
            edicion_id = detectar_edicion(r, ediciones, eventos)
            if edicion_id:
                cambios["edicion_id"] = ObjectId(edicion_id)
                con_edicion += 1

        if cambios:
            ops.append(UpdateOne({"_id": r["_id"]}, {"$set": cambios}))
        else:
            sin_coincidencia += 1

    actualizados = col_recurso.bulk_write(ops, ordered=False).modified_count if ops else 0
    ediciones_creadas = len(ediciones) - ediciones_antes

    print(f"Recursos actualizados      : {actualizados}")
    print(f"  -> con lugar asignado    : {con_lugar}")
    print(f"  -> con edicion asignada  : {con_edicion}")
    print(f"Ediciones nuevas creadas   : {ediciones_creadas}")
    print(f"Recursos sin coincidencia  : {sin_coincidencia}")


if __name__ == "__main__":
    main()
