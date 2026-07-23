# Guía de Implementación — Módulo EDA (Home / Dashboard / Reviews)
## Proyecto ETL Turismo Loja · UTPL 2026
### Actualizado 2026-07 — el módulo EDA está terminado, este documento ahora es de referencia

---

## 0. Estado actual — todo lo planeado originalmente ya está hecho

Esta guía originalmente describía crear el módulo de estadísticas desde
cero, y luego agregar solo "Top lugares". **Ambas etapas ya se completaron
y el alcance creció bastante más** — el dashboard de Inicio tiene análisis
exploratorio completo, y se agregó un módulo nuevo (**Reviews**) dedicado a
las reseñas de Google. Antes de tocar código, corre el proyecto (ver
`guia_instalacion.md`) y revisa las pestañas **Inicio** y **Reviews** para
ver el estado real.

| Sección (Inicio) | Estado |
|------|--------|
| KPIs generales (recursos, fuentes, eventos, lugares) | ✅ Hecho — `/api/stats/resumen` |
| Distribución por plataforma (gráfico circular) | ✅ Hecho — `/api/stats/resumen` |
| Distribución por estado de procesamiento | ✅ Hecho — `/api/stats/resumen` |
| Ingesta mensual, con filtro interactivo por rango de fechas | ✅ Hecho — `/api/stats/ingesta-mensual?desde=&hasta=` |
| Comparación mes actual vs. mes anterior | ✅ Hecho — calculado en el frontend con los mismos datos |
| Alcance de YouTube (vistas/likes/comentarios + video más visto) | ✅ Hecho — `/api/stats/engagement` |
| Hashtags más usados (nube de palabras) | ✅ Hecho — `/api/stats/hashtags` |
| Palabra más repetida en descripciones | ✅ Hecho — `/api/stats/palabras-frecuentes` |
| Top eventos por recursos + evento más popular | ✅ Hecho — `/api/stats/eventos` |
| Top lugares por recursos, con buscador | ✅ Hecho — `/api/stats/top-lugares?limite=` |
| Mapa de puntos de lugares (por cantidad de recursos) | ✅ Hecho — calculado en el frontend con lat/lon de `top-lugares` |

| Sección (Reviews) | Estado |
|------|--------|
| Resumen de calificaciones (promedio, % Local Guides, distribución de estrellas) | ✅ Hecho — `/api/stats/reviews-resumen` |
| Lugares con más reseñas + calificación promedio | ✅ Hecho — `/api/stats/reviews-por-lugar` |
| Listado de reseñas, filtrable por lugar/calificación/orden/fecha | ✅ Hecho — `/api/stats/reviews-recientes` |
| Paginación ("Cargar más") en el listado | ✅ Hecho — parámetros `offset`/`total`/`hay_mas` |
| Galería de fotos por lugar | ✅ Hecho — `/api/stats/reviews-imagenes` |
| Ocultar fotos que no corresponden al lugar | ✅ Hecho — `/api/stats/reviews-imagenes/ocultar` + colección `imagen_oculta` |

**Si necesitas agregar algo nuevo a cualquiera de las dos vistas**, el
patrón a seguir es el mismo que se usó para todo lo anterior: un endpoint
nuevo en `backend/routes/stats.py` (siempre devolviendo
`{"exito": true, ...}`), y una llamada + bloque de UI nuevo en
`frontend/views/home.js` o `frontend/views/reviews.js` según corresponda,
reusando las clases CSS que ya existen (`chart-card`, `bar-row`,
`stat-card`, `.card`, etc. — todas viven en `index.html`).

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

## 2. Archivos involucrados en el módulo EDA/Reviews

### Backend

- `backend/routes/stats.py` — todos los endpoints de estadísticas de
  Inicio y de Reviews viven aquí. Once endpoints en total a la fecha:
  `/resumen`, `/ingesta-mensual`, `/eventos`, `/top-lugares`, `/engagement`,
  `/hashtags`, `/palabras-frecuentes`, `/reviews-resumen`,
  `/reviews-por-lugar`, `/reviews-recientes`, `/reviews-imagenes` y
  `/reviews-imagenes/ocultar`.
- `backend/connectors/google_reviews.py` — conector real de Google Reviews
  vía SerpApi (ver `guia_implementacion_apis.md` para el detalle de esta
  integración).
- `backend/database.py` — agrega la colección `imagen_oculta` (URLs de
  fotos marcadas como "no corresponde" desde la galería).

### Frontend

- `frontend/views/home.js` — dashboard de Inicio completo.
- `frontend/views/reviews.js` — vista nueva, dedicada a Google Reviews
  (estadísticas, listado filtrable, galería de fotos).
- `frontend/views/lugares.js` — se agregó el campo **"ID de Google Maps"**
  (`google_data_id`) para poder asociar reviews reales a cada lugar.
- `frontend/app.js` — se agregó la ruta `reviews` y su entrada en el menú.
- `frontend/index.html` — se agregó el botón de navegación "Reviews".

### Scripts de mantenimiento (`backend/scripts/`)

- `importar_reviews_manual.py` / `importar_reviews_sinteticas.py` — para
  cargar datasets de ejemplo/prueba (no reseñas reales), usados solo
  durante el desarrollo de este módulo.
- `limpiar_reviews_prueba.py` — borra datos mock/de prueba de la colección
  `recurso` antes de una extracción real (requiere `--confirmar`).
- `ver_tamano_bd.py` — reporta el tamaño real de la base de datos contra
  el límite del plan de MongoDB Atlas (ej. 500 MB en el tier gratuito).

---

## 3. Cosas que NO debes tocar sin coordinarlo con el equipo

| Archivo | Por qué no tocarlo a la ligera |
|---------|-------------------|
| `backend/database.py` | Conexión a MongoDB, la tocan todos los módulos |
| `backend/schemas.py` | Validación de documentos, crítico |
| `backend/connectors/base.py` | Clase base de todos los conectores |
| `backend/etl/pipeline.py` | Pipeline de transformación de todas las fuentes |
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
- No usar `print()` para debug en código nuevo de este módulo (los
  conectores sí usan `print()` deliberadamente, para dar visibilidad del
  progreso de extracción en la terminal — eso es intencional, no un error)
- No crear colecciones nuevas en MongoDB sin necesidad real — la única
  colección nueva que se agregó en este módulo es `imagen_oculta`, y fue
  deliberado (permite revertir el ocultamiento de una foto sin tocar la
  reseña original)

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
GET http://127.0.0.1:8000/api/stats/resumen
GET http://127.0.0.1:8000/api/stats/reviews-resumen
```

Ábrelos en el navegador y confirma que devuelven `"exito": true` con datos.
Luego, en el sistema, confirma que **Inicio** y **Reviews** cargan sin
errores en la consola del navegador (F12 → Console) y que los filtros de
cada sección (fechas, calificación, lugar) responden correctamente.
