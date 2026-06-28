"""
routes/recursos.py — CRUD completo de la colección 'recurso'.

Filtros corregidos:
- evento_id  → lookup: edicion[evento_id == X] → ids de ediciones → recursos
- edicion_id → cast a ObjectId antes de comparar
- lugar_id   → cast a ObjectId antes de comparar
- fecha_desde/hasta → rango sobre fecha_publicacion (string ISO, comparación lexicográfica)
"""
from typing import Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pymongo import UpdateOne
from bson import ObjectId

from ..database import get_col, serializar_doc, oid, ahora_utc
from ..database import COL_RECURSO, COL_EDICION
from ..schemas  import RecursoSchema

router = APIRouter(prefix="/api/recursos", tags=["Recursos"])


def _oid_or_none(val: str):
    """Convierte string a ObjectId si es válido, si no retorna None."""
    try:
        return ObjectId(val)
    except Exception:
        return None


@router.get("")
def listar_recursos(
    plataforma  : Optional[str] = Query(None),
    estado      : Optional[str] = Query(None),
    lugar_id    : Optional[str] = Query(None),
    edicion_id  : Optional[str] = Query(None),
    evento_id   : Optional[str] = Query(None),
    fecha_desde : Optional[str] = Query(None),
    fecha_hasta : Optional[str] = Query(None),
    skip        : int           = Query(0, ge=0),
    limit       : int           = Query(20, le=200)
):
    filtro: dict[str, Any] = {}

    if plataforma:
        filtro["origen.plataforma"] = plataforma

    if estado:
        filtro["estado_procesamiento"] = estado

    # lugar_id: el campo en BD es ObjectId, hay que castearlo
    if lugar_id:
        oid_lugar = _oid_or_none(lugar_id)
        if oid_lugar:
            filtro["lugar_id"] = oid_lugar
        else:
            # Si el id no es válido, no va a haber resultados de todas formas
            filtro["lugar_id"] = lugar_id

    # evento_id: requiere lookup en colección edicion
    # primero buscamos todas las ediciones de ese evento,
    # luego filtramos recursos cuyos edicion_id estén en esa lista
    if evento_id:
        oid_evento = _oid_or_none(evento_id)
        query_evento = {"evento_id": oid_evento} if oid_evento else {"evento_id": evento_id}
        ediciones = get_col(COL_EDICION).find(query_evento, {"_id": 1})
        ids_edicion = [e["_id"] for e in ediciones]
        if not ids_edicion:
            # No hay ediciones para ese evento → sin resultados
            return {"exito": True, "total": 0, "data": []}
        filtro["edicion_id"] = {"$in": ids_edicion}

    # edicion_id directo (si viene del filtro de edición, no de evento)
    elif edicion_id:
        oid_edicion = _oid_or_none(edicion_id)
        filtro["edicion_id"] = oid_edicion if oid_edicion else edicion_id

    # Rango de fechas sobre fecha_publicacion (string "YYYY-MM-DD")
    if fecha_desde or fecha_hasta:
        rango: dict[str, str] = {}
        if fecha_desde: rango["$gte"] = fecha_desde
        if fecha_hasta: rango["$lte"] = fecha_hasta
        filtro["fecha_publicacion"] = rango

    col   = get_col(COL_RECURSO)
    total = col.count_documents(filtro)
    docs  = [serializar_doc(d) for d in col.find(filtro).skip(skip).limit(limit)]

    return {"exito": True, "total": total, "data": docs}


@router.post("/bulk")
def guardar_bulk(recursos: list[RecursoSchema]):
    if not recursos:
        raise HTTPException(status_code=400, detail="Lista vacía.")

    ahora = ahora_utc()
    ops   = []
    for r in recursos:
        doc = r.model_dump()
        doc["actualizado_en"] = ahora

        # El schema validator de Atlas exige ObjectId para edicion_id y lugar_id.
        # El pipeline ETL los asigna como strings — convertimos aquí antes de escribir.
        for campo in ("edicion_id", "lugar_id"):
            val = doc.get(campo)
            if val:
                try:
                    doc[campo] = ObjectId(str(val))
                except Exception:
                    doc[campo] = None
            else:
                doc[campo] = None

        ops.append(UpdateOne(
            {"origen.id_externo": r.origen.id_externo},
            {"$set": doc, "$setOnInsert": {"creado_en": ahora}},
            upsert=True
        ))


    res = get_col(COL_RECURSO).bulk_write(ops, ordered=False)
    return {
        "exito"       : True,
        "insertados"  : res.upserted_count,
        "actualizados": res.modified_count,
        "total"       : len(ops)
    }


@router.get("/{id}")
def obtener_recurso(id: str):
    doc = get_col(COL_RECURSO).find_one({"_id": oid(id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Recurso no encontrado.")
    return {"exito": True, "data": serializar_doc(doc)}


@router.put("/{id}")
def actualizar_recurso(id: str, cambios: dict):
    protegidos = {"_id", "origen", "creado_en"}
    limpios    = {k: v for k, v in cambios.items() if k not in protegidos}
    if not limpios:
        raise HTTPException(status_code=400, detail="Sin campos válidos para actualizar.")

    # El schema validator de Atlas exige que edicion_id y lugar_id sean ObjectId, no string.
    # El frontend los envía como strings — los convertimos aquí antes de escribir.
    for campo in ("edicion_id", "lugar_id"):
        if campo in limpios:
            val = limpios[campo]
            limpios[campo] = _oid_or_none(str(val)) if val else None

    limpios["actualizado_en"] = ahora_utc()
    res = get_col(COL_RECURSO).update_one({"_id": oid(id)}, {"$set": limpios})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recurso no encontrado.")
    return {"exito": True, "modificados": res.modified_count}


@router.delete("/{id}")
def eliminar_recurso(id: str):
    res = get_col(COL_RECURSO).delete_one({"_id": oid(id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recurso no encontrado.")
    return {"exito": True, "eliminados": res.deleted_count}
