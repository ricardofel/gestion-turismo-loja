# Guía de Instalación y Levantamiento del Proyecto
## Proyecto ETL Turismo Loja · UTPL 2026

Pasos para clonar el repositorio y dejar el proyecto corriendo en local desde
cero. El proyecto tiene dos partes independientes: **backend** (FastAPI +
MongoDB) y **frontend** (HTML/JS sin build, ES Modules puros).

---

## 1. Requisitos previos

- Python 3.11+ instalado
- **Acceso al cluster compartido de MongoDB Atlas del equipo**
- Una API Key de YouTube Data API v3 (ver paso 4)
- Una API Key de SerpApi, si vas a trabajar con reseñas de Google (ver paso 4)

> **Sobre la base de datos: todos trabajamos contra la misma instancia.**
> Este proyecto usa **un único cluster de MongoDB Atlas compartido por todo
> el equipo** — no uno local por persona. Esto es intencional: los
> catálogos de Lugares/Eventos/Ediciones y los recursos ingeridos deben ser
> los mismos para todos, para que el trabajo de cada quien (crear un lugar,
> correr una extracción ETL, revisar datos en Base de Datos) sea visible
> para el resto del equipo de inmediato.
>
> Por seguridad, la cadena de conexión (`MONGO_URI`) **no está en este
> repositorio ni en ningún archivo versionado** — pídesela directamente a
> quien administra el cluster (por un canal privado, no por chat público)
> y pégala en tu `backend/.env` local, siguiendo el paso 4. Si tu conexión
> falla con un error de red/timeout, probablemente tu IP no esté en la
> whitelist de Atlas (Network Access) — pide que la agreguen ahí.
>
> No se necesita (ni se recomienda) montar un MongoDB local para este
> proyecto: los datos de prueba, catálogos y credenciales de API ya viven
> en el cluster compartido.

---

## 2. Clonar y crear el entorno virtual

```bash
git clone <url-del-repositorio>
cd gestion-turismo-loja

# Crear entorno virtual
python -m venv venv

# Activar el entorno virtual
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Windows (cmd):
venv\Scripts\activate.bat
# macOS / Linux:
source venv/bin/activate
```

## 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instala FastAPI, Uvicorn, PyMongo, Pydantic, Requests y python-dotenv.

## 4. Configurar variables de entorno

Copia la plantilla y completa tus propios valores:

```bash
cp backend/.env.example backend/.env
```

Edita `backend/.env` con:

```
MONGO_URI=mongodb+srv://usuario:password@cluster.mongodb.net/
MONGO_DB=db_name
YOUTUBE_API_KEY=api_key
SERPAPI_KEY=api_key
```

**Nota:** Pedir los datos del .env al admin, la api key de youtube y la de SerpApi se pueden generar personalmente.

- **MONGO_URI**: la cadena de conexión del **cluster compartido del
  equipo** (no es de cada quien — pídesela a quien lo administra, ver nota
  del paso 1). Nunca la escribas en un commit, issue, PR o chat público.
- **MONGO_DB**: el nombre de la base es `turismo_loja` para todo el equipo
  — no lo cambies, o vas a estar leyendo/escribiendo en una base vacía
  distinta a la del resto.
- **YOUTUBE_API_KEY**: esta sí es individual — cada persona genera la suya,
  gratuita, en [console.cloud.google.com](https://console.cloud.google.com)
  → habilita "YouTube Data API v3" → Credentials → Create API Key. Toma
  2-3 minutos y no pide tarjeta de crédito.
- **SERPAPI_KEY**: también individual, se genera en
  [serpapi.com/manage-api-key](https://serpapi.com/manage-api-key). A
  diferencia de YouTube, SerpApi es de pago por búsqueda (con un tier
  gratuito limitado) — revisa tu consumo en el dashboard de SerpApi antes
  de extraer reseñas de lugares con muchas reviews. Solo hace falta si vas
  a trabajar con la fuente "GoogleReviews".

`backend/.env` nunca se debe subir al repositorio (ya está en `.gitignore`)
— es tuyo, local, y contiene credenciales reales.

## 5. Levantar el backend

```bash
uvicorn backend.main:app --reload
```

- API disponible en `http://127.0.0.1:8000`
- Documentación interactiva (Swagger) en `http://127.0.0.1:8000/docs`
- Prueba rápida de salud: `http://127.0.0.1:8000/api/health` debe devolver
  `"mongodb": "conectado"`

> Nota: `--reload` vigila cambios en archivos `.py`, pero **no** en
> `backend/.env`. Si cambias una variable de entorno, reinicia el server
> manualmente (Ctrl+C y volver a correr el comando) para que se recargue.

## 6. Levantar el frontend

El frontend es HTML/JS plano con ES Modules — no tiene build ni bundler,
pero **no se puede abrir el `index.html` directamente con doble clic**
(los navegadores bloquean `import` de módulos vía `file://`). Necesita
servirse por HTTP. Dos opciones:

**Opción A — servidor simple de Python:**
```bash
cd frontend
python -m http.server 5500
```
Abre `http://localhost:5500` en el navegador.

**Opción B — extensión Live Server de VS Code:**
Clic derecho sobre `frontend/index.html` → "Open with Live Server".

El frontend apunta al backend en `http://127.0.0.1:8000` (definido en
`frontend/components/badges.js`, función `apiFetch`). Si cambias el puerto
del backend, actualiza esa constante.

## 7. Verificar que todo funciona

1. Con el backend y el frontend corriendo, abre el frontend en el navegador.
2. Deberías ver el punto verde "Base de datos conectada" en la esquina
   superior derecha.
3. Ve a **Ingesta ETL** → selecciona YouTube → escribe un tag (ej: `fiavl`)
   → "Extraer datos". Si la API Key es válida, deberían aparecer resultados
   reales de YouTube.
4. Para probar Google Reviews: ve a **Base de Datos → Lugares**, edita
   un lugar y pégale su **"ID de Google Maps"** (`data_id`, se obtiene
   buscando el lugar por nombre o coordenadas en la
   [Google Maps API de SerpApi](https://serpapi.com/google-maps-api)).
   Luego ve a **Ingesta ETL** → selecciona **GoogleReviews** → extrae. Si
   funcionó, la pestaña **Reviews** debería mostrar datos reales de ese
   lugar (calificaciones, texto, y fotos si el usuario subió alguna).

---

## Estructura del proyecto

```
gestion-turismo-loja/
├── backend/
│   ├── main.py              ← punto de entrada FastAPI
│   ├── database.py          ← conexión a MongoDB
│   ├── schemas.py           ← validación Pydantic
│   ├── connectors/          ← conectores ETL (YouTube y Google Reviews reales)
│   ├── etl/pipeline.py      ← transformación, deduplicación, detección
│   ├── scripts/             ← utilidades de mantenimiento de datos
│   └── routes/              ← endpoints de la API
├── frontend/
│   ├── index.html           ← shell + estilos (todo el CSS vive aquí)
│   ├── app.js                ← router de la SPA
│   ├── views/                ← una vista por sección (Home, DB, ETL, Reviews...)
│   └── components/            ← autocomplete, datepicker, badges, etc.
├── guia_implementacion_apis.md   ← qué APIs están activas / disponibles a futuro
├── guia_implementacion_eda.md    ← estado del módulo de estadísticas (Home + Reviews)
└── guia_instalacion.md            ← este archivo
```


## Problemas comunes

- **"mongodb": "desconectado" en /api/health** → revisa `MONGO_URI` en
  `backend/.env` y que tu IP esté en la whitelist de Atlas (Network Access).
- **Extraer datos siempre da 0 resultados** → revisa que `YOUTUBE_API_KEY`
  (o `SERPAPI_KEY`) esté bien copiada en `backend/.env` y que reiniciaste
  uvicorn después de agregarla.
- **"Error: Sin transformador para 'X'" al extraer** → el nombre de la
  fuente debe coincidir EXACTO entre `backend/connectors/registry.py`,
  `backend/etl/pipeline.py` (diccionario `TRANSFORMERS`) y
  `backend/schemas.py` (`PLATAFORMAS_VALIDAS`). El nombre real que exige
  la base para Google es `GoogleReviews` (sin espacio) — si alguno de esos
  3 archivos tiene `"Google Reviews"` con espacio, falla. Ver el validador
  real en `schema_validator_recurso.json` si hay dudas sobre qué valores
  acepta Mongo.
- **Extraer reseñas de Google no trae nada para un lugar** → confirma que
  ese lugar tenga su `google_data_id` guardado (pantalla Lugares). Sin ese
  dato, el conector lo salta silenciosamente (revisa la terminal de
  uvicorn, ahí sale el aviso).
- **El navegador no actualiza los cambios del frontend** → los navegadores
  cachean agresivamente los módulos ES. Haz un hard refresh o abre en una
  ventana de incógnito si algo no se refleja.
