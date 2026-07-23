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
from fastapi.staticfiles import StaticFiles
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


@app.get("/api/health", tags=["Salud"])
def health():
    """
    El health check intenta conectar si aún no está conectado.
    No bloquea el arranque del servidor. Devuelve 200 aunque Mongo esté
    desconectado a propósito — así un deploy sin credenciales (demo/
    decorativo) sigue reportando el servicio como sano.
    """
    return {
        "api"    : "ok",
        "mongodb": "conectado" if is_connected() else "desconectado"
    }


# El frontend (HTML/JS sin build step) se sirve desde el mismo servicio,
# en la raíz "/" — así Render (u otro host) solo necesita desplegar un
# único servicio, sin CORS entre orígenes distintos. Va al final para que
# las rutas /api/* de arriba se resuelvan primero.
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
