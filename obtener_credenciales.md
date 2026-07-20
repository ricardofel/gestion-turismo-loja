# Cómo Obtener las Credenciales del Proyecto
## Proyecto ETL Turismo Loja · UTPL 2026

Guía paso a paso para crear, desde cero, cada cuenta/API key que el proyecto
necesita en `backend/.env`. Pensada para que quien registre las cuentas
(ej. la tutora, a su nombre y su correo) sepa exactamente a dónde entrar y
qué botón presionar — sin conocimiento previo de la herramienta.

Al final de cada sección se indica **qué valor exacto va en `backend/.env`**.

---

## 1. MongoDB Atlas (base de datos — `MONGO_URI` y `MONGO_DB`)

MongoDB Atlas es la base de datos en la nube donde vive todo (recursos,
lugares, eventos, ediciones). Es gratuita en el tier "Shared" (M0, hasta
512 MB), suficiente para este proyecto.

1. Entra a [mongodb.com/cloud/atlas/register](https://www.mongodb.com/cloud/atlas/register)
   y crea una cuenta (con correo y contraseña, o con cuenta de Google).
2. Al terminar el registro te pedirá crear un primer proyecto/organización —
   acepta los nombres por defecto o ponle "Turismo Loja".
3. Te va a proponer crear un cluster. Elige:
   - **Tipo:** M0 Free (gratis, marcado como "FREE" — no elijas Dedicated/Serverless).
   - **Proveedor/región:** cualquiera, de preferencia AWS y una región de
     Sudamérica (ej. São Paulo) para menor latencia.
   - Nombre del cluster: el que quieras (ej. `TurismoLoja`).
4. **Crear usuario de base de datos** (te lo pide en el mismo flujo o en
   *Database Access* del menú lateral):
   - Username y password — **guarda ese password**, es distinto al de tu
     cuenta de Atlas y se usa en la cadena de conexión.
5. **Network Access** (menú lateral) → *Add IP Address*:
   - Para que cualquiera del equipo se pueda conectar sin pedir whitelist
     por cada persona, se puede agregar `0.0.0.0/0` ("Allow access from
     anywhere"). Es una base académica sin datos sensibles, así que es
     aceptable; si se prefiere más control, hay que agregar la IP de cada
     integrante manualmente cuando falle la conexión.
6. Ve a **Database** (menú lateral) → botón **Connect** en el cluster →
   elige **"Drivers"** → copia la cadena que aparece, tipo:
   ```
   mongodb+srv://<username>:<password>@turismoloja.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
   Reemplaza `<username>` y `<password>` por los del paso 4 (si el password
   tiene caracteres especiales como `@` o `/`, hay que codificarlos con
   [URL-encoding](https://www.mongodb.com/docs/atlas/troubleshoot-connection/#special-characters-in-connection-string-password)).
7. Crea también la base de datos y colección inicial (o se crean solas al
   primer insert): el nombre de la base debe ser exactamente `turismo_loja`.

**Va en `backend/.env`:**
```
MONGO_URI=mongodb+srv://usuario:password@turismoloja.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGO_DB=turismo_loja
```

> **Nota sobre MongoDB Compass:** Compass es solo un programa de escritorio
> para *ver* los datos con una interfaz gráfica (como un Excel de la base).
> No es una credencial ni es obligatorio para que el proyecto funcione —
> el backend se conecta directo con `MONGO_URI`. Si de todos modos se quiere
> instalar para inspeccionar los datos a simple vista: descargar en
> [mongodb.com/products/tools/compass](https://www.mongodb.com/products/tools/compass),
> abrir la app, y pegar la misma cadena de conexión del paso 6 en el campo
> "connection string" al abrir Compass.

---

## 2. YouTube Data API v3 (`YOUTUBE_API_KEY`)

Ya está activa y en uso — se documenta aquí por si se necesita generar una
key nueva a nombre de la tutora (por ejemplo, para tener una key "oficial"
del proyecto en vez de la personal de un estudiante).

1. Entra a [console.cloud.google.com](https://console.cloud.google.com) con
   una cuenta de Google (Gmail cualquiera sirve).
2. Arriba, junto al logo "Google Cloud", haz clic en el selector de
   proyecto → **New Project**. Nómbralo, ej. `turismo-loja` → **Create**.
3. Con el proyecto ya seleccionado, ve al menú ☰ → **APIs & Services** →
   **Library**.
4. Busca **"YouTube Data API v3"** → ábrela → botón **Enable**.
5. Ve a **APIs & Services** → **Credentials** → **+ Create Credentials** →
   **API key**. Se genera una key tipo `AIzaSy...` — cópiala.
6. (Opcional pero recomendado) clic en la key recién creada → en
   "API restrictions" selecciona **Restrict key** → marca solo
   "YouTube Data API v3", para que esa key no pueda usarse en otras APIs de
   Google si se filtra.

No pide tarjeta de crédito. Cuota gratis: 10,000 unidades/día (~99
extracciones diarias con el patrón actual del proyecto).

**Va en `backend/.env`:**
```
YOUTUBE_API_KEY=AIzaSy...
```

---

## 3. SerpApi (`SERPAPI_KEY`) — nueva, para agregar más fuentes vía Google

SerpApi entrega resultados de Google (Búsqueda, Maps, Reseñas, Imágenes,
etc.) ya en JSON estructurado, sin necesitar una cuenta de Google Cloud con
tarjeta de crédito (a diferencia de Google Places API, que el equipo ya
descartó por eso — ver `guia_implementacion_apis.md`).

1. Entra a [serpapi.com](https://serpapi.com) → **Register** (arriba a la
   derecha).
2. Crea la cuenta con correo y contraseña (o con Google/GitHub).
3. Verifica el correo si te lo pide (revisa spam).
4. Al iniciar sesión, el plan por defecto es **Free** — 100 búsquedas al
   mes, no pide tarjeta de crédito para este plan.
5. Ve a **Dashboard** (o directo a
   [serpapi.com/manage-api-key](https://serpapi.com/manage-api-key)) — ahí
   aparece el **"Your Private API Key"**, un string largo alfanumérico.
   Cópialo.

Con el plan Free alcanza para pruebas y desarrollo; si el proyecto necesita
más de 100 búsquedas/mes habría que evaluar un plan pago más adelante.

**Va en `backend/.env`:**
```
SERPAPI_KEY=el_key_que_copiaste
```

---

## 4. Fuentes descartadas — solo si en el futuro hay presupuesto

`guia_implementacion_apis.md` documenta otras fuentes que se evaluaron y
quedaron pausadas por costo o aprobación incierta (Flickr Pro, Apify para
TikTok/Instagram/TripAdvisor, Google Places con tarjeta). Si la tutora
decide invertir en alguna, ese archivo ya tiene el detalle de qué pediría
cada una y su costo aproximado — no hace falta repetirlo aquí hasta que se
decida activar una.

---

## Resumen de variables para `backend/.env`

```
MONGO_URI=mongodb+srv://usuario:password@cluster.mongodb.net/
MONGO_DB=turismo_loja
YOUTUBE_API_KEY=AIzaSy...
SERPAPI_KEY=...
```

Una vez generadas, quien administre las cuentas comparte estos valores por
un canal privado (no chat público ni commit) a cada integrante, que los
pega en su `backend/.env` local siguiendo `guia_instalacion.md`.
