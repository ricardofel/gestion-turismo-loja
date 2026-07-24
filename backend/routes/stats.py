"""
routes/stats.py — Endpoints de estadísticas reales para el dashboard Home.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from bson import ObjectId
import re
from ..database import get_col, COL_RECURSO, COL_EVENTO, COL_EDICION, COL_LUGAR, COL_IMAGEN_OCULTA, ahora_utc

router = APIRouter(prefix="/api/stats", tags=["Estadísticas"])


@router.get("/resumen")
def resumen_general():
    """
    KPIs principales: total, distribución por plataforma y por estado.
    """
    col = get_col(COL_RECURSO)

    # Por plataforma
    por_plataforma = list(col.aggregate([
        {"$group": {"_id": "$origen.plataforma", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))

    # Por estado
    por_estado = list(col.aggregate([
        {"$group": {"_id": "$estado_procesamiento", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))

    # Fuentes activas = plataformas con al menos 1 recurso
    fuentes_activas = [p["_id"] for p in por_plataforma if p["_id"]]

    return {
        "exito": True,
        "fuentes_activas": len(fuentes_activas),
        "fuentes_nombres": fuentes_activas,
        "por_plataforma": [
            {"plataforma": p["_id"] or "Desconocida", "count": p["count"]}
            for p in por_plataforma if p["_id"]
        ],
        "por_estado": [
            {"estado": e["_id"] or "Desconocido", "count": e["count"]}
            for e in por_estado if e["_id"]
        ],
    }


@router.get("/ingesta-mensual")
def ingesta_mensual(desde: str | None = None, hasta: str | None = None):
    """
    Agrupa recursos por mes según fecha_publicacion (YYYY-MM-DD).
    Devuelve todos los meses con datos, o solo el rango [desde, hasta]
    si se pasan como query params en formato "YYYY-MM"
    (ej: /api/stats/ingesta-mensual?desde=2026-02&hasta=2026-06).
    """
    col = get_col(COL_RECURSO)

    match_stage = {"fecha_publicacion": {"$ne": None, "$type": "string", "$regex": r"^\d{4}-\d{2}"}}
    if desde and re.match(r"^\d{4}-\d{2}$", desde):
        match_stage.setdefault("fecha_publicacion", {})
        match_stage["fecha_publicacion"] = {**match_stage["fecha_publicacion"], "$gte": f"{desde}-01"}
    if hasta and re.match(r"^\d{4}-\d{2}$", hasta):
        match_stage["fecha_publicacion"] = {**match_stage["fecha_publicacion"], "$lte": f"{hasta}-31"}

    pipeline = [
        {"$match": match_stage},
        {"$project": {
            "anio": {"$substr": ["$fecha_publicacion", 0, 4]},
            "mes":  {"$substr": ["$fecha_publicacion", 5, 2]},
        }},
        {"$group": {
            "_id":   {"anio": "$anio", "mes": "$mes"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.anio": 1, "_id.mes": 1}},
    ]
    if not desde and not hasta:
        pipeline.append({"$limit": 24})  # sin filtro, se mantiene el tope original

    resultado = list(col.aggregate(pipeline))

    MESES_ES = {
        "01": "Ene", "02": "Feb", "03": "Mar", "04": "Abr",
        "05": "May", "06": "Jun", "07": "Jul", "08": "Ago",
        "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dic"
    }

    return {
        "exito": True,
        "data": [
            {
                "periodo": f"{r['_id']['anio']}-{r['_id']['mes']}",
                "label":   f"{MESES_ES.get(r['_id']['mes'], r['_id']['mes'])} {r['_id']['anio']}",
                "count":   r["count"]
            }
            for r in resultado
        ]
    }


@router.get("/eventos")
def stats_eventos():
    """
    Por cada evento: cuántos recursos tiene (via edicion_id),
    cuántas ediciones tiene y si es el más popular.
    """
    col_recurso = get_col(COL_RECURSO)
    col_edicion = get_col(COL_EDICION)
    col_evento  = get_col(COL_EVENTO)

    # Todos los eventos
    eventos = list(col_evento.find({}))

    resultado = []
    for ev in eventos:
        ev_id = ev["_id"]

        # Ediciones de este evento
        ediciones = list(col_edicion.find({"evento_id": ev_id}, {"_id": 1, "anio": 1}))
        edicion_ids = [e["_id"] for e in ediciones]

        # Recursos con alguna de esas ediciones
        recursos_count = 0
        if edicion_ids:
            recursos_count = col_recurso.count_documents(
                {"edicion_id": {"$in": edicion_ids}}
            )

        resultado.append({
            "id":               str(ev_id),
            "nombre":           ev.get("nombre_oficial", ""),
            "categoria":        ev.get("categoria", ""),
            "activo":           ev.get("activo", True),
            "ediciones":        len(ediciones),
            "anios_ediciones":  sorted([e.get("anio", 0) for e in ediciones], reverse=True),
            "recursos":         recursos_count,
        })

    # Ordenar por recursos descendente
    resultado.sort(key=lambda x: x["recursos"], reverse=True)

    # Marcar el más popular
    if resultado and resultado[0]["recursos"] > 0:
        resultado[0]["es_mas_popular"] = True

    return {"exito": True, "data": resultado}


@router.get("/top-lugares")
def top_lugares(limite: int = 5):
    """
    Los lugares con más recursos asociados. `limite` controla cuántos se
    devuelven (el frontend pide más de 5 cuando el usuario busca o para
    dibujar el mapa de puntos).
    """
    col_recurso = get_col(COL_RECURSO)
    col_lugar   = get_col(COL_LUGAR)
    limite = max(1, min(limite, 100))

    por_lugar = list(col_recurso.aggregate([
        {"$match": {"lugar_id": {"$ne": None}}},
        {"$group": {"_id": "$lugar_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limite}
    ]))

    resultado = []
    for item in por_lugar:
        lugar = col_lugar.find_one(
            {"_id": item["_id"]},
            {"nombre": 1, "tipo_lugar": 1, "coordenadas_geo": 1}
        )
        if lugar:
            coords = lugar.get("coordenadas_geo") or {}
            lonlat = coords.get("coordinates") if coords.get("type") == "Point" else None
            resultado.append({
                "nombre"    : lugar["nombre"],
                "tipo_lugar": lugar.get("tipo_lugar", ""),
                "count"     : item["count"],
                "lon"       : lonlat[0] if lonlat else None,
                "lat"       : lonlat[1] if lonlat else None,
            })

    return {"exito": True, "data": resultado}


@router.get("/engagement")
def engagement():
    """
    KPIs de alcance real (vistas/likes/comentarios) + el recurso más visto,
    como tarjeta destacada. Solo tiene sentido para recursos con métricas
    numéricas (por ahora, YouTube).
    """
    col = get_col(COL_RECURSO)

    totales = list(col.aggregate([
        {"$group": {
            "_id": None,
            "vistas":      {"$sum": "$metadata.metricas.plays"},
            "likes":       {"$sum": "$metadata.metricas.likes"},
            "comentarios": {"$sum": "$metadata.metricas.comentarios"},
        }}
    ]))
    t = totales[0] if totales else {}

    top = list(col.find(
        {"metadata.metricas.plays": {"$gt": 0}},
        {"metadata.texto_original": 1, "metadata.autor.name": 1,
         "metadata.metricas": 1, "metadata.urls.video": 1}
    ).sort("metadata.metricas.plays", -1).limit(1))

    destacado = None
    if top:
        r = top[0]
        meta = r.get("metadata", {})
        destacado = {
            "titulo":      (meta.get("texto_original") or "").split(".")[0][:120],
            "canal":       meta.get("autor", {}).get("name", "—"),
            "vistas":      meta.get("metricas", {}).get("plays", 0),
            "comentarios": meta.get("metricas", {}).get("comentarios", 0),
            "url":         meta.get("urls", {}).get("video", ""),
        }

    return {
        "exito": True,
        "total_vistas":      t.get("vistas", 0) or 0,
        "total_likes":       t.get("likes", 0) or 0,
        "total_comentarios": t.get("comentarios", 0) or 0,
        "destacado": destacado,
    }


@router.get("/hashtags")
def top_hashtags():
    """
    Palabras clave / hashtags más usados en los recursos.
    """
    col = get_col(COL_RECURSO)

    resultado = list(col.aggregate([
        {"$match": {"metadata.hashtags": {"$exists": True, "$ne": []}}},
        {"$unwind": "$metadata.hashtags"},
        {"$group": {"_id": {"$toLower": "$metadata.hashtags"}, "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]))

    return {
        "exito": True,
        "data": [{"tag": r["_id"], "count": r["count"]} for r in resultado if r["_id"]],
    }


# Palabras muy comunes en español que no aportan significado para este análisis.
_STOP_WORDS_ES = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las",
    "por", "un", "para", "con", "no", "una", "su", "al", "lo", "como",
    "más", "pero", "sus", "le", "ya", "o", "este", "sí", "porque", "esta",
    "entre", "cuando", "muy", "sin", "sobre", "también", "me", "hasta",
    "hay", "donde", "quien", "desde", "todo", "nos", "durante", "todos",
    "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante", "ellos",
    "e", "esto", "mí", "antes", "algunos", "qué", "unos", "yo", "otro",
    "otras", "otra", "él", "tanto", "esa", "estos", "mucho", "quienes",
    "nada", "muchos", "cual", "poco", "ella", "estar", "estas", "algunas",
    "algo", "nosotros", "es", "son", "fue", "ser", "loja", "ecuador",
}


@router.get("/palabras-frecuentes")
def palabras_frecuentes(plataforma: str | None = None):
    """
    La(s) palabra(s) más repetidas en el texto de los recursos
    (título/descripción), sin contar palabras de relleno.
    Distinto de /hashtags: aquí se analiza el texto libre, no las etiquetas.
    `plataforma` filtra (ej: ?plataforma=GoogleReviews).
    """
    col = get_col(COL_RECURSO)

    match = {"metadata.texto_original": {"$exists": True, "$ne": ""}}
    if plataforma:
        match["origen.plataforma"] = plataforma

    textos = col.find(match, {"metadata.texto_original": 1})

    conteo = {}
    for r in textos:
        texto = (r.get("metadata", {}).get("texto_original") or "").lower()
        for palabra in re.findall(r"[a-záéíóúñü]+", texto):
            if len(palabra) <= 3 or palabra in _STOP_WORDS_ES:
                continue
            conteo[palabra] = conteo.get(palabra, 0) + 1

    top = sorted(conteo.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "exito": True,
        "data": [{"palabra": p, "count": c} for p, c in top],
    }


@router.get("/reviews-resumen")
def reviews_resumen():
    """
    KPIs generales de las reseñas de Google (rating promedio, % de Local
    Guides, distribución de estrellas).
    """
    col = get_col(COL_RECURSO)
    match = {"origen.plataforma": "GoogleReviews"}

    total = col.count_documents(match)
    if total == 0:
        return {"exito": True, "total": 0, "rating_promedio": None, "pct_local_guides": 0, "distribucion": []}

    agg = list(col.aggregate([
        {"$match": match},
        {"$group": {
            "_id": None,
            "rating_promedio": {"$avg": "$metadata.metricas.rating"},
            "local_guides": {"$sum": {"$cond": ["$metadata.autor.verified", 1, 0]}},
        }}
    ]))
    a = agg[0] if agg else {}

    distribucion_raw = list(col.aggregate([
        {"$match": {**match, "metadata.metricas.rating": {"$ne": None}}},
        {"$group": {"_id": "$metadata.metricas.rating", "count": {"$sum": 1}}},
    ]))
    dist_map = {int(r["_id"]): r["count"] for r in distribucion_raw if r["_id"] is not None}
    distribucion = [{"estrellas": e, "count": dist_map.get(e, 0)} for e in [5, 4, 3, 2, 1]]

    return {
        "exito": True,
        "total": total,
        "rating_promedio": round(a.get("rating_promedio") or 0, 2),
        "pct_local_guides": round((a.get("local_guides", 0) / total) * 100, 1),
        "distribucion": distribucion,
    }


@router.get("/reviews-por-lugar")
def reviews_por_lugar(limite: int = 10):
    """
    Rating promedio y cantidad de reseñas por lugar (solo Google Reviews).
    """
    col_recurso = get_col(COL_RECURSO)
    col_lugar   = get_col(COL_LUGAR)
    limite = max(1, min(limite, 50))

    agg = list(col_recurso.aggregate([
        {"$match": {"origen.plataforma": "GoogleReviews", "lugar_id": {"$ne": None}}},
        {"$group": {
            "_id": "$lugar_id",
            "count": {"$sum": 1},
            "rating_promedio": {"$avg": "$metadata.metricas.rating"},
        }},
        {"$sort": {"count": -1}},
        {"$limit": limite},
    ]))

    resultado = []
    for item in agg:
        lugar = col_lugar.find_one({"_id": item["_id"]}, {"nombre": 1, "tipo_lugar": 1})
        if lugar:
            resultado.append({
                "lugar_id": str(item["_id"]),
                "nombre": lugar["nombre"],
                "tipo_lugar": lugar.get("tipo_lugar", ""),
                "count": item["count"],
                "rating_promedio": round(item["rating_promedio"] or 0, 2),
            })

    return {"exito": True, "data": resultado}


@router.get("/reviews-recientes")
def reviews_recientes(
    lugar_id: str | None = None,
    limite: int = 20,
    offset: int = 0,
    rating: int | None = None,
    rating_max: int | None = None,
    orden: str = "recientes",
    desde: str | None = None,
    hasta: str | None = None,
):
    """
    Lista de reseñas individuales (texto, autor, rating, lugar).
    `lugar_id`   filtra por un lugar específico.
    `rating`     filtra por una calificación exacta (1-5).
    `rating_max` filtra por calificación <= N (ej: rating_max=2 = quejas).
    `orden`      "recientes" (default) o "likes" (más útiles primero).
    `desde`/`hasta` filtran por fecha_publicacion, formato "YYYY-MM-DD".
    `offset`     cuántos resultados saltar (para "cargar más" / paginación).
    """
    col_recurso = get_col(COL_RECURSO)
    col_lugar   = get_col(COL_LUGAR)
    limite = max(1, min(limite, 100))
    offset = max(0, offset)

    match: dict = {"origen.plataforma": "GoogleReviews"}
    if lugar_id:
        try:
            match["lugar_id"] = ObjectId(lugar_id)
        except Exception:
            return {"exito": True, "data": [], "total": 0}

    if rating is not None:
        match["metadata.metricas.rating"] = rating
    elif rating_max is not None:
        match["metadata.metricas.rating"] = {"$lte": rating_max}

    if desde or hasta:
        rango_fecha: dict = {}
        if desde:
            rango_fecha["$gte"] = desde
        if hasta:
            rango_fecha["$lte"] = hasta + "T23:59:59Z"
        match["fecha_publicacion"] = rango_fecha

    total = col_recurso.count_documents(match)

    campo_orden = "metadata.metricas.likes" if orden == "likes" else "fecha_publicacion"
    docs = list(col_recurso.find(match).sort(campo_orden, -1).skip(offset).limit(limite))

    lugares_cache: dict[str, str] = {}
    resultado = []
    for d in docs:
        meta = d.get("metadata", {})
        lid = d.get("lugar_id")
        nombre_lugar = None
        if lid:
            lid_str = str(lid)
            if lid_str not in lugares_cache:
                lugar = col_lugar.find_one({"_id": lid}, {"nombre": 1})
                lugares_cache[lid_str] = lugar["nombre"] if lugar else None
            nombre_lugar = lugares_cache[lid_str]

        resultado.append({
            "texto": meta.get("texto_original", ""),
            "autor": meta.get("autor", {}).get("name", "—"),
            "es_local_guide": meta.get("autor", {}).get("verified", False),
            "rating": meta.get("metricas", {}).get("rating"),
            "likes": meta.get("metricas", {}).get("likes", 0),
            "fecha": d.get("fecha_publicacion"),
            "lugar_nombre": nombre_lugar,
            "url": meta.get("urls", {}).get("review", ""),
            "imagenes": meta.get("imagenes", []) or [],
        })

    return {
        "exito": True,
        "data": resultado,
        "total": total,
        "offset": offset,
        "hay_mas": (offset + len(resultado)) < total,
    }


@router.get("/reviews-imagenes")
def reviews_imagenes(lugar_id: str | None = None, limite: int = 60):
    """
    Todas las fotos subidas en las reseñas de Google, aplanadas en una
    sola lista (para mostrarlas como galería/collage). Si se pasa
    `lugar_id`, solo trae las de ese lugar. No incluye las fotos marcadas
    como "no corresponde" desde la propia galería.
    """
    col = get_col(COL_RECURSO)
    col_ocultas = get_col(COL_IMAGEN_OCULTA)
    limite = max(1, min(limite, 200))

    urls_ocultas = {d["url"] for d in col_ocultas.find({}, {"url": 1})}

    match: dict = {
        "origen.plataforma": "GoogleReviews",
        "metadata.imagenes": {"$exists": True, "$ne": []},
    }
    if lugar_id:
        try:
            match["lugar_id"] = ObjectId(lugar_id)
        except Exception:
            return {"exito": True, "data": []}

    # Traemos de más porque algunas se van a descartar por estar ocultas.
    docs = list(col.find(
        match,
        {"metadata.imagenes": 1, "metadata.autor.name": 1, "metadata.metricas.rating": 1, "fecha_publicacion": 1}
    ).sort("fecha_publicacion", -1).limit(limite * 2))

    fotos = []
    for d in docs:
        meta = d.get("metadata", {})
        for url in (meta.get("imagenes") or []):
            if url in urls_ocultas:
                continue
            fotos.append({
                "url": url,
                "autor": meta.get("autor", {}).get("name", "—"),
                "rating": meta.get("metricas", {}).get("rating"),
            })
            if len(fotos) >= limite:
                break
        if len(fotos) >= limite:
            break

    return {"exito": True, "data": fotos}


class OcultarImagenBody(BaseModel):
    url: str


@router.post("/reviews-imagenes/ocultar")
def ocultar_imagen(body: OcultarImagenBody):
    """
    Marca una foto como "no corresponde" para que deje de salir en la
    galería/collage. No borra la reseña ni la foto original, solo la
    excluye de la vista (se puede revertir quitando el registro de la
    colección imagen_oculta directamente en Mongo si hiciera falta).
    """
    col = get_col(COL_IMAGEN_OCULTA)
    col.update_one(
        {"url": body.url},
        {"$set": {"url": body.url, "ocultada_en": ahora_utc().isoformat()}},
        upsert=True,
    )
    return {"exito": True}
