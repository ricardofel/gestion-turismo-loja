"""
schemas.py — Validación de esquema con Pydantic.
Refleja exactamente el modelo de datos real en MongoDB Atlas.
Cualquier inserción que no cumpla esto → HTTP 422 antes de tocar la BD.
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator

PLATAFORMAS_VALIDAS = {
    "TikTok", "YouTube", "Instagram",
    "GoogleReviews", "TripAdvisor",
    "Flickr", "Eventbrite", "mock"
}
FORMATOS_VALIDOS = {"video", "reseña", "post", "articulo", "imagen", "mock"}
ESTADOS_VALIDOS  = {"Crudo", "Clasificado", "Error"}


class OrigenSchema(BaseModel):
    plataforma     : str
    formato        : str
    id_externo     : str
    fecha_ingesta  : str
    ubicacion_cruda: Optional[str] = None

    @field_validator("plataforma")
    @classmethod
    def plat_valida(cls, v):
        if v not in PLATAFORMAS_VALIDAS:
            raise ValueError(f"Plataforma '{v}' no permitida. Válidas: {PLATAFORMAS_VALIDAS}")
        return v

    @field_validator("formato")
    @classmethod
    def fmt_valido(cls, v):
        if v not in FORMATOS_VALIDOS:
            raise ValueError(f"Formato '{v}' no permitido. Válidos: {FORMATOS_VALIDOS}")
        return v


class RecursoSchema(BaseModel):
    """
    Espejo exacto del documento 'recurso' en MongoDB Atlas.
    Campos obligatorios: origen, estado_procesamiento, metadata.
    """
    origen               : OrigenSchema
    estado_procesamiento : str                = "Crudo"
    fecha_publicacion    : Optional[str]      = None
    edicion_id           : Optional[str]      = None
    lugar_id             : Optional[str]      = None
    metadata             : dict               = Field(default_factory=dict)

    @field_validator("estado_procesamiento")
    @classmethod
    def estado_valido(cls, v):
        if v not in ESTADOS_VALIDOS:
            raise ValueError(f"Estado '{v}' no válido. Usa: {ESTADOS_VALIDOS}")
        return v

    @model_validator(mode="after")
    def metadata_no_vacia(self):
        if not self.metadata:
            raise ValueError("El campo 'metadata' no puede estar vacío.")
        return self
