"""
routes/catalogos.py — Endpoint de catálogos resumidos (Eventos, Ediciones, Lugares).

El CRUD completo de estas colecciones vive en catalogos_crud.py — este módulo
solo expone la vista compacta id/nombre que usa el frontend para selectores.
"""
from fastapi import APIRouter, HTTPException
from ..database import get_col, serializar_doc
from ..database import COL_EVENTO, COL_EDICION, COL_LUGAR

router = APIRouter(prefix="/api", tags=["Catálogos"])

# ── Helper genérico ──────────────────────────────────────
def _nombre_doc(d: dict) -> str:
    """Extrae el nombre para mostrar, dependiendo del tipo de documento."""
    return d.get("nombre") or d.get("nombre_oficial") or str(d.get("anio", "—"))


@router.get("/catalogos/{tipo}")
def obtener_catalogo(tipo: str):
    """
    tipo = 'lugares' | 'eventos' | 'ediciones'
    Devuelve lista id/nombre para llenar selectores en el frontend.
    """
    mapa = {"lugares": COL_LUGAR, "eventos": COL_EVENTO, "ediciones": COL_EDICION}
    if tipo not in mapa:
        raise HTTPException(status_code=404, detail=f"Catálogo '{tipo}' no existe.")

    docs  = [serializar_doc(d) for d in get_col(mapa[tipo]).find({})]
    items = [{"id": d["_id"], "nombre": _nombre_doc(d)} for d in docs]
    return {"exito": True, "tipo": tipo, "total": len(items), "data": items}
