"""
routes/stats.py — Endpoints de estadísticas reales para el dashboard Home.
"""
from fastapi import APIRouter
from bson import ObjectId
from ..database import get_col, COL_RECURSO, COL_EVENTO, COL_EDICION, COL_LUGAR

router = APIRouter(prefix="/api/stats", tags=["Estadísticas"])


@router.get("/resumen")
def resumen_general():
    """
    KPIs principales: total, distribución por plataforma y por estado.
    """
    col = get_col(COL_RECURSO)

    # Por plataforma
    por_plataforma = list(col.aggregate([
        {"$group": {"_id": "$origen.plataforma", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))

    # Por estado
    por_estado = list(col.aggregate([
        {"$group": {"_id": "$estado_procesamiento", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))

    # Fuentes activas = plataformas con al menos 1 recurso
    fuentes_activas = [p["_id"] for p in por_plataforma if p["_id"]]

    return {
        "exito": True,
        "fuentes_activas": len(fuentes_activas),
        "fuentes_nombres": fuentes_activas,
        "por_plataforma": [
            {"plataforma": p["_id"] or "Desconocida", "count": p["count"]}
            for p in por_plataforma if p["_id"]
        ],
        "por_estado": [
            {"estado": e["_id"] or "Desconocido", "count": e["count"]}
            for e in por_estado if e["_id"]
        ],
    }


@router.get("/ingesta-mensual")
def ingesta_mensual():
    """
    Agrupa recursos por mes según fecha_publicacion (YYYY-MM-DD).
    Devuelve todos los meses con datos.
    """
    col = get_col(COL_RECURSO)

    resultado = list(col.aggregate([
        {"$match": {"fecha_publicacion": {"$ne": None, "$type": "string", "$regex": r"^\d{4}-\d{2}"}}},
        {"$project": {
            "anio": {"$substr": ["$fecha_publicacion", 0, 4]},
            "mes":  {"$substr": ["$fecha_publicacion", 5, 2]},
        }},
        {"$group": {
            "_id":   {"anio": "$anio", "mes": "$mes"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.anio": 1, "_id.mes": 1}},
        {"$limit": 24}
    ]))

    MESES_ES = {
        "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr",
        "05": "May", "06": "Jun", "07": "Jul", "08": "Ago",
        "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic"
    }

    return {
        "exito": True,
        "data": [
            {
                "periodo": f"{r['_id']['anio']}-{r['_id']['mes']}",
                "label":   f"{MESES_ES.get(r['_id']['mes'], r['_id']['mes'])} {r['_id']['anio']}",
                "count":   r["count"]
            }
            for r in resultado
        ]
    }


@router.get("/eventos")
def stats_eventos():
    """
    Por cada evento: cuántos recursos tiene (via edicion_id),
    cuántas ediciones tiene y si es el más popular.
    """
    col_recurso = get_col(COL_RECURSO)
    col_edicion = get_col(COL_EDICION)
    col_evento  = get_col(COL_EVENTO)

    # Todos los eventos
    eventos = list(col_evento.find({}))

    resultado = []
    for ev in eventos:
        ev_id = ev["_id"]

        # Ediciones de este evento
        ediciones = list(col_edicion.find({"evento_id": ev_id}, {"_id": 1, "anio": 1}))
        edicion_ids = [e["_id"] for e in ediciones]

        # Recursos con alguna de esas ediciones
        recursos_count = 0
        if edicion_ids:
            recursos_count = col_recurso.count_documents(
                {"edicion_id": {"$in": edicion_ids}}
            )

        resultado.append({
            "id":               str(ev_id),
            "nombre":           ev.get("nombre_oficial", ""),
            "categoria":        ev.get("categoria", ""),
            "activo":           ev.get("activo", True),
            "ediciones":        len(ediciones),
            "anios_ediciones":  sorted([e.get("anio", 0) for e in ediciones], reverse=True),
            "recursos":         recursos_count,
        })

    # Ordenar por recursos descendente
    resultado.sort(key=lambda x: x["recursos"], reverse=True)

    # Marcar el más popular
    if resultado and resultado[0]["recursos"] > 0:
        resultado[0]["es_mas_popular"] = True

    return {"exito": True, "data": resultado}
