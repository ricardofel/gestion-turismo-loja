# Guía de Integración — APIs Reales
## Proyecto ETL Turismo Loja · UTPL 2026

---

## Estado actual (2026-07)

**YouTube Data API v3** y **Google Reviews (vía SerpApi)** están activas
como fuentes reales. Ambas son viables sin depender de aprobaciones de
terceros: YouTube es 100% gratuita, y Google Reviews vía SerpApi es de
pago por uso (no requiere tarjeta de Google Cloud ni aprobación).

El resto de fuentes que se evaluaron quedaron **descartadas por ahora** —no
por falta de interés, sino porque no son viables sin inversión económica o
sin procesos de aprobación largos e inciertos. Quedan documentadas más abajo
por si en el futuro el proyecto cuenta con presupuesto o tiempo para
gestionar la aprobación.

```
backend/connectors/
  base.py            ← clase base ConectorBase, no se toca
  registry.py        ← registro de conectores activos (YouTube + GoogleReviews)
  youtube.py         ← ConectorYouTubeReal, conectado a YouTube Data API v3
  google_reviews.py  ← ConectorGoogleReviews, conectado a SerpApi (google_maps_reviews)
```

**Regla:** el método `extraer_raw()` de un conector debe devolver siempre una
`list[dict]` con los datos en formato crudo de la API. El pipeline ETL
(`backend/etl/pipeline.py`) se encarga del resto (transformar, deduplicar,
detectar lugar y edición).

---

## Fuentes activas

### YouTube Data API v3 — ACTIVA
- Gratuita, activación inmediata (minutos), sin aprobación de terceros.
- Cuota: 10,000 unidades/día. Cada extracción consume ~101 unidades
  (100 de `search.list` + 1 de `videos.list`).
- El conector (`backend/connectors/youtube.py`) controla la cuota desde el
  código: se corta en 9,000/10,000 unidades para dejar margen, y cachea cada
  búsqueda 1 hora para no repetir llamadas idénticas.
- Configuración: agrega `YOUTUBE_API_KEY=AIza...` a `backend/.env`.
  Se obtiene en [console.cloud.google.com](https://console.cloud.google.com)
  → habilitar "YouTube Data API v3" → Credentials → Create API Key.

### Google Reviews (vía SerpApi) — ACTIVA
- **No es la Google Places API** (esa sigue descartada más abajo, por la
  tarjeta de crédito). SerpApi es un servicio intermediario de pago por
  búsqueda que hace de "scraper" de Google Maps sin necesidad de cuenta de
  facturación de Google Cloud.
- Identifica un lugar por su `data_id` (no por nombre) — cada lugar del
  catálogo necesita este dato guardado en el campo **"ID de Google Maps"**
  desde la pantalla Lugares del sistema. Se obtiene buscando el lugar (por
  nombre o coordenadas GPS) en la
  [Google Maps API de SerpApi](https://serpapi.com/google-maps-api) y
  copiando el `data_id` del resultado.
- El conector (`backend/connectors/google_reviews.py`) pagina
  automáticamente con `next_page_token` hasta traer **todo el histórico
  disponible** de cada lugar (sin tope de negocio, solo un límite de
  seguridad técnico de 500 páginas por lugar).
- **Limitación conocida de Google, no del conector:** para negocios con
  muchas reseñas, Google deja de exponer más resultados vía paginación
  bastante antes de llegar al total que muestra públicamente en la
  interfaz de Maps (ej: un lugar con 1,091 reseñas mostradas puede devolver
  solo ~400-450 vía API). Es una restricción del lado de Google, documentada
  también por SerpApi, y no hay forma de evitarla desde el cliente.
- Costo: pago por búsqueda en tu cuenta SerpApi (cada página de hasta 20
  reseñas = 1 búsqueda). Un lugar con muchas reseñas puede consumir bastante
  cuota — revisa tu dashboard de SerpApi después de extraer.
- Configuración: agrega `SERPAPI_KEY=...` a `backend/.env`. Se obtiene en
  [serpapi.com/manage-api-key](https://serpapi.com/manage-api-key).

---

## Fuentes descartadas (requieren inversión o aprobación incierta)

### Flickr — requiere plan Pro de pago
Hasta 2025 la API era 100% gratuita. Flickr cambió su política: **crear una
API key nueva ahora exige una suscripción Flickr Pro** (de pago). El conector
real ya estaba escrito (`ConectorFlickrReal`, con caché y manejo de errores)
pero se retiró del proyecto porque no hay forma de generar la key sin pagar.
Si en el futuro se consigue una cuenta Pro, el patrón a seguir es el mismo
que `youtube.py`: llamar a `flickr.photos.search` con bounding box de Loja
(`-79.35,-4.45,-79.05,-3.75`) y mapear la respuesta al esquema `RecursoSchema`.

### Eventbrite — API pública de búsqueda descontinuada
Eventbrite descontinuó el endpoint público `/events/search/` para apps
nuevas hace varios años. Una API key nueva solo puede leer los eventos de
**la propia organización del desarrollador**, no buscar eventos públicos de
terceros. No es viable para este proyecto salvo que la universidad publique
sus propios eventos como organizador en Eventbrite.

### TripAdvisor Content API — aprobación reservada a socios comerciales
En la práctica esta API está limitada casi exclusivamente a socios de la
industria de viajes. Proyectos académicos pequeños suelen ser rechazados o
no reciben respuesta. Requiere gestión activa y sin garantía de éxito.

### Google Places API — requiere tarjeta de crédito (reviews ya resueltas por otra vía)
Google reestructuró el pricing de Maps Platform: ya no existe el crédito
plano de $200/mes para todo, ahora es un tier gratuito por SKU. Además,
**exige una cuenta de facturación con tarjeta de crédito activa** para
poder crear la key, aunque el uso se mantenga en $0. Costo real si se activa
con volumen: ~$17 por 1,000 reseñas. **Esta limitación ya no bloquea las
reseñas de Google** — se resolvió por otra vía (SerpApi, ver "Fuentes
activas" arriba), que no pide tarjeta de crédito. Esta API seguiría siendo
útil si en el futuro se necesita, por ejemplo, autocompletado de
direcciones o datos oficiales de Google Places distintos a reseñas.
- Opción de pago sin tarjeta de Google: Apify Google Maps Reviews Scraper
  (~$20/mes) — alternativa a SerpApi si hiciera falta.

### TikTok Research API — acceso académico incierto para instituciones fuera de EEUU/UE
El acceso académico de TikTok ha estado históricamente limitado a
instituciones de ciertas regiones, con procesos de aprobación de 2-4+
semanas y sin garantía de aprobación para una universidad ecuatoriana.
- Alternativa de pago sin aprobación: Apify TikTok Scraper (~$30/mes).

### Instagram Graph API — requiere App Review de Meta
Requiere cuenta Business/Creator + Facebook App con **App Review** aprobado,
y el hashtag search solo funciona sobre contenido de cuentas ya conectadas
—no permite buscar libremente contenido público con un hashtag de Loja—.
Proceso largo (1-2 semanas) y con alta tasa de rechazo para apps pequeñas.
- Alternativa de pago sin aprobación: Apify Instagram Scraper (~$30/mes).

---

## Resumen de costos y dificultad

| Fuente         | Estado          | Costo si se activa   | Dificultad |
|----------------|-----------------|----------------------|------------|
| YouTube        | ✅ Activa        | $0                   | Ya hecho |
| Google Reviews | ✅ Activa (SerpApi) | Pago por búsqueda (SerpApi) | Ya hecho |
| Flickr         | ❌ Requiere Pro  | Flickr Pro (~$72/año)| Baja (solo falta la key) |
| Eventbrite     | ❌ Inviable      | —                    | No aplica (API pública cerrada) |
| TripAdvisor    | ❌ Incierta      | Apify ~$25/mes       | Alta (aprobación no garantizada) |
| Google Places  | ⚠️ Reviews resueltas por SerpApi; el resto necesita tarjeta | ~$17/1000 reseñas o Apify ~$20/mes | Media |
| TikTok         | ❌ Incierta      | Apify ~$30/mes       | Alta (aprobación no garantizada) |
| Instagram      | ❌ Incierta      | Apify ~$30/mes       | Alta (aprobación no garantizada) |

---

## Cómo agregar una fuente nueva (activa o descartada) en el futuro

1. Obtén la API Key o token del proveedor.
2. Agrégala a `backend/.env`: `NOMBRE_API_KEY=...`
3. Crea `backend/connectors/nombre.py` con una clase que herede de
   `ConectorBase` (ver `base.py`) e implemente `extraer_raw(tags: list[str])`.
   Usa `youtube.py` como referencia de patrón: caché con TTL, control de
   límites/cuota si aplica, manejo de errores sin crashear (try/except +
   `print()` de warning + devolver lista vacía).
4. Agrega un `transform_nombre()` en `backend/etl/pipeline.py` que mapee los
   campos crudos al esquema `RecursoSchema`, y súmalo al diccionario
   `TRANSFORMERS`.
5. Agrega el nombre de la plataforma a `PLATAFORMAS_VALIDAS` en
   `backend/schemas.py` (y el formato a `FORMATOS_VALIDOS` si es nuevo).
6. Importa el conector y agrégalo a `CONECTORES` en
   `backend/connectors/registry.py`.
7. Reinicia uvicorn — el selector de fuentes del frontend (`etl.js`) se
   actualiza solo, porque lee `/api/etl/fuentes` dinámicamente.

**El resto del sistema (pipeline ETL, deduplicación, detección de lugares,
interfaz web) funciona igual sin ningún cambio adicional.**
