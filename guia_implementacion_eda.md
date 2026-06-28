# Guía de Implementación — Módulo EDA (Home / Dashboard)
## Proyecto ETL Turismo Loja · UTPL 2026
### Para: Desarrollador del módulo de estadísticas
### Antes de tocar cualquier cosa, lee esto completo.

---

## 1. Contexto rápido del proyecto

El proyecto tiene un backend en **FastAPI (Python)** y un frontend en
**JavaScript puro con ES Modules** (sin React, sin Vue, sin build tools).

```
gestion-turismo-loja/
├── backend/          ← Python, FastAPI, MongoDB
└── frontend/         ← HTML + JS puro, sin frameworks
```

Levantar el servidor:
```bash
# Desde la raíz del proyecto
uvicorn backend.main:app --reload
# Luego abrir frontend/index.html con Live Server en VS Code
```

---

## 2. Qué está hecho y qué falta en el Home

### Lo que YA es real (no toques esto):
| Dato | De dónde viene |
|------|---------------|
| Total de recursos | `GET /api/recursos?limit=1` → campo `total` |
| Eventos registrados | Catálogo cargado al inicio en `app.js` |
| Lugares registrados | Catálogo cargado al inicio en `app.js` |

### Lo que está SIMULADO (tu trabajo):
| Dato | Estado actual |
|------|--------------|
| Distribución por plataforma | Hardcodeado: solo TikTok al 100% |
| Distribución por estado | Hardcodeado: todo Crudo, 0 Clasificado, 0 Error |
| Ingesta mensual | Hardcodeado: todo en junio |
| Fuentes activas | Hardcodeado: siempre "1, TikTok activa" |
| Top eventos por recursos | No existe todavía |
| Top lugares por recursos | No existe todavía |

---

## 3. Los dos archivos que debes modificar/crear

### ARCHIVO 1 — Backend: `backend/routes/stats.py` (CREAR NUEVO)
Aquí van todos los endpoints de estadísticas. Créalo desde cero.

**Estructura base para empezar:**
```python
"""
routes/stats.py — Endpoints de estadísticas y EDA para el dashboard Home.
"""
from fastapi import APIRouter
from ..database import get_col, COL_RECURSO, COL_EVENTO, COL_EDICION, COL_LUGAR
from ..connectors.registry import CONECTORES

router = APIRouter(prefix="/api/stats", tags=["Estadísticas"])


@router.get("/resumen")
def resumen_general():
    """
    Devuelve los KPIs principales del dashboard.
    Este endpoint reemplaza todos los datos hardcodeados del Home.
    """
    col = get_col(COL_RECURSO)

    # Total de recursos
    total = col.count_documents({})

    # Por plataforma — usar aggregation pipeline de MongoDB
    por_plataforma = list(col.aggregate([
        {"$group": {"_id": "$origen.plataforma", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))

    # Por estado de procesamiento
    por_estado = list(col.aggregate([
        {"$group": {"_id": "$estado_procesamiento", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))

    # Fuentes activas = cuántas plataformas distintas tienen al menos 1 recurso
    fuentes_activas = len(por_plataforma)

    return {
        "exito"          : True,
        "total_recursos" : total,
        "fuentes_activas": fuentes_activas,
        "por_plataforma" : [{"plataforma": p["_id"], "count": p["count"]} for p in por_plataforma],
        "por_estado"     : [{"estado": e["_id"], "count": e["count"]} for e in por_estado],
    }


@router.get("/ingesta-mensual")
def ingesta_mensual():
    """
    Agrupa los recursos por mes según fecha_publicacion.
    Devuelve los últimos 12 meses.
    """
    col = get_col(COL_RECURSO)

    resultado = list(col.aggregate([
        # Solo documentos que tengan fecha_publicacion válida
        {"$match": {"fecha_publicacion": {"$ne": None, "$type": "string"}}},
        # Extraer año y mes del string "YYYY-MM-DD"
        {"$project": {
            "anio": {"$substr": ["$fecha_publicacion", 0, 4]},
            "mes" : {"$substr": ["$fecha_publicacion", 5, 2]},
        }},
        {"$group": {
            "_id"  : {"anio": "$anio", "mes": "$mes"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.anio": 1, "_id.mes": 1}},
        {"$limit": 12}
    ]))

    return {
        "exito": True,
        "data" : [
            {
                "periodo": f"{r['_id']['anio']}-{r['_id']['mes']}",
                "count"  : r["count"]
            }
            for r in resultado
        ]
    }


@router.get("/top-eventos")
def top_eventos():
    """
    Los eventos con más recursos asociados (via edicion_id → evento_id).
    """
    col_recurso = get_col(COL_RECURSO)
    col_edicion = get_col(COL_EDICION)
    col_evento  = get_col(COL_EVENTO)

    # Contar recursos por edicion_id
    por_edicion = list(col_recurso.aggregate([
        {"$match": {"edicion_id": {"$ne": None}}},
        {"$group": {"_id": "$edicion_id", "count": {"$sum": 1}}}
    ]))

    # Agrupar por evento
    conteo_evento = {}
    for item in por_edicion:
        edicion = col_edicion.find_one({"_id": item["_id"]}, {"evento_id": 1})
        if edicion and edicion.get("evento_id"):
            ev_id = str(edicion["evento_id"])
            conteo_evento[ev_id] = conteo_evento.get(ev_id, 0) + item["count"]

    # Enriquecer con nombres
    resultado = []
    for ev_id, count in sorted(conteo_evento.items(), key=lambda x: -x[1])[:5]:
        from bson import ObjectId
        evento = col_evento.find_one({"_id": ObjectId(ev_id)}, {"nombre_oficial": 1})
        if evento:
            resultado.append({
                "nombre": evento["nombre_oficial"],
                "count" : count
            })

    return {"exito": True, "data": resultado}


@router.get("/top-lugares")
def top_lugares():
    """
    Los lugares con más recursos asociados.
    """
    col_recurso = get_col(COL_RECURSO)
    col_lugar   = get_col(COL_LUGAR)

    por_lugar = list(col_recurso.aggregate([
        {"$match": {"lugar_id": {"$ne": None}}},
        {"$group": {"_id": "$lugar_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]))

    resultado = []
    for item in por_lugar:
        from bson import ObjectId
        lugar = col_lugar.find_one({"_id": item["_id"]}, {"nombre": 1})
        if lugar:
            resultado.append({"nombre": lugar["nombre"], "count": item["count"]})

    return {"exito": True, "data": resultado}
```

### ARCHIVO 2 — Backend: `backend/routes/__init__.py` (MODIFICAR)
Agregar una línea para registrar el nuevo router.

**Antes:**
```python
from .recursos       import router as recursos_router
from .etl            import router as etl_router
from .catalogos      import router as catalogos_router
from .catalogos_crud import router as catalogos_crud_router
```

**Después (agrega esta línea al final):**
```python
from .recursos       import router as recursos_router
from .etl            import router as etl_router
from .catalogos      import router as catalogos_router
from .catalogos_crud import router as catalogos_crud_router
from .stats          import router as stats_router      # ← NUEVA LÍNEA
```

### ARCHIVO 3 — Backend: `backend/main.py` (MODIFICAR)
Registrar el router en la app.

**Busca esta sección:**
```python
app.include_router(recursos_router)
app.include_router(etl_router)
app.include_router(catalogos_router)
app.include_router(catalogos_crud_router)
```

**Agrega al final:**
```python
app.include_router(stats_router)    # ← NUEVA LÍNEA
```

**Y en el import del mismo archivo:**
```python
# Antes:
from .routes import recursos_router, etl_router, catalogos_router, catalogos_crud_router

# Después:
from .routes import recursos_router, etl_router, catalogos_router, catalogos_crud_router, stats_router
```

### ARCHIVO 4 — Frontend: `frontend/views/home.js` (MODIFICAR)
Este es el único archivo del frontend que debes tocar.

**Qué hacer:**
1. Reemplaza la llamada a `/api/recursos?limit=1` por `/api/stats/resumen`
2. Usa los datos reales del endpoint para construir las gráficas
3. Agrega llamadas a `/api/stats/ingesta-mensual`, `/api/stats/top-eventos`,
   `/api/stats/top-lugares`

**Ejemplo de cómo consumir los endpoints:**
```javascript
// Al inicio de la función render():
const [resumen, ingestaMensual, topEventos, topLugares] = await Promise.all([
  apiFetch('/api/stats/resumen'),
  apiFetch('/api/stats/ingesta-mensual'),
  apiFetch('/api/stats/top-eventos'),
  apiFetch('/api/stats/top-lugares'),
]);

// Los datos llegan así:
resumen.total_recursos      // número
resumen.fuentes_activas     // número
resumen.por_plataforma      // [{ plataforma: "TikTok", count: 792 }, ...]
resumen.por_estado          // [{ estado: "Crudo", count: 792 }, ...]
ingestaMensual.data         // [{ periodo: "2025-11", count: 45 }, ...]
topEventos.data             // [{ nombre: "FIAVL", count: 234 }, ...]
topLugares.data             // [{ nombre: "Teatro Benjamín Carrión", count: 89 }, ...]
```

**Para calcular los porcentajes de las barras:**
```javascript
const maxPlat = Math.max(...resumen.por_plataforma.map(p => p.count), 1);
// pct de cada barra = Math.round((item.count / maxPlat) * 100)
```

---

## 4. Cosas que NO debes tocar

| Archivo | Por qué no tocarlo |
|---------|-------------------|
| `backend/database.py` | Conexión a MongoDB, la tocan todos los módulos |
| `backend/schemas.py` | Validación de documentos, crítico |
| `backend/connectors/*` | Los conectores ETL, módulo separado |
| `backend/etl/pipeline.py` | Pipeline de transformación |
| `frontend/app.js` | Router principal, catálogos globales |
| `frontend/components/*` | Componentes reutilizables |
| `frontend/views/database.js` | Vista de base de datos |
| `frontend/views/etl.js` | Vista de ingesta |
| `frontend/index.html` | Solo si necesitas agregar CSS nuevo |

---

## 5. Reglas del proyecto que debes respetar

**Backend:**
- Todos los endpoints devuelven siempre `{ "exito": True, ... }`
- Los nombres de campos en español con snake_case
- No usar `print()` para debug, usa el logger de uvicorn
- No crear colecciones nuevas en MongoDB — usa las que existen:
  `recurso`, `evento`, `edicion`, `lugar`

**Frontend:**
- No usar `fetch()` directo, usar siempre la función `apiFetch()` de
  `components/badges.js` — ya maneja errores y headers
- No usar `alert()` para notificaciones, usar la función `toast(msg, tipo)`
  del mismo archivo (`tipo` puede ser `'ok'` o `'err'`)
- No usar `innerHTML` con datos del usuario sin sanitizar
- El CSS vive en `index.html` en el bloque `<style>` — no crear archivos CSS separados
- Los módulos JS usan `import/export` ES6, no CommonJS

---

## 6. Verificar que funciona

Una vez implementado, estos endpoints deben responder correctamente:

```
GET http://127.0.0.1:8000/api/stats/resumen
GET http://127.0.0.1:8000/api/stats/ingesta-mensual
GET http://127.0.0.1:8000/api/stats/top-eventos
GET http://127.0.0.1:8000/api/stats/top-lugares
```

Ábrelos en el navegador antes de conectarlos al frontend y verifica que
el JSON tiene la estructura esperada.

---

## 7. Resumen en 5 pasos

```
1. CREAR   backend/routes/stats.py          (código del paso 3)
2. EDITAR  backend/routes/__init__.py        (agregar 1 línea)
3. EDITAR  backend/main.py                   (agregar 2 líneas)
4. EDITAR  frontend/views/home.js            (consumir los nuevos endpoints)
5. PROBAR  los 4 endpoints en el navegador antes de conectar el frontend
```

Cualquier duda sobre la estructura del proyecto, consulta el archivo
`guia_implementacion_apis.md` en la raíz del proyecto.
