# Guía de Despliegue en Render
## Proyecto ETL Turismo Loja · UTPL 2026

---

## 1. Contexto: estado actual del despliegue

**Actualizado 2026-07-26.** Este documento originalmente decía que el
despliegue en Render era "decorativo, sin credenciales reales" — esa fue
la decisión inicial del equipo, pero **ya no es el estado actual**.

Para una revisión puntual con la docente, se activaron temporalmente las
credenciales reales (`MONGO_URI`, `SERPAPI_KEY`, `YOUTUBE_API_KEY`) en el
panel de Render → Environment. El servicio está **en vivo y conectado al
cluster compartido real** (el mismo que se usa en desarrollo local), no a
una base vacía de demostración.

**Esto es temporal, no la configuración definitiva.** El plan sigue
siendo el mismo que se documentaba originalmente: cuando el proyecto pase
a un despliegue "de verdad" (no solo para una revisión puntual), estas
credenciales de cuentas personales del equipo deben **quitarse** de
Render y reemplazarse por credenciales propias de la institución/tutora
(cuenta de Atlas propia, keys propias) — ver sección 6 actualizada. Dejar
credenciales personales indefinidamente en un servicio público expone:
- El cluster de MongoDB compartido de todo el equipo (accesible por
  cualquiera que encuentre la URL).
- La cuota de SerpApi (de pago por uso) y de YouTube Data API de quien
  puso su key.

**Antes de esa etapa "de verdad":** si alguien nuevo lee esto y encuentra
las credenciales todavía puestas, es señal de que falta el paso de
"apagarlas" tras la revisión — avisar al equipo, no asumir que quedaron
así a propósito para siempre.

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

## 6. Checklist — activar para una revisión, y apagar después

**Para activar (antes de una demo/revisión puntual):**
- [ ] `MONGO_URI`, `MONGO_DB`, `SERPAPI_KEY`, `YOUTUBE_API_KEY` cargadas en
      Render → Environment.
- [ ] Network Access de Atlas permite la conexión desde Render (`0.0.0.0/0`
      en el plan gratuito, ya que Render no da IP fija).
- [ ] `https://<tu-servicio>.onrender.com/api/health` responde
      `"mongodb": "conectado"`.
- [ ] Avisar al equipo (ej. mensaje corto al grupo) que el hosting quedó
      con credenciales reales temporalmente, y para qué/hasta cuándo.

**Para apagar (apenas termine la revisión — no dejarlo así indefinido):**
- [ ] Quitar `MONGO_URI` y `SERPAPI_KEY` de Render → Environment (son las
      de mayor riesgo/costo).
- [ ] Confirmar que `/api/health` vuelve a mostrar `"mongodb":
      "desconectado"`.
- [ ] Revisar el consumo real de SerpApi en su dashboard durante la
      ventana en que estuvo activo, para descartar uso inesperado.
- [ ] Si se restringió la whitelist de Atlas solo para esto, evaluar
      volver a cerrarla.

Cuando el proyecto tenga un despliegue "de verdad" (no solo para una
revisión), estas credenciales deben ser las de una cuenta propia de la
institución/tutora, no las personales de un estudiante del equipo.
