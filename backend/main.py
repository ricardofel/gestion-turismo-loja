"""
main.py — Punto de entrada. Solo configura FastAPI y registra routers.

Arrancar con:
  uvicorn backend.main:app --reload
"""
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import recursos_router, etl_router, catalogos_router, catalogos_crud_router, stats_router
from .database import get_col, is_connected

app = FastAPI(
    title       = "API ETL Turismo Loja",
    description = "Motor de ingesta y gestión de recursos turísticos — UTPL 2026",
    version     = "4.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(recursos_router)
app.include_router(etl_router)
app.include_router(catalogos_router)
app.include_router(catalogos_crud_router)
app.include_router(stats_router)


@app.get("/", tags=["Salud"])
def raiz():
    return {"mensaje": "Motor ETL Turismo Loja en línea.", "version": "4.1.0"}


@app.get("/api/health", tags=["Salud"])
def health():
    """
    El health check intenta conectar si aún no está conectado.
    No bloquea el arranque del servidor.
    """
    return {
        "api"    : "ok",
        "mongodb": "conectado" if is_connected() else "desconectado"
    }
