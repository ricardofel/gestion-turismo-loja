"""
routes/catalogos.py — Endpoints de catálogos (Eventos, Ediciones, Lugares).
"""
from fastapi import APIRouter, HTTPException
from ..database import get_col, serializar_doc, ahora_utc
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


# ── EVENTOS ──────────────────────────────────────────────
@router.get("/eventos")
def listar_eventos():
    docs = [serializar_doc(d) for d in get_col(COL_EVENTO).find({})]
    return {"exito": True, "total": len(docs), "data": docs}


@router.post("/eventos")
def crear_evento(evento: dict):
    """
    Campos esperados (modelo Evento):
      nombre_oficial  : str   (obligatorio)
      descripcion_general: str
      categoria       : str   ej: "Cultura y Arte", "Religioso", "Comercial"
      palabras_clave  : list[str]
      activo          : bool
    """
    if "nombre_oficial" not in evento:
        raise HTTPException(status_code=400, detail="'nombre_oficial' es obligatorio.")
    evento.setdefault("activo", True)
    evento.setdefault("palabras_clave", [])
    evento["creado_en"] = ahora_utc()
    res = get_col(COL_EVENTO).insert_one(evento)
    return {"exito": True, "id": str(res.inserted_id)}


# ── EDICIONES ────────────────────────────────────────────
@router.get("/ediciones")
def listar_ediciones():
    docs = [serializar_doc(d) for d in get_col(COL_EDICION).find({})]
    return {"exito": True, "total": len(docs), "data": docs}


@router.post("/ediciones")
def crear_edicion(edicion: dict):
    """
    Campos esperados (modelo Edicion):
      evento_id    : str  ObjectId del evento (obligatorio)
      anio         : int  (obligatorio)
      estado       : str  "Planificada" | "En curso" | "Finalizada"
      fecha_inicio : str  YYYY-MM-DD (opcional)
      fecha_fin    : str  YYYY-MM-DD (opcional)
    """
    if "evento_id" not in edicion or "anio" not in edicion:
        raise HTTPException(status_code=400, detail="'evento_id' y 'anio' son obligatorios.")
    edicion.setdefault("estado", "Planificada")
    edicion["creado_en"] = ahora_utc()
    res = get_col(COL_EDICION).insert_one(edicion)
    return {"exito": True, "id": str(res.inserted_id)}


# ── LUGARES ──────────────────────────────────────────────
@router.get("/lugares")
def listar_lugares():
    docs = [serializar_doc(d) for d in get_col(COL_LUGAR).find({})]
    return {"exito": True, "total": len(docs), "data": docs}


@router.post("/lugares")
def crear_lugar(lugar: dict):
    """
    Campos esperados (modelo Lugar):
      nombre          : str   (obligatorio)
      tipo_lugar      : str   ej: "Teatro", "Santuario", "Plaza Pública"
      coordenadas_geo : dict  GeoJSON Point
                        ej: {"type":"Point","coordinates":[-79.20,-3.99]}
      direccion_texto : str   ej: "Av. Salvador Bustamante Celi"
    """
    if "nombre" not in lugar:
        raise HTTPException(status_code=400, detail="'nombre' es obligatorio.")
    lugar["creado_en"] = ahora_utc()
    res = get_col(COL_LUGAR).insert_one(lugar)
    return {"exito": True, "id": str(res.inserted_id)}
