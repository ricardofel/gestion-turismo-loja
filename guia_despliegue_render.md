# Guía de Despliegue en Render
## Proyecto ETL Turismo Loja · UTPL 2026

---

## 1. Contexto: por qué está desplegado sin credenciales

Este proyecto se hostea en [Render](https://render.com), pero **sin la 
cadena de conexión de MongoDB Atlas ni la API Key
de YouTube usadas en desarrollo**, porque esas credenciales pertenecen a
cuentas personales del equipo (ver `obtener_credenciales.md`) y no deben
quedar expuestas en un servicio público.

Por eso, el despliegue en Render es **decorativo por ahora**: sirve para
mostrar que la aplicación compila, arranca y la interfaz carga
correctamente, pero **sin base de datos ni ingesta real conectada**. Esto
es intencional y no es un error de configuración.

El backend está preparado para esto sin necesitar ningún cambio de código:
si no hay `MONGO_URI` configurada, el servidor arranca igual (la conexión a
Mongo es "perezosa", solo se intenta en la primera petición que la
necesita — ver `backend/database.py`) y cada endpoint que depende de la
base de datos responde con un error controlado (503) en vez de tumbar el
servicio. El punto `/api/health` siempre responde 200, indicando
`"mongodb": "desconectado"` cuando no hay credenciales.

**Qué vas a ver en el deploy actual:**
- La interfaz completa carga con normalidad (sidebar, vistas, estilos).
- El indicador de estado en la esquina superior derecha muestra "Sin base
  de datos" (punto rojo) — esperado.
- Las vistas que dependen de datos (Inicio, Base de Datos, ETL) se ven
  vacías o muestran mensajes tipo "Sin datos aún" — esperado.
- No hay forma de ingerir contenido real ni de ver los ~2400 recursos que
  sí existen en el cluster compartido de desarrollo — esperado, porque ese
  cluster no está conectado aquí.

---

## 2. Arquitectura del despliegue

Se usa **un solo servicio Render** (Web Service, plan Free) para todo el
proyecto: el backend de FastAPI sirve la API bajo `/api/*` **y además**
sirve los archivos estáticos del frontend (`frontend/`) en la raíz `/`,
desde el mismo proceso (`backend/main.py`, al final del archivo). Esto
evita tener que desplegar dos servicios separados, configurar CORS entre
dos dominios distintos, o que el frontend necesite saber la URL pública del
backend — todo vive en una sola URL.

La configuración de build/arranque está en **`render.yaml`**, en la raíz
del repositorio (formato *Blueprint* de Render):

```yaml
buildCommand: pip install -r requirements.txt
startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
healthCheckPath: /api/health
```

Si el servicio en Render se conecta a este repositorio como *Blueprint*,
Render lee este archivo solo y detecta las variables de entorno que hacen
falta (ver sección 4), pidiéndolas vacías la primera vez.

---

## 3. Variables de entorno que usa el proyecto

| Variable | Para qué sirve | ¿Obligatoria? | Cómo conseguirla |
|---|---|---|---|
| `MONGO_URI` | Cadena de conexión al cluster de MongoDB Atlas | Sí, para que haya datos | `obtener_credenciales.md`, sección 1 |
| `MONGO_DB` | Nombre de la base de datos (`turismo_loja`) | Sí, pero tiene un valor por defecto correcto | No aplica — no cambiar |
| `YOUTUBE_API_KEY` | Ingesta real desde YouTube Data API v3 | Solo si se quiere usar el módulo ETL | `obtener_credenciales.md`, sección 2 |
| `SERPAPI_KEY` | Fuente adicional vía SerpApi (si se llega a implementar) | No, futura | `obtener_credenciales.md`, sección 3 |

Ninguna de estas cuatro variables está en el repositorio, ni en
`render.yaml` (los valores de las tres primeras están marcados como
`sync: false`, que en Render significa "esta variable existe pero su valor
se configura manualmente y no se guarda en el archivo versionado").

---

## 4. Cómo crear el `.env` para correr el proyecto en LOCAL

Esto es para desarrollo en tu máquina, no afecta a Render.

1. En la raíz del repo, entra a la carpeta `backend/`.
2. Copia la plantilla:
   ```bash
   cp backend/.env.example backend/.env
   ```
3. Abre el archivo recién creado, **`backend/.env`** (esa es la ubicación
   exacta — no en la raíz del proyecto, sino dentro de `backend/`), y
   completa:
   ```
   MONGO_URI=mongodb+srv://usuario:password@cluster.mongodb.net/
   MONGO_DB=turismo_loja
   YOUTUBE_API_KEY=tu_api_key_de_youtube
   SERPAPI_KEY=tu_api_key_de_serpapi
   ```
4. Guarda el archivo. **Nunca lo subas a git** — ya está en `.gitignore`
   (`backend/.env`), así que un `git add .` normal no lo va a incluir.
5. Reinicia `uvicorn` si ya estaba corriendo, para que recargue las
   variables (`--reload` vigila archivos `.py`, no `.env`).

Detalle completo de cada variable y de dónde sacar cada credencial en
`obtener_credenciales.md` y en `guia_instalacion.md`.

---

## 5. Cómo configurar esas mismas variables en Render (para activar el hosting con datos reales)

**Importante:** Render **no lee el archivo `backend/.env` del repositorio**
— de hecho no puede, porque ese archivo nunca se sube a git y por lo tanto
nunca llega al servidor. Las variables de entorno en Render se configuran
manualmente desde su panel, y viven solo ahí (nunca en un archivo
versionado).

Pasos, para quien administre el servicio en Render (ej. la tutora, con sus
propias credenciales — ver `obtener_credenciales.md` si necesita crearlas):

1. Entra a [dashboard.render.com](https://dashboard.render.com) y abre el
   servicio (`gestion-turismo-loja` o el nombre que se le haya dado).
2. En el menú lateral del servicio, ve a la pestaña **"Environment"**.
3. Bajo **"Environment Variables"**, agrega cada una con **Add Environment
   Variable**:
   - `MONGO_URI` → pega la cadena de conexión completa (obtenida en
     MongoDB Atlas, ver `obtener_credenciales.md` sección 1).
   - `MONGO_DB` → `turismo_loja`
   - `YOUTUBE_API_KEY` → la key generada en Google Cloud Console (ver
     `obtener_credenciales.md` sección 2).
   - `SERPAPI_KEY` → opcional, solo si se implementa esa fuente.
4. Clic en **Save Changes**. Render redespliega el servicio
   automáticamente con las variables nuevas.
5. Verifica entrando a `https://<tu-servicio>.onrender.com/api/health` —
   debe responder `"mongodb": "conectado"`. Si sigue en "desconectado",
   revisa que la IP de Render esté permitida en **Network Access** de
   MongoDB Atlas (ver nota de whitelist en `guia_instalacion.md`) — para
   un servicio en la nube como Render, lo más simple es dejar
   `0.0.0.0/0` (cualquier IP) en esa whitelist, ya que Render no tiene IP
   fija en el plan gratuito.

No hace falta tocar código ni volver a hacer `git push` para esto — es
puramente configuración en el panel de Render.

---

## 6. Checklist rápido para "activar" el hosting con datos reales

- [ ] Cuenta de MongoDB Atlas creada (propia, no la personal de un
      estudiante) y `MONGO_URI` a mano.
- [ ] Network Access de Atlas con `0.0.0.0/0` (o la IP saliente de Render,
      si se prefiere restringir).
- [ ] API Key de YouTube Data API v3 generada.
- [ ] Las 3-4 variables cargadas en Render → Environment.
- [ ] `https://<tu-servicio>.onrender.com/api/health` responde
      `"mongodb": "conectado"`.
- [ ] Probar en la interfaz: Ingesta ETL → YouTube → extraer con un tag de
      prueba (ej. `fiavl`) y confirmar que trae resultados reales.

Hasta que esos pasos no se hagan, el estado esperado y correcto del deploy
es: interfaz visible, sin datos, punto de estado en rojo. No es un bug.
