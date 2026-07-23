"""
database.py — Conexión lazy a MongoDB Atlas y helpers de serialización.
La conexión se establece en la primera petición, no al importar.
Esto evita que el servidor tarde o falle al arrancar si Atlas no responde.
"""
import os
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId
from fastapi import HTTPException

# ── Nombres de colecciones (fuente de verdad) ─────────────
COL_RECURSO  = "recurso"
COL_EVENTO   = "evento"
COL_EDICION  = "edicion"
COL_LUGAR    = "lugar"

MONGO_URI = os.getenv("MONGO_URI", "")
MONGO_DB  = os.getenv("MONGO_DB", "turismo_loja")

# Conexión lazy — se inicializa en la primera llamada a get_db()
_client = None
_db     = None


def get_db():
    """Retorna la instancia de la BD, conectando si es necesario."""
    global _client, _db
    if _db is not None:
        return _db
    try:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        _db = _client[MONGO_DB]
        print(f"[OK] MongoDB Atlas conectado -> base: '{MONGO_DB}'")
    except Exception as e:
        # Mensaje en ASCII a propósito: en Windows con consola cp1252, un
        # print() con emoji lanza UnicodeEncodeError y ese error escapa de
        # este except, convirtiendo el fallback controlado (_db = None,
        # 503 en get_col) en un 500 sin control.
        print(f"[ERROR] No se pudo conectar a MongoDB: {e}")
        _db = None
    return _db


def get_col(name: str) -> Collection:
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Base de datos no disponible.")
    return db[name]


def is_connected() -> bool:
    return get_db() is not None


def ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


# ── Serialización ─────────────────────────────────────────
def _serializar_valor(v):
    if isinstance(v, ObjectId): return str(v)
    if isinstance(v, datetime):  return v.isoformat()
    if isinstance(v, dict):      return serializar_doc(v)
    if isinstance(v, list):      return [_serializar_valor(i) for i in v]
    return v


def serializar_doc(doc: dict) -> dict:
    return {k: _serializar_valor(v) for k, v in doc.items()}


def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail=f"ID inválido: '{id_str}'")
