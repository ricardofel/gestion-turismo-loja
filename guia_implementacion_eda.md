# Guía de Implementación — Módulo EDA (Home / Dashboard)
## Proyecto ETL Turismo Loja · UTPL 2026
### Actualizado 2026-07 — la mayor parte de esto ya está hecho, lee el estado antes de empezar

---

## 0. Estado actual — léelo antes de tocar nada

Esta guía originalmente describía crear todo el módulo de estadísticas desde
cero. **Ya no es así.** El dashboard de Home ya está implementado y
funcionando con datos reales. Antes de escribir código, confirma esto
corriendo el proyecto (ver `guia_instalacion.md`) y abriendo la pestaña
Inicio — deberías ver KPIs, gráficas de plataforma/estado, línea de tiempo
de ingesta mensual, y un ranking de eventos con su "evento más popular".

**Lo único que falta es una sección: "Top lugares".** Ver sección 4.

| Dato | Estado |
|------|--------|
| Total de recursos | ✅ Hecho — `/api/stats/resumen` |
| Distribución por plataforma | ✅ Hecho — `/api/stats/resumen` |
| Distribución por estado de procesamiento | ✅ Hecho — `/api/stats/resumen` |
| Ingesta mensual (línea de tiempo) | ✅ Hecho — `/api/stats/ingesta-mensual` |
| Eventos registrados / lugares registrados (KPI) | ✅ Hecho — catálogos cargados en `app.js` |
| Top eventos por recursos + evento más popular | ✅ Hecho — `/api/stats/eventos` |
| **Top lugares por recursos** | ❌ **Falta — tu tarea** |

---

## 1. Contexto rápido del proyecto

Backend en **FastAPI (Python)**, frontend en **JavaScript puro con ES
Modules** (sin React, sin Vue, sin build tools).

```
gestion-turismo-loja/
├── backend/          ← Python, FastAPI, MongoDB
└── frontend/         ← HTML + JS puro, sin frameworks
```

Para levantar el proyecto completo (backend + frontend + variables de
entorno), sigue `guia_instalacion.md` en la raíz — no lo repito aquí.

---

## 2. Los archivos que vas a modificar

### ARCHIVO 1 — Backend: `backend/routes/stats.py` (YA EXISTE — agrega un endpoint)

Ya tiene `/resumen`, `/ingesta-mensual` y `/eventos`. Agrega `/top-lugares`
siguiendo el mismo patrón que `stats_eventos()` (líneas 89-134 del archivo):

```python
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
        lugar = col_lugar.find_one({"_id": item["_id"]}, {"nombre": 1, "tipo_lugar": 1})
        if lugar:
            resultado.append({
                "nombre"    : lugar["nombre"],
                "tipo_lugar": lugar.get("tipo_lugar", ""),
                "count"     : item["count"],
            })

    return {"exito": True, "data": resultado}
```

`COL_LUGAR` ya está importado en el archivo (se usa en el import de
`database` al inicio). No hace falta tocar `routes/__init__.py` ni
`main.py` — el router `stats_router` ya está registrado, un endpoint nuevo
dentro de un router existente no necesita registro adicional.

### ARCHIVO 2 — Frontend: `frontend/views/home.js` (MODIFICAR)

Agrega la llamada al nuevo endpoint junto a las que ya existen (línea ~24):

```javascript
const [resumen, ingesta, statsEventos, statsLugares] = await Promise.all([
  apiFetch('/api/stats/resumen'),
  apiFetch('/api/stats/ingesta-mensual'),
  apiFetch('/api/stats/eventos'),
  apiFetch('/api/stats/top-lugares'),   // ← nuevo
]);
```

Y agrega una sección de UI para mostrarlo. La forma más simple es reusar el
patrón de barras que ya existe para "Por plataforma" (`chart-card` +
`bar-row`/`bar-track`/`bar-fill`, ver líneas 92-106 del archivo actual), con
un `chart-card` nuevo para "Top lugares" cerca de la sección de eventos.
No hace falta CSS nuevo — las clases `.chart-card`, `.bar-row`, `.bar-track`,
`.bar-fill`, `.bar-count` ya están definidas en `index.html`.

**Importante:** `home.js` ya usa un token de navegación (`esTokenVigente`,
ver `components/nav-state.js`) para evitar que el dashboard se pinte encima
de otra vista si el usuario navega antes de que termine de cargar. Si
agregas la llamada a `top-lugares` dentro del mismo `Promise.all`, ese
comportamiento se mantiene automáticamente — no necesitas tocar nada de esa
lógica.

---

## 3. Cosas que NO debes tocar

| Archivo | Por qué no tocarlo |
|---------|-------------------|
| `backend/database.py` | Conexión a MongoDB, la tocan todos los módulos |
| `backend/schemas.py` | Validación de documentos, crítico |
| `backend/connectors/*` | Conectores ETL, módulo separado (ver `guia_implementacion_apis.md`) |
| `backend/etl/pipeline.py` | Pipeline de transformación |
| `frontend/app.js` | Router principal, catálogos globales, token de navegación |
| `frontend/components/*` | Componentes reutilizables |
| `frontend/views/database.js` | Vista de base de datos |
| `frontend/views/etl.js` | Vista de ingesta |
| `frontend/index.html` | Solo si necesitas una clase CSS que realmente no exista |

---

## 4. Reglas del proyecto que debes respetar

**Backend:**
- Todos los endpoints devuelven siempre `{ "exito": True, ... }`
- Los nombres de campos en español con snake_case
- No usar `print()` para debug en código nuevo de este módulo
- No crear colecciones nuevas en MongoDB — usa las que existen:
  `recurso`, `evento`, `edicion`, `lugar`

**Frontend:**
- No usar `fetch()` directo, usar siempre `apiFetch()` de
  `components/badges.js` — ya maneja errores y headers
- No usar `alert()` para notificaciones, usar `toast(msg, tipo)` del mismo
  archivo (`tipo` puede ser `'ok'` o `'err'`)
- No usar `innerHTML` con datos del usuario sin sanitizar
- El CSS vive en `index.html` en el bloque `<style>` — no crear archivos
  CSS separados
- Los módulos JS usan `import/export` ES6, no CommonJS

---

## 5. Verificar que funciona

```
GET http://127.0.0.1:8000/api/stats/top-lugares
```

Ábrelo en el navegador antes de conectarlo al frontend y verifica que el
JSON tiene la estructura `{ "exito": true, "data": [{ "nombre": ..., "count": ... }, ...] }`.

Luego, en el Home, confirma que la nueva sección aparece con datos reales y
que no rompe el resto del dashboard (KPIs, gráficas de plataforma/estado,
ingesta mensual y eventos deben seguir funcionando igual).
