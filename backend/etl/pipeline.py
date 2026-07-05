"""
etl/pipeline.py — Pipeline ETL completo.

Flujo:
  1. Datos crudos de la fuente (formato específico de cada API)
  2. Transform → normaliza al esquema RecursoSchema
  3. Deduplica → elimina los que ya existen en BD por id_externo
  4. Detecta lugares → busca coincidencias en colección lugar
  5. Detecta edición → calcula por año de publicación y evento
  6. Retorna solo registros nuevos con lugar_id y edicion_id asignados
     + lista de lugares nuevos detectados para que el usuario decida
"""
from datetime import datetime, timezone
from bson import ObjectId
from ..database import get_col, COL_RECURSO, COL_LUGAR, COL_EDICION, COL_EVENTO


# ── Palabras que NO son nombres de lugares (stop words) ──
STOP_WORDS = {
    "loja", "ecuador", "sur", "norte", "ciudad", "el", "la", "los", "las",
    "de", "del", "en", "y", "a", "con", "por", "para", "un", "una", "es",
    "festival", "fiavl", "arte", "artes", "vivas", "turismo", "cultura",
    "internacional", "nacional", "foto", "video", "tour", "vlog", "reels",
    "tiktok", "instagram", "youtube", "flickr"
}

# ── Transformadores por fuente ────────────────────────────

def _ts(s: str) -> str:
    """Normaliza timestamp ISO."""
    if not s:
        return datetime.now(timezone.utc).isoformat()
    return s if s.endswith("Z") or "+" in s else s + "Z"

def _fecha_pub(s: str) -> str | None:
    """Extrae YYYY-MM-DD de un timestamp."""
    if not s:
        return None
    return s[:10]

def _anio(fecha_pub: str | None) -> int | None:
    """Extrae el año de una fecha publicación."""
    if not fecha_pub or len(fecha_pub) < 4:
        return None
    try:
        return int(fecha_pub[:4])
    except ValueError:
        return None


def transform_tiktok(raw: dict) -> dict:
    """Normaliza dato crudo de TikTok al esquema RecursoSchema."""
    return {
        "origen": {
            "plataforma"    : "TikTok",
            "formato"       : "video",
            "id_externo"    : str(raw.get("id") or raw.get("id_externo") or ""),
            "fecha_ingesta" : datetime.now(timezone.utc).isoformat(),
            "ubicacion_cruda": raw.get("location") or raw.get("ubicacion_cruda"),
        },
        "estado_procesamiento": "Crudo",
        "fecha_publicacion"   : _fecha_pub(raw.get("timestamp") or raw.get("fecha_publicacion")),
        "edicion_id"          : None,
        "lugar_id"            : None,
        "metadata": {
            "metricas": {
                "likes"      : raw.get("likes") or raw.get("metricas", {}).get("likes", 0),
                "shares"     : raw.get("shares") or raw.get("metricas", {}).get("shares", 0),
                "plays"      : raw.get("plays") or raw.get("metricas", {}).get("plays", 0),
                "guardados"  : raw.get("guardados") or raw.get("metricas", {}).get("guardados", 0),
                "comentarios": raw.get("comentarios") or raw.get("metricas", {}).get("comentarios", 0),
            },
            "autor": {
                "name"     : raw.get("user") or raw.get("autor", {}).get("name", "—"),
                "verified" : raw.get("verified", False),
                "fans"     : raw.get("fans", 0),
                "heart"    : raw.get("heart", 0),
                "video"    : raw.get("video", 0),
                "following": raw.get("following", 0),
                "friends"  : raw.get("friends", 0),
                "signature": raw.get("signature", ""),
            },
            "texto_original" : raw.get("caption") or raw.get("texto_original", ""),
            "hashtags"       : raw.get("hashtags", []),
            "urls"           : raw.get("urls", {"video": "", "cover": ""}),
            "video"          : raw.get("video", {"duracion_seg": 0, "cover_url": ""}),
            "musica"         : raw.get("musica", {"nombre": "", "autor": ""}),
            "idioma"         : raw.get("idioma", "es"),
            "es_anuncio"     : raw.get("es_anuncio", False),
            "es_patrocinado" : raw.get("es_patrocinado", False),
            "hora_publicacion": raw.get("hora_publicacion", ""),
        }
    }


def transform_instagram(raw: dict) -> dict:
    """Normaliza dato crudo de Instagram al esquema RecursoSchema."""
    return {
        "origen": {
            "plataforma"    : "Instagram",
            "formato"       : "post",
            "id_externo"    : str(raw.get("id") or raw.get("photo_id") or ""),
            "fecha_ingesta" : datetime.now(timezone.utc).isoformat(),
            "ubicacion_cruda": raw.get("location"),
        },
        "estado_procesamiento": "Crudo",
        "fecha_publicacion"   : _fecha_pub(raw.get("timestamp") or raw.get("date_taken")),
        "edicion_id"          : None,
        "lugar_id"            : None,
        "metadata": {
            "metricas": {
                "likes"      : raw.get("likes", 0),
                "comentarios": raw.get("comments", 0),
                "plays"      : 0,
            },
            "autor": {
                "name"    : raw.get("user") or raw.get("owner", "—"),
                "verified": False,
            },
            "texto_original": raw.get("caption") or raw.get("description", ""),
            "hashtags"      : raw.get("hashtags", []),
            "urls"          : {"video": "", "cover": raw.get("cover_url", "")},
            "video"         : {"duracion_seg": 0, "cover_url": ""},
            "musica"        : {"nombre": "", "autor": ""},
            "idioma"        : "es",
            "es_anuncio"    : False,
            "es_patrocinado": False,
            "hora_publicacion": "",
        }
    }


def transform_tripadvisor(raw: dict) -> dict:
    """Normaliza reseña cruda de TripAdvisor al esquema RecursoSchema."""
    return {
        "origen": {
            "plataforma"    : "TripAdvisor",
            "formato"       : "reseña",
            "id_externo"    : str(raw.get("review_id") or ""),
            "fecha_ingesta" : datetime.now(timezone.utc).isoformat(),
            "ubicacion_cruda": raw.get("location_name"),
        },
        "estado_procesamiento": "Crudo",
        "fecha_publicacion"   : raw.get("date"),
        "edicion_id"          : None,
        "lugar_id"            : None,
        "metadata": {
            "metricas": {
                "likes"      : raw.get("helpful_votes", 0),
                "comentarios": 0,
                "plays"      : 0,
            },
            "autor": {
                "name"    : raw.get("author", "—"),
                "verified": False,
            },
            "texto_original": f"{raw.get('title','')}: {raw.get('text','')}",
            "hashtags"      : [],
            "urls"          : {"video": "", "cover": ""},
            "video"         : {"duracion_seg": 0, "cover_url": ""},
            "musica"        : {"nombre": "", "autor": ""},
            "idioma"        : "es",
            "es_anuncio"    : False,
            "es_patrocinado": False,
            "hora_publicacion": "",
            "estrellas"     : raw.get("rating", 0),
            "tipo_lugar"    : raw.get("location_type", ""),
        }
    }


def transform_flickr(raw: dict) -> dict:
    """Normaliza foto cruda de Flickr al esquema RecursoSchema."""
    geo = raw.get("geo", {})
    return {
        "origen": {
            "plataforma"    : "Flickr",
            "formato"       : "imagen",
            "id_externo"    : str(raw.get("photo_id") or ""),
            "fecha_ingesta" : datetime.now(timezone.utc).isoformat(),
            "ubicacion_cruda": raw.get("place"),
        },
        "estado_procesamiento": "Crudo",
        "fecha_publicacion"   : raw.get("date_taken"),
        "edicion_id"          : None,
        "lugar_id"            : None,
        "metadata": {
            "metricas": {
                "plays"   : raw.get("views", 0),
                "likes"   : raw.get("favorites", 0),
                "comentarios": 0,
            },
            "autor": {
                "name"    : raw.get("owner", "—"),
                "verified": False,
            },
            "texto_original": f"{raw.get('title','')}: {raw.get('description','')}",
            "hashtags"      : raw.get("tags", []),
            "urls"          : {"video": "", "cover": raw.get("url_m", "")},
            "video"         : {"duracion_seg": 0, "cover_url": raw.get("url_m", "")},
            "musica"        : {"nombre": "", "autor": ""},
            "idioma"        : "es",
            "es_anuncio"    : False,
            "es_patrocinado": False,
            "hora_publicacion": "",
            "coordenadas"   : geo,
        }
    }


def transform_eventbrite(raw: dict) -> dict:
    """Normaliza evento crudo de Eventbrite al esquema RecursoSchema."""
    return {
        "origen": {
            "plataforma"    : "Eventbrite",
            "formato"       : "articulo",
            "id_externo"    : str(raw.get("event_id") or ""),
            "fecha_ingesta" : datetime.now(timezone.utc).isoformat(),
            "ubicacion_cruda": raw.get("venue"),
        },
        "estado_procesamiento": "Crudo",
        "fecha_publicacion"   : _fecha_pub(raw.get("start")),
        "edicion_id"          : None,
        "lugar_id"            : None,
        "metadata": {
            "metricas": {
                "plays"      : raw.get("attendees_capacity", 0),
                "likes"      : raw.get("tickets_sold", 0),
                "comentarios": 0,
            },
            "autor": {
                "name"    : raw.get("organizer", "—"),
                "verified": True,
            },
            "texto_original": f"{raw.get('name','')}: {raw.get('description','')}",
            "hashtags"      : raw.get("tags", []),
            "urls"          : {"video": "", "cover": ""},
            "video"         : {"duracion_seg": 0, "cover_url": ""},
            "musica"        : {"nombre": "", "autor": ""},
            "idioma"        : "es",
            "es_anuncio"    : False,
            "es_patrocinado": raw.get("is_free", True) is False,
            "hora_publicacion": "",
            "estado_evento" : raw.get("status", ""),
            "categoria"     : raw.get("category", ""),
        }
    }


def transform_youtube(raw: dict) -> dict:
    """Normaliza dato crudo de YouTube al esquema RecursoSchema."""
    return {
        "origen": {
            "plataforma"    : "YouTube",
            "formato"       : "video",
            "id_externo"    : str(raw.get("video_id") or raw.get("id_externo") or ""),
            "fecha_ingesta" : datetime.now(timezone.utc).isoformat(),
            "ubicacion_cruda": None,
        },
        "estado_procesamiento": "Crudo",
        "fecha_publicacion"   : raw.get("date") or raw.get("fecha_publicacion"),
        "edicion_id"          : None,
        "lugar_id"            : None,
        "metadata": {
            "metricas": {
                "plays"      : raw.get("views", 0),
                "likes"      : raw.get("likes", 0),
                "comentarios": raw.get("comments", 0),
            },
            "autor": {
                "name"    : raw.get("channel", "—"),
                "verified": False,
            },
            "texto_original": f"{raw.get('title','')}. {raw.get('description','')}",
            "hashtags"      : raw.get("tags", []),
            "urls"          : {"video": raw.get("url",""), "cover": raw.get("thumbnail","")},
            "video"         : {"duracion_seg": raw.get("duration", 0), "cover_url": raw.get("thumbnail","")},
            "musica"        : {"nombre": "", "autor": ""},
            "idioma"        : "es",
            "es_anuncio"    : False,
            "es_patrocinado": False,
            "hora_publicacion": "",
        }
    }


def transform_google_reviews(raw: dict) -> dict:
    """Normaliza reseña cruda de Google Reviews al esquema RecursoSchema."""
    return {
        "origen": {
            "plataforma"    : "GoogleReviews",
            "formato"       : "reseña",
            "id_externo"    : str(raw.get("review_id") or ""),
            "fecha_ingesta" : datetime.now(timezone.utc).isoformat(),
            "ubicacion_cruda": raw.get("location") or raw.get("place_name"),
        },
        "estado_procesamiento": "Crudo",
        "fecha_publicacion"   : raw.get("date"),
        "edicion_id"          : None,
        "lugar_id"            : None,
        "metadata": {
            "metricas": {
                "likes"      : raw.get("rating", 0),
                "comentarios": 0,
                "plays"      : 0,
            },
            "autor": {
                "name"    : raw.get("author_name", "—"),
                "verified": False,
            },
            "texto_original": raw.get("text", ""),
            "hashtags"      : [],
            "urls"          : {"video": "", "cover": ""},
            "video"         : {"duracion_seg": 0, "cover_url": ""},
            "musica"        : {"nombre": "", "autor": ""},
            "idioma"        : "es",
            "es_anuncio"    : False,
            "es_patrocinado": False,
            "hora_publicacion": "",
            "estrellas"     : raw.get("rating", 0),
            "tipo_lugar"    : raw.get("place_type", ""),
            "lugar_nombre"  : raw.get("place_name", ""),
        }
    }


# Mapa de transformadores por plataforma
TRANSFORMERS = {
    "TikTok"       : transform_tiktok,
    "Instagram"    : transform_instagram,
    "TripAdvisor"  : transform_tripadvisor,
    "Flickr"       : transform_flickr,
    "Eventbrite"   : transform_eventbrite,
    "YouTube"      : transform_youtube,
    "GoogleReviews": transform_google_reviews,
}


# ── Detección de lugares ──────────────────────────────────

def _tokens_texto(recurso: dict) -> set[str]:
    """Extrae tokens relevantes de un recurso para buscar lugares."""
    meta = recurso.get("metadata", {})
    texto = (meta.get("texto_original") or "").lower()
    hashtags = [h.lower() for h in (meta.get("hashtags") or [])]
    ubicacion = (recurso.get("origen", {}).get("ubicacion_cruda") or "").lower()
    return set(texto.split() + hashtags + ubicacion.split())


def detectar_lugar(recurso: dict, lugares_catalogo: list[dict]) -> str | None:
    """
    Busca si el recurso menciona algún lugar del catálogo.
    Retorna el _id del lugar si hay coincidencia, None si no.
    Lógica: busca el nombre del lugar (o sus palabras clave) en
    texto, hashtags y ubicacion_cruda del recurso.
    """
    tokens = _tokens_texto(recurso)
    ubicacion_raw = (recurso.get("origen", {}).get("ubicacion_cruda") or "").lower()
    texto = (recurso.get("metadata", {}).get("texto_original") or "").lower()

    for lugar in lugares_catalogo:
        nombre = lugar.get("nombre", "").lower()
        # Coincidencia exacta en ubicacion_cruda (más confiable)
        if nombre in ubicacion_raw:
            return str(lugar["_id"])
        # Coincidencia de palabras clave significativas del nombre
        palabras = [p for p in nombre.split() if len(p) > 3 and p not in STOP_WORDS]
        if palabras and all(p in texto or p in ubicacion_raw for p in palabras):
            return str(lugar["_id"])

    return None


def detectar_lugar_nuevo(recurso: dict, nombres_existentes: set[str]) -> dict | None:
    """
    Intenta detectar si el recurso menciona un lugar que NO está en el catálogo.
    Usa la ubicacion_cruda como señal principal.
    Retorna un dict con datos del posible lugar nuevo, o None.
    """
    ubicacion = (recurso.get("origen", {}).get("ubicacion_cruda") or "").strip()
    if not ubicacion:
        return None

    # Normalizar para comparar
    ub_norm = ubicacion.lower()
    for existente in nombres_existentes:
        if existente.lower() in ub_norm or ub_norm in existente.lower():
            return None

    # Filtrar ubicaciones genéricas
    palabras_genericas = {"loja", "ecuador", "loja, ecuador", "ec", "sur del ecuador"}
    if ub_norm in palabras_genericas or len(ubicacion) < 5:
        return None

    return {
        "nombre"        : ubicacion,
        "tipo_lugar"    : "Por clasificar",
        "direccion_texto": ubicacion,
        "coordenadas_geo": None,
        "_sugerido_por"  : recurso.get("origen", {}).get("id_externo", ""),
    }


# ── Detección de edición ──────────────────────────────────

def detectar_edicion(recurso: dict, ediciones: list[dict], eventos: list[dict]) -> str | None:
    """
    Asigna edicion_id basándose en:
    1. El año de fecha_publicacion del recurso
    2. Las palabras clave del evento que aparecen en el texto/hashtags

    Prioriza: evento con más palabras clave coincidentes + año exacto.
    """
    anio = _anio(recurso.get("fecha_publicacion"))
    if not anio:
        return None

    meta    = recurso.get("metadata", {})
    texto   = (meta.get("texto_original") or "").lower()
    hashtags = [h.lower() for h in (meta.get("hashtags") or [])]
    contenido = texto + " " + " ".join(hashtags)

    mejor_score    = 0
    mejor_edicion  = None

    for evento in eventos:
        palabras_clave = [p.lower() for p in (evento.get("palabras_clave") or [])]
        if not palabras_clave:
            continue
        score = sum(1 for p in palabras_clave if p in contenido)
        if score == 0:
            continue

        # Buscar edición de ese evento en el año correcto
        for edicion in ediciones:
            ev_id_str = str(edicion.get("evento_id") or "")
            if ev_id_str == str(evento.get("_id") or ""):
                if edicion.get("anio") == anio and score > mejor_score:
                    mejor_score   = score
                    mejor_edicion = str(edicion.get("_id"))

    return mejor_edicion


# ── Pipeline principal ────────────────────────────────────

def ejecutar_pipeline(datos_crudos: list[dict], plataforma: str) -> dict:
    """
    Ejecuta el pipeline ETL completo sobre datos crudos de una fuente.

    Retorna:
      {
        "recursos_nuevos"  : [...],   # listos para mostrar y guardar
        "lugares_nuevos"   : [...],   # candidatos a agregar al catálogo
        "total_extraidos"  : int,
        "duplicados"       : int,
        "nuevos"           : int,
      }
    """
    transformer = TRANSFORMERS.get(plataforma)
    if not transformer:
        return {"error": f"Sin transformador para '{plataforma}'"}

    # 1. TRANSFORM — normalizar al esquema
    transformados = []
    for raw in datos_crudos:
        try:
            transformados.append(transformer(raw))
        except Exception as e:
            print(f"⚠️  Error transformando {plataforma}: {e}")
            continue

    # 2. DEDUPLICAR — solo nuevos
    ids_extraidos = [r["origen"]["id_externo"] for r in transformados]
    col_recurso   = get_col("recurso")
    existentes    = set(
        doc["origen"]["id_externo"]
        for doc in col_recurso.find(
            {"origen.id_externo": {"$in": ids_extraidos}},
            {"origen.id_externo": 1}
        )
    )
    nuevos = [r for r in transformados if r["origen"]["id_externo"] not in existentes]

    # 3. CARGAR CATÁLOGOS para detección
    lugares_catalogo = list(get_col("lugar").find({}))
    nombres_existentes = {l.get("nombre", "") for l in lugares_catalogo}
    ediciones = list(get_col("edicion").find({}))
    eventos   = list(get_col("evento").find({}))

    # 4. DETECTAR LUGAR + EDICIÓN para cada recurso nuevo
    lugares_nuevos_map: dict[str, dict] = {}  # nombre → datos
    for r in nuevos:
        # Lugar
        lugar_id = detectar_lugar(r, lugares_catalogo)
        if lugar_id:
            r["lugar_id"] = lugar_id
        else:
            candidato = detectar_lugar_nuevo(r, nombres_existentes)
            if candidato:
                nombre = candidato["nombre"]
                if nombre not in lugares_nuevos_map:
                    lugares_nuevos_map[nombre] = candidato
                # Marcar el recurso para que el frontend muestre qué lugar nuevo le corresponde
                r["_lugar_nuevo_sugerido"] = nombre

        # Edición
        edicion_id = detectar_edicion(r, ediciones, eventos)
        if edicion_id:
            r["edicion_id"] = edicion_id

    return {
        "total_extraidos": len(transformados),
        "duplicados"     : len(existentes),
        "nuevos"         : len(nuevos),
        "recursos_nuevos": nuevos,
        "lugares_nuevos" : list(lugares_nuevos_map.values()),
    }
