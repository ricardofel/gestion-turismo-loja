"""
routes/catalogos_crud.py — CRUD completo para Lugares, Eventos y Ediciones.
"""
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from ..database import get_col, serializar_doc, oid, ahora_utc
from ..database import COL_LUGAR, COL_EVENTO, COL_EDICION, COL_RECURSO

router = APIRouter(prefix="/api", tags=["Catálogos CRUD"])


def _oid_or_none(val):
    if not val: return None
    try: return ObjectId(str(val))
    except: return None


# ══════════════════════════════════════════════
# LUGARES
# ══════════════════════════════════════════════

@router.get("/lugares")
def listar_lugares():
    docs = [serializar_doc(d) for d in get_col(COL_LUGAR).find({}).sort("nombre", 1)]
    return {"exito": True, "total": len(docs), "data": docs}


@router.post("/lugares")
def crear_lugar(lugar: dict):
    if not lugar.get("nombre", "").strip():
        raise HTTPException(status_code=400, detail="El campo 'nombre' es obligatorio.")

    # Construir coordenadas GeoJSON solo si vienen ambos valores
    lat = lugar.pop("lat", None)
    lon = lugar.pop("lon", None)
    if lat is not None and lon is not None:
        try:
            lugar["coordenadas_geo"] = {
                "type": "Point",
                "coordinates": [float(lon), float(lat)]
            }
        except (ValueError, TypeError):
            lugar["coordenadas_geo"] = None
    else:
        lugar["coordenadas_geo"] = None

    lugar["creado_en"] = ahora_utc()
    res = get_col(COL_LUGAR).insert_one(lugar)
    return {"exito": True, "id": str(res.inserted_id)}


@router.put("/lugares/{id}")
def actualizar_lugar(id: str, cambios: dict):
    cambios.pop("_id", None)
    cambios.pop("creado_en", None)

    lat = cambios.pop("lat", None)
    lon = cambios.pop("lon", None)
    if lat is not None and lon is not None:
        try:
            cambios["coordenadas_geo"] = {
                "type": "Point",
                "coordinates": [float(lon), float(lat)]
            }
        except (ValueError, TypeError):
            pass

    cambios["actualizado_en"] = ahora_utc()
    res = get_col(COL_LUGAR).update_one({"_id": oid(id)}, {"$set": cambios})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lugar no encontrado.")
    return {"exito": True}


@router.delete("/lugares/{id}")
def eliminar_lugar(id: str):
    # Contar recursos que usan este lugar
    recursos_afectados = get_col(COL_RECURSO).count_documents(
        {"lugar_id": _oid_or_none(id)}
    )
    get_col(COL_LUGAR).delete_one({"_id": oid(id)})
    # Desasignar lugar de recursos huérfanos
    if recursos_afectados:
        get_col(COL_RECURSO).update_many(
            {"lugar_id": _oid_or_none(id)},
            {"$set": {"lugar_id": None}}
        )
    return {"exito": True, "recursos_desvinculados": recursos_afectados}


@router.get("/lugares/{id}/impacto")
def impacto_lugar(id: str):
    """Cuántos recursos quedarían huérfanos si se elimina este lugar."""
    n = get_col(COL_RECURSO).count_documents({"lugar_id": _oid_or_none(id)})
    return {"recursos_afectados": n}


# ══════════════════════════════════════════════
# EVENTOS
# ══════════════════════════════════════════════

@router.get("/eventos")
def listar_eventos():
    docs = [serializar_doc(d) for d in get_col(COL_EVENTO).find({}).sort("nombre_oficial", 1)]
    return {"exito": True, "total": len(docs), "data": docs}


@router.post("/eventos")
def crear_evento(evento: dict):
    if not evento.get("nombre_oficial", "").strip():
        raise HTTPException(status_code=400, detail="El campo 'nombre_oficial' es obligatorio.")
    evento.setdefault("activo", True)
    evento.setdefault("palabras_clave", [])
    evento.setdefault("categoria", "")
    evento.setdefault("descripcion_general", "")
    evento["creado_en"] = ahora_utc()
    res = get_col(COL_EVENTO).insert_one(evento)
    return {"exito": True, "id": str(res.inserted_id)}


@router.put("/eventos/{id}")
def actualizar_evento(id: str, cambios: dict):
    cambios.pop("_id", None)
    cambios.pop("creado_en", None)
    # palabras_clave puede venir como string separado por comas
    if "palabras_clave" in cambios and isinstance(cambios["palabras_clave"], str):
        cambios["palabras_clave"] = [p.strip() for p in cambios["palabras_clave"].split(",") if p.strip()]
    cambios["actualizado_en"] = ahora_utc()
    res = get_col(COL_EVENTO).update_one({"_id": oid(id)}, {"$set": cambios})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Evento no encontrado.")
    return {"exito": True}


@router.delete("/eventos/{id}")
def eliminar_evento(id: str):
    # Obtener ediciones del evento
    ediciones = list(get_col(COL_EDICION).find({"evento_id": oid(id)}, {"_id": 1}))
    edicion_ids = [e["_id"] for e in ediciones]

    # Contar recursos afectados
    recursos_afectados = 0
    if edicion_ids:
        recursos_afectados = get_col(COL_RECURSO).count_documents(
            {"edicion_id": {"$in": edicion_ids}}
        )
        # Desasignar edicion de recursos
        get_col(COL_RECURSO).update_many(
            {"edicion_id": {"$in": edicion_ids}},
            {"$set": {"edicion_id": None}}
        )
        # Eliminar ediciones
        get_col(COL_EDICION).delete_many({"evento_id": oid(id)})

    get_col(COL_EVENTO).delete_one({"_id": oid(id)})
    return {
        "exito": True,
        "ediciones_eliminadas": len(edicion_ids),
        "recursos_desvinculados": recursos_afectados
    }


@router.get("/eventos/{id}/impacto")
def impacto_evento(id: str):
    """Cuántas ediciones y recursos quedarían afectados si se elimina este evento."""
    ediciones = list(get_col(COL_EDICION).find({"evento_id": oid(id)}, {"_id": 1}))
    edicion_ids = [e["_id"] for e in ediciones]
    recursos = 0
    if edicion_ids:
        recursos = get_col(COL_RECURSO).count_documents(
            {"edicion_id": {"$in": edicion_ids}}
        )
    return {"ediciones_afectadas": len(edicion_ids), "recursos_afectados": recursos}


# ══════════════════════════════════════════════
# EDICIONES
# ══════════════════════════════════════════════

@router.get("/ediciones")
def listar_ediciones():
    docs = [serializar_doc(d) for d in get_col(COL_EDICION).find({}).sort("anio", -1)]
    return {"exito": True, "total": len(docs), "data": docs}


@router.get("/eventos/{evento_id}/ediciones")
def listar_ediciones_de_evento(evento_id: str):
    docs = [
        serializar_doc(d)
        for d in get_col(COL_EDICION).find(
            {"evento_id": oid(evento_id)}
        ).sort("anio", -1)
    ]
    return {"exito": True, "total": len(docs), "data": docs}


@router.post("/eventos/{evento_id}/ediciones")
def crear_edicion(evento_id: str, edicion: dict):
    if not edicion.get("anio"):
        raise HTTPException(status_code=400, detail="El campo 'anio' es obligatorio.")
    # Verificar que no exista ya una edición para ese año en ese evento
    existe = get_col(COL_EDICION).find_one({
        "evento_id": oid(evento_id),
        "anio": int(edicion["anio"])
    })
    if existe:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe una edicion para el año {edicion['anio']} en este evento."
        )
    edicion["evento_id"]  = oid(evento_id)
    edicion["anio"]       = int(edicion["anio"])
    edicion.setdefault("estado", "Planificada")
    edicion.setdefault("fecha_inicio", None)
    edicion.setdefault("fecha_fin", None)
    edicion["creado_en"]  = ahora_utc()
    res = get_col(COL_EDICION).insert_one(edicion)
    return {"exito": True, "id": str(res.inserted_id)}


@router.put("/ediciones/{id}")
def actualizar_edicion(id: str, cambios: dict):
    cambios.pop("_id", None)
    cambios.pop("creado_en", None)
    cambios.pop("evento_id", None)  # no se puede cambiar el evento padre
    if "anio" in cambios:
        cambios["anio"] = int(cambios["anio"])
    cambios["actualizado_en"] = ahora_utc()
    res = get_col(COL_EDICION).update_one({"_id": oid(id)}, {"$set": cambios})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Edicion no encontrada.")
    return {"exito": True}


@router.delete("/ediciones/{id}")
def eliminar_edicion(id: str):
    recursos_afectados = get_col(COL_RECURSO).count_documents(
        {"edicion_id": _oid_or_none(id)}
    )
    if recursos_afectados:
        get_col(COL_RECURSO).update_many(
            {"edicion_id": _oid_or_none(id)},
            {"$set": {"edicion_id": None}}
        )
    get_col(COL_EDICION).delete_one({"_id": oid(id)})
    return {"exito": True, "recursos_desvinculados": recursos_afectados}


@router.get("/ediciones/{id}/impacto")
def impacto_edicion(id: str):
    n = get_col(COL_RECURSO).count_documents({"edicion_id": _oid_or_none(id)})
    return {"recursos_afectados": n}
