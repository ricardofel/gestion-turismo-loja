"""
routes/etl.py — Endpoints de extracción ETL con pipeline completo.
"""
from fastapi import APIRouter, HTTPException, Query
from ..database import get_col, COL_LUGAR
from ..connectors.registry import CONECTORES
from ..etl.pipeline import ejecutar_pipeline
from ..database import serializar_doc, ahora_utc
from bson import ObjectId

router = APIRouter(prefix="/api/etl", tags=["ETL"])


@router.get("/fuentes")
def listar_fuentes():
    return {
        "exito"  : True,
        "fuentes": [{"id": k, "nombre": k} for k in CONECTORES]
    }


@router.get("/extraer")
def extraer_datos(
    fuente: str = Query(..., description="TikTok | YouTube | Instagram | TripAdvisor | Flickr | Eventbrite | GoogleReviews"),
    tags  : str = Query("turismo loja", description="Tags separados por coma")
):
    """
    Pipeline ETL completo:
    1. Extrae datos crudos de la fuente con los tags dados
    2. Transforma al esquema RecursoSchema
    3. Deduplica — el usuario solo ve registros NUEVOS
    4. Detecta lugar automáticamente
    5. Detecta edición por año de publicación
    6. Retorna nuevos + lista de lugares nuevos detectados
    """
    if fuente not in CONECTORES:
        raise HTTPException(
            status_code=404,
            detail=f"Fuente '{fuente}' no disponible. Usa: {list(CONECTORES.keys())}"
        )

    lista_tags = [t.strip() for t in tags.split(",") if t.strip()]
    conector   = CONECTORES[fuente]

    # Extraer datos crudos usando extraer_raw (formato nativo de la API)
    if hasattr(conector, "extraer_raw"):
        datos_crudos = conector.extraer_raw(lista_tags)
    else:
        datos_crudos = conector.extraer(lista_tags)

    # Ejecutar pipeline ETL
    resultado = ejecutar_pipeline(datos_crudos, fuente)

    if "error" in resultado:
        raise HTTPException(status_code=500, detail=resultado["error"])

    return {
        "exito"          : True,
        "fuente"         : fuente,
        "tags_usados"    : lista_tags,
        "total_extraidos": resultado["total_extraidos"],
        "nuevos"         : resultado["nuevos"],
        "duplicados"     : resultado["duplicados"],
        "data"           : resultado["recursos_nuevos"],
        "lugares_nuevos" : resultado["lugares_nuevos"],
    }


@router.post("/lugares/confirmar")
def confirmar_lugares_nuevos(lugares: list[dict]):
    """
    Guarda en el catálogo los lugares nuevos que el usuario confirmó.
    Recibe lista de lugares con: nombre, tipo_lugar, direccion_texto.
    """
    if not lugares:
        return {"exito": True, "insertados": 0}

    col = get_col(COL_LUGAR)
    insertados = 0
    ids = []

    for lugar in lugares:
        # Evitar duplicados por nombre
        nombre = lugar.get("nombre", "").strip()
        if not nombre:
            continue
        existe = col.find_one({"nombre": {"$regex": f"^{nombre}$", "$options": "i"}})
        if existe:
            ids.append(str(existe["_id"]))
            continue

        lugar_doc = {
            "nombre"        : nombre,
            "tipo_lugar"    : lugar.get("tipo_lugar", "Por clasificar"),
            "direccion_texto": lugar.get("direccion_texto", nombre),
            "coordenadas_geo": lugar.get("coordenadas_geo"),
            "creado_en"     : ahora_utc(),
        }
        # Quitar campos internos del pipeline
        lugar_doc.pop("_sugerido_por", None)

        res = col.insert_one(lugar_doc)
        ids.append(str(res.inserted_id))
        insertados += 1

    return {"exito": True, "insertados": insertados, "ids": ids}
