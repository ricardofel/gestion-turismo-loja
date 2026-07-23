"""
connectors/registry.py — Registro de conectores ETL activos.

Solo aparecen aquí las fuentes con una API real conectada. Para agregar una
fuente nueva: crea su conector en este mismo paquete (ver base.py), agrégale
su transform_* en backend/etl/pipeline.py, súmala a PLATAFORMAS_VALIDAS en
backend/schemas.py, e impórtala aquí. Ver guia_implementacion_apis.md para el
detalle de qué APIs están disponibles y con qué costo/dificultad.
"""
from .youtube import ConectorYouTubeReal
from .google_reviews import ConectorGoogleReviews
from .base    import ConectorBase

CONECTORES: dict[str, ConectorBase] = {
    "YouTube": ConectorYouTubeReal(),
    "GoogleReviews": ConectorGoogleReviews(),
}
