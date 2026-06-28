# Guía de Integración — APIs Reales
## Proyecto ETL Turismo Loja · UTPL 2026

---

## Cómo está estructurado el sistema

Cada fuente de datos tiene su propio archivo en `backend/connectors/`.
Para activar una API real, **solo se modifica ese archivo** — nada más en el sistema cambia.

```
backend/connectors/
  tiktok.py       ← modifica extraer_raw() para conectar TikTok Research API
  youtube.py      ← modifica extraer_raw() para conectar YouTube Data API v3
  instagram.py    ← modifica extraer_raw() para conectar Instagram Graph API
  google.py       ← modifica extraer_raw() para conectar Google Places API
  tripadvisor.py  ← modifica extraer_raw() para conectar TripAdvisor Content API
  flickr.py       ← modifica extraer_raw() para conectar Flickr API
  eventbrite.py   ← modifica extraer_raw() para conectar Eventbrite API
```

**Regla:** el método `extraer_raw()` debe devolver siempre una `list[dict]`
con los datos en formato crudo de la API. El pipeline ETL se encarga del resto.

---

## Opciones por fuente

### 1. YouTube — RECOMENDADA COMO PRIMERA
**Opción A: YouTube Data API v3 (oficial, GRATUITA)**
- Cuota: 10,000 unidades/día (suficiente para uso académico)
- Activación: inmediata (minutos)
- URL: https://console.cloud.google.com/ → APIs & Services → YouTube Data API v3

```
# Agregar al backend/.env
YOUTUBE_API_KEY=AIza...tuKeyAqui
```

**Implementación en `connectors/youtube.py`:**
Ver el bloque de comentarios `══════` dentro del archivo — contiene el código
completo listo para pegar.

---

### 2. Flickr — SEGUNDA MÁS FÁCIL
**Opción A: Flickr API (oficial, COMPLETAMENTE GRATUITA)**
- Sin límites estrictos para uso académico
- Activación: inmediata (minutos)
- URL: https://www.flickr.com/services/api/

```
# Agregar al backend/.env
FLICKR_API_KEY=tuKeyAqui
```

**Endpoint principal:**
```
GET https://api.flickr.com/services/rest/
    ?method=flickr.photos.search
    &api_key={key}
    &tags={tags}
    &bbox=-79.35,-4.45,-79.05,-3.75    ← Bounding box de Loja
    &extras=description,date_taken,geo,tags,views,count_faves
    &format=json&nojsoncallback=1
```

---

### 3. Eventbrite — FÁCIL, GRATUITA
**Opción A: Eventbrite API (oficial, gratuita)**
- Activación: minutos en developers.eventbrite.com
- URL: https://www.eventbrite.com/platform/api

```
# Agregar al backend/.env
EVENTBRITE_TOKEN=tuTokenAqui
```

**Endpoint principal:**
```
GET https://www.eventbriteapi.com/v3/events/search/
    ?q={tags}&location.address=Loja,Ecuador&location.within=50km
    Authorization: Bearer {token}
```

---

### 4. TikTok
**Opción A: TikTok Research API (oficial, GRATUITA para academia)**
- Requiere solicitud formal, aprobación en 2-4 semanas
- UTPL califica como institución educativa
- URL: https://developers.tiktok.com/

```
# Agregar al backend/.env
TIKTOK_CLIENT_KEY=tuKeyAqui
TIKTOK_CLIENT_SECRET=tuSecretAqui
```

**Opción B: Apify TikTok Scraper (~$30/mes)**
- Sin aprobación, funciona inmediatamente
- URL: https://apify.com/clockworks/free-tiktok-scraper
- Mismo resultado, diferente endpoint

---

### 5. Instagram
**Opción A: Instagram Graph API (oficial, gratuita)**
- Requiere Facebook App aprobada, 1-2 semanas de proceso
- URL: https://developers.facebook.com/

```
# Agregar al backend/.env
INSTAGRAM_ACCESS_TOKEN=EAABsb...
INSTAGRAM_BUSINESS_ID=123456...
```

**Opción B: Apify Instagram Scraper (~$30/mes)**
- URL: https://apify.com/apify/instagram-scraper

---

### 6. Google Reviews
**Opción A: Google Places API (oficial, de pago)**
- $17 por 1,000 reseñas, pero incluye $200 de crédito gratuito mensual
- Suficiente para uso moderado académico sin costo
- URL: https://console.cloud.google.com/ → Places API

```
# Agregar al backend/.env
GOOGLE_PLACES_KEY=AIza...tuKeyAqui
```

**Opción B: Apify Google Maps Reviews Scraper (~$20/mes)**
- URL: https://apify.com/compass/google-maps-reviews-scraper

---

### 7. TripAdvisor
**Opción A: TripAdvisor Content API (oficial, gratuita tier básico)**
- Aprobación en 3-5 días hábiles
- URL: https://tripadvisor-content-api.readme.io/

```
# Agregar al backend/.env
TRIPADVISOR_API_KEY=tuKeyAqui
```

**Opción B: Apify TripAdvisor Scraper (~$25/mes)**
- URL: https://apify.com/maxcopell/tripadvisor

---

## Resumen de costos y dificultad

| Fuente        | Opción gratuita        | Costo si paga      | Dificultad |
|---------------|------------------------|--------------------|------------|
| YouTube       | API oficial         | $0                 | Muy fácil |
| Flickr        | API oficial         | $0                 | Muy fácil |
| Eventbrite    | API oficial         | $0                 | Muy fácil |
| TikTok        | Académica (lenta)   | Apify ~$30/mes     |  Media |
| Instagram     | Proceso aprobación  | Apify ~$30/mes     |  Media |
| TripAdvisor   | Tier básico         | Apify ~$25/mes     |  Media |
| Google Reviews| $200 crédito/mes   | Apify ~$20/mes     |  Media |

**Recomendación de inicio:** YouTube + Flickr + Eventbrite son gratuitas y se
activan en menos de 30 minutos. Empezar por ellas para demostrar el sistema
funcionando con datos reales antes de gestionar aprobaciones.

---

## Proceso para activar cualquier API

1. Obtener la API Key o token del proveedor
2. Agregar al archivo `backend/.env`:
   ```
   NOMBRE_API_KEY=tuKeyAqui
   ```
3. Abrir el archivo del conector correspondiente en `backend/connectors/`
4. Leer el bloque `══════` dentro de la clase — contiene el código real listo
5. Reemplazar el método `extraer_raw()` con el código del bloque
6. Reiniciar uvicorn — no se toca ningún otro archivo

**El resto del sistema (pipeline ETL, deduplicación, detección de lugares,
interfaz web) funciona igual sin ningún cambio.**
