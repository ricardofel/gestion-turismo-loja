<div align="center">

# 🏔️ Data Turismo Loja

### Motor ETL y API RESTful para la gestión de recursos turísticos de Loja, Ecuador

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Proyecto académico · Universidad Técnica Particular de Loja (UTPL) · 2026

</div>

---

## ¿Qué es esto?

Un sistema que **ingiere contenido real de redes sociales** (YouTube y
Google Reviews) sobre atractivos turísticos de Loja, lo clasifica
automáticamente por **lugar**, **evento** y **edición**, y lo expone en un
dashboard con estadísticas y un panel de administración para curar los
datos a mano cuando la detección automática no alcanza.

No es una demo con datos inventados: corre contra un cluster real de
MongoDB Atlas compartido por todo el equipo. YouTube trae videos reales
con deduplicación propia, y Google Reviews trae reseñas reales (texto,
calificación, autor y fotos) vía SerpApi — una página por lugar y
extracción (hasta 20 reseñas; sin paginación automática por ahora).

## ✨ Características

- **Ingesta ETL real** desde YouTube Data API v3 y Google Reviews (vía
  SerpApi), con control de cuota diaria y caché para no desperdiciarla.
- **Detección automática** de lugar y evento/edición a partir del texto del
  contenido — y si no existe la edición correspondiente a un año detectado,
  el sistema **la crea sola**, calculando su estado (Planificada / En curso
  / Finalizada) por calendario.
- **Deduplicación** — un mismo video/reseña nunca se inserta dos veces, sin
  importar cuántas veces se vuelva a extraer.
- **CRUD completo** de Lugares, Eventos y Ediciones, con buscador en vivo,
  detección de nombres duplicados/parecidos (typos, variantes de redacción)
  antes de guardar, y aviso de impacto antes de eliminar algo que otros
  recursos usan.
- **Editor de recursos enriquecido** — permite reasignar lugar y evento →
  edición (en cascada) a mano, para los casos donde la detección automática
  no encontró coincidencia.
- **Dashboard con estadísticas reales**: distribución por plataforma
  (circular) y estado, línea de tiempo de ingesta mensual con filtro
  interactivo por rango de fechas y comparación automática contra el mes
  anterior, alcance de YouTube (vistas/likes/comentarios y video más
  visto), nube de hashtags y palabra más repetida, mapa de puntos de
  lugares turísticos, buscador de lugares, y ranking de eventos por
  recursos asociados.
- **Módulo Reviews** — panel dedicado a las reseñas de Google: resumen de
  calificaciones, lugares mejor calificados, palabras más repetidas,
  listado de reseñas filtrable por lugar/calificación/fecha con
  paginación ("Cargar más"), y una **galería de fotos por lugar** con
  opción de ocultar fotos que no correspondan al sitio (sin borrar la
  reseña completa).
- **Diseñado para bajo presupuesto** — YouTube es gratuita, Google Reviews
  es pago por uso vía SerpApi (sin tarjeta de crédito de Google Cloud, sin
  aprobación de terceros).

## 🛠️ Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11 · FastAPI · Pydantic · PyMongo |
| Base de datos | MongoDB Atlas (cluster compartido en la nube) |
| Frontend | HTML + JavaScript puro (ES Modules) · sin frameworks ni build step |
| Estilos | CSS propio + Tailwind (CDN, solo utilidades puntuales) |
| Ingesta | YouTube Data API v3 · Google Reviews (vía SerpApi) |

Sin React, sin Vue, sin bundlers — el frontend es JS nativo servido tal cual.

## 🚀 Empezar

Instrucciones completas de instalación (entorno virtual, dependencias,
variables de entorno, cómo levantar backend y frontend) en
**[`guia_instalacion.md`](guia_instalacion.md)**.

Resumen exprés:

```bash
git clone <url-del-repositorio> && cd gestion-turismo-loja
python -m venv venv && venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
cp backend/.env.example backend/.env               # completar con las credenciales del equipo
uvicorn backend.main:app --reload                  # backend en :8000
cd frontend && python -m http.server 5500          # frontend en :5500
```

> Este proyecto usa un **cluster de MongoDB Atlas compartido por todo el
> equipo** — no montes uno local. Pide la cadena de conexión a quien lo
> administra (ver `guia_instalacion.md` para el detalle).

## 📁 Estructura del proyecto

```
gestion-turismo-loja/
├── backend/
│   ├── main.py           ← punto de entrada FastAPI
│   ├── database.py       ← conexión a MongoDB
│   ├── schemas.py        ← validación Pydantic
│   ├── connectors/       ← conectores ETL (YouTube y Google Reviews reales)
│   ├── etl/pipeline.py   ← transformación, deduplicación, detección
│   ├── scripts/          ← utilidades de mantenimiento de datos
│   └── routes/           ← endpoints de la API
└── frontend/
    ├── index.html        ← shell + estilos
    ├── app.js             ← router de la SPA
    ├── views/              ← una vista por sección (Inicio, Base de Datos, ETL, Reviews...)
    └── components/          ← piezas reutilizables (autocomplete, modales, etc.)
```

## 📚 Documentación

| Archivo | Contenido |
|---|---|
| [`guia_instalacion.md`](guia_instalacion.md) | Cómo levantar el proyecto de cero |
| [`obtener_credenciales.md`](obtener_credenciales.md) | Cómo crear cada cuenta/API key desde cero (MongoDB Atlas, YouTube, SerpApi) |
| [`guia_despliegue_render.md`](guia_despliegue_render.md) | Despliegue en Render: por qué está sin credenciales, y cómo activarlas cuando corresponda |

> **Nota:** el despliegue en Render tiene actualmente credenciales reales
> configuradas **temporalmente**, para una revisión puntual con la
> docente — no es el estado definitivo. Detalle completo, incluyendo
> cuándo y cómo quitarlas después, en `guia_despliegue_render.md`.

## Licencia

[MIT](LICENSE) © 2026 Ricardo E.
