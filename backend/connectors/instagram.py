"""
connectors/instagram.py — Conector Instagram (modo mock).

API REAL: Instagram Graph API
  https://developers.facebook.com/docs/instagram-api/
  - Requiere Facebook Developer App aprobada
  - Endpoint: GET /ig_hashtag_search + /hashtag/{id}/recent_media
  - Agrega al .env: INSTAGRAM_ACCESS_TOKEN=...
"""
from datetime import datetime, timezone, timedelta
from .base import ConectorBase
import random

POSTS_RAW = [
    # FIAVL
    {"id":"ig_001","user":"lojaexplorer","caption":"Increíble noche en el #FIAVL2025 🎭 El teatro de calle nos dejó sin palabras. #loja #artesvivas #festivalloja","likes":312,"comments":18,"location":"Teatro Benjamín Carrión","timestamp":"2025-11-14T21:30:00Z","hashtags":["FIAVL2025","loja","artesvivas","festivalloja"]},
    {"id":"ig_002","user":"viajes_ecuador","caption":"El festival de artes vivas de Loja es simplemente mágico ✨ #fiavl #lojaecuador #turismocultural #artesvivas","likes":891,"comments":45,"location":"Centro Histórico Loja","timestamp":"2025-11-15T10:00:00Z","hashtags":["fiavl","lojaecuador","turismocultural","artesvivas"]},
    {"id":"ig_003","user":"culturaloja","caption":"Circo, teatro y danza en las calles de Loja 🎪 #FIAVL #artesvivas #loja #cultura #festival","likes":567,"comments":29,"location":"Parque Central de Loja","timestamp":"2025-11-15T19:00:00Z","hashtags":["FIAVL","artesvivas","loja","cultura","festival"]},
    {"id":"ig_004","user":"photographyec","caption":"Los colores del festival internacional de artes vivas #fiavl2025 #lojamagica #fotografiaecuador","likes":1203,"comments":67,"location":"Plaza San Sebastián","timestamp":"2025-11-16T11:30:00Z","hashtags":["fiavl2025","lojamagica","fotografiaecuador"]},
    {"id":"ig_005","user":"arte_loja","caption":"Mimos, acróbatas y artistas de todo el mundo reunidos en Loja 🌍 #fiavl #artesinternacional #loja","likes":445,"comments":23,"location":"Teatro Benjamín Carrión","timestamp":"2025-11-16T15:00:00Z","hashtags":["fiavl","artesinternacional","loja"]},
    {"id":"ig_006","user":"turismo_loja_ec","caption":"El Festival Internacional de Artes Vivas transforma las calles de Loja en un escenario único #fiavl #lojaturismo","likes":678,"comments":34,"location":"Centro Histórico Loja","timestamp":"2025-11-17T09:00:00Z","hashtags":["fiavl","lojaturismo"]},
    {"id":"ig_007","user":"loja_lifestyle","caption":"Noche mágica en el FIAVL, la energía de los artistas es contagiosa 🎶 #fiavl2025 #lojaecuador #noche","likes":234,"comments":12,"location":"Parque Central de Loja","timestamp":"2025-11-17T22:00:00Z","hashtags":["fiavl2025","lojaecuador","noche"]},
    {"id":"ig_008","user":"ecuadortravel","caption":"Razón #1 para visitar Loja en noviembre: el Festival de Artes Vivas 🎭 #fiavl #ecuador #travel #loja","likes":1567,"comments":89,"location":"Loja, Ecuador","timestamp":"2025-11-18T08:00:00Z","hashtags":["fiavl","ecuador","travel","loja"]},
    {"id":"ig_009","user":"artistas_ec","caption":"Compartiendo escenario con artistas de 15 países en el FIAVL 🌐 #fiavl #artesvivas #internacionalización","likes":389,"comments":21,"location":"Teatro Benjamín Carrión","timestamp":"2025-11-18T17:00:00Z","hashtags":["fiavl","artesvivas","internacionalización"]},
    {"id":"ig_010","user":"loja_photos","caption":"Las calles se convierten en museo vivo durante el festival ✨ #fiavl2025 #artecallejero #loja #cultura","likes":723,"comments":41,"location":"Plaza San Sebastián","timestamp":"2025-11-19T14:00:00Z","hashtags":["fiavl2025","artecallejero","loja","cultura"]},
    # Romería El Cisne
    {"id":"ig_011","user":"fe_ecuador","caption":"La Romería de El Cisne, una tradición que une a miles de peregrinos cada año 🕊️ #ElCisne #romeria #loja #fe","likes":2341,"comments":178,"location":"Santuario de El Cisne","timestamp":"2025-08-15T07:00:00Z","hashtags":["ElCisne","romeria","loja","fe"]},
    {"id":"ig_012","user":"tradiciones_ec","caption":"Miles de fieles recorren el camino hacia el santuario de la Virgen del Cisne 🙏 #romeria #ElCisne #lojaecuador","likes":1876,"comments":134,"location":"El Cisne, Loja","timestamp":"2025-08-14T06:00:00Z","hashtags":["romeria","ElCisne","lojaecuador"]},
    {"id":"ig_013","user":"photoecuador","caption":"La devoción en su máxima expresión: la romería de El Cisne #romeriaecuador #ElCisne #virgendecisne","likes":3012,"comments":201,"location":"Santuario de El Cisne","timestamp":"2025-08-15T12:00:00Z","hashtags":["romeriaecuador","ElCisne","virgendecisne"]},
    {"id":"ig_014","user":"loja_traditions","caption":"El camino hacia El Cisne es fe, comunidad y cultura #romeria #cisne #ecuadortradiciones #loja","likes":892,"comments":56,"location":"El Cisne, Loja","timestamp":"2025-08-13T16:00:00Z","hashtags":["romeria","cisne","ecuadortradiciones","loja"]},
    {"id":"ig_015","user":"viajero_ec","caption":"Participando en la romería más famosa del Ecuador 🇪🇨 #ElCisne #romeria #turismorreligioso #loja","likes":1234,"comments":78,"location":"Santuario de El Cisne","timestamp":"2025-08-15T09:00:00Z","hashtags":["ElCisne","romeria","turismoreligioso","loja"]},
    # Fiestas de Independencia
    {"id":"ig_016","user":"historia_loja","caption":"Celebrando 203 años de independencia de Loja 🎉🇪🇨 #independencialoja #loja #18noviembre #fiestas","likes":567,"comments":34,"location":"Parque Central de Loja","timestamp":"2024-11-18T10:00:00Z","hashtags":["independencialoja","loja","18noviembre","fiestas"]},
    {"id":"ig_017","user":"lojadigital","caption":"El desfile cívico del 18 de noviembre llena las calles de orgullo lojano 🎊 #loja #desfile #independencia","likes":789,"comments":45,"location":"Av. Salvador Bustamante Celi","timestamp":"2024-11-18T09:00:00Z","hashtags":["loja","desfile","independencia"]},
    {"id":"ig_018","user":"cultura_ec","caption":"Tradición, historia y orgullo en las fiestas de independencia de Loja #loja #fiestaspatrias #independencia","likes":432,"comments":28,"location":"Centro Histórico Loja","timestamp":"2024-11-17T14:00:00Z","hashtags":["loja","fiestaspatrias","independencia"]},
    # Festival de Cine
    {"id":"ig_019","user":"cine_loja","caption":"El Festival Internacional de Cine de Loja trae lo mejor del cine mundial a nuestra ciudad 🎬 #cineloja #festival","likes":345,"comments":19,"location":"Teatro Benjamín Carrión","timestamp":"2024-09-20T19:00:00Z","hashtags":["cineloja","festival"]},
    {"id":"ig_020","user":"film_ecuador","caption":"Cortometrajes, documentales y largometrajes en el festival de cine de Loja 🎥 #cineloja #cine #loja","likes":267,"comments":14,"location":"Loja, Ecuador","timestamp":"2024-09-21T18:00:00Z","hashtags":["cineloja","cine","loja"]},
    # Lugares turísticos
    {"id":"ig_021","user":"natureloja","caption":"El Parque Nacional Podocarpus, un tesoro de biodiversidad en el sur del Ecuador 🌿 #Podocarpus #naturaleza #loja","likes":2103,"comments":145,"location":"Parque Nacional Podocarpus","timestamp":"2025-03-10T08:00:00Z","hashtags":["Podocarpus","naturaleza","loja"]},
    {"id":"ig_022","user":"hiking_ec","caption":"Senderismo en Podocarpus, flora y fauna únicas en el mundo 🦋 #Podocarpus #senderismo #ecoturismo #loja","likes":1456,"comments":98,"location":"Parque Nacional Podocarpus","timestamp":"2025-04-05T07:30:00Z","hashtags":["Podocarpus","senderismo","ecoturismo","loja"]},
    {"id":"ig_023","user":"vilcabamba_life","caption":"Vilcabamba, el Valle de la Longevidad 🌄 aire puro y naturaleza inigualable #Vilcabamba #loja #vallelargogevidad","likes":3456,"comments":234,"location":"Valle de Vilcabamba","timestamp":"2025-05-20T07:00:00Z","hashtags":["Vilcabamba","loja","vallelongevidad"]},
    {"id":"ig_024","user":"travel_sur_ec","caption":"La Puerta de la Ciudad de Loja, bienvenida monumental al sur del Ecuador 🏛️ #loja #puertaciudad #arquitectura","likes":678,"comments":42,"location":"Puerta de la Ciudad","timestamp":"2025-02-14T11:00:00Z","hashtags":["loja","puertaciudad","arquitectura"]},
    {"id":"ig_025","user":"cathedral_tours","caption":"La Catedral de Loja, joya arquitectónica del centro histórico ⛪ #catedral #loja #arquitectura #colonial","likes":891,"comments":56,"location":"Catedral de la Inmaculada Concepción","timestamp":"2025-01-20T10:00:00Z","hashtags":["catedral","loja","arquitectura","colonial"]},
    {"id":"ig_026","user":"music_ecuador","caption":"Loja, capital musical del Ecuador 🎵 La ciudad que más músicos ha dado al país #loja #musica #capitalmusical","likes":1234,"comments":78,"location":"Museo de la Música de Loja","timestamp":"2025-06-15T14:00:00Z","hashtags":["loja","musica","capitalmusical"]},
    {"id":"ig_027","user":"plaza_tours","caption":"La Plaza San Sebastián, corazón del centro histórico de Loja 🏙️ #loja #plazasansebastian #centrohistorico","likes":567,"comments":33,"location":"Plaza San Sebastián","timestamp":"2025-03-25T16:00:00Z","hashtags":["loja","plazasansebastian","centrohistorico"]},
    {"id":"ig_028","user":"eco_loja","caption":"Las orquídeas de Loja, flora exótica que enamora a propios y extraños 🌸 #loja #orquideas #naturaleza #biodiversidad","likes":1678,"comments":112,"location":"Parque Nacional Podocarpus","timestamp":"2025-04-22T09:00:00Z","hashtags":["loja","orquideas","naturaleza","biodiversidad"]},
    {"id":"ig_029","user":"gastronomia_ec","caption":"Los tamales lojanos, sabor único que no puedes perderte 🫔 #loja #gastronomia #tamales #ecuadorfood","likes":2345,"comments":167,"location":"Mercado Central Loja","timestamp":"2025-07-10T12:00:00Z","hashtags":["loja","gastronomia","tamales","ecuadorfood"]},
    {"id":"ig_030","user":"coffee_loja","caption":"El café de Loja, entre los mejores de Ecuador ☕ visita las fincas cafetaleras del sur #loja #cafe #coffeeecuador","likes":1890,"comments":123,"location":"Loja, Ecuador","timestamp":"2025-08-05T08:00:00Z","hashtags":["loja","cafe","coffeeecuador"]},
    # Más FIAVL y eventos mixtos
    {"id":"ig_031","user":"danza_ec","caption":"Ballet y danza contemporánea en el escenario del FIAVL 💃 #fiavl #danza #ballet #loja #artesvivas","likes":456,"comments":27,"location":"Teatro Benjamín Carrión","timestamp":"2025-11-15T20:00:00Z","hashtags":["fiavl","danza","ballet","loja","artesvivas"]},
    {"id":"ig_032","user":"teatro_loja","caption":"El teatro de calle del FIAVL convierte a Loja en la capital cultural de Sudamérica #fiavl #teatrocalle #loja","likes":789,"comments":48,"location":"Centro Histórico Loja","timestamp":"2025-11-16T21:00:00Z","hashtags":["fiavl","teatrocalle","loja"]},
    {"id":"ig_033","user":"festivales_ec","caption":"Ya comenzó el FIAVL 2025 y la ciudad vibra con arte de todos los continentes 🌍 #fiavl2025 #artesvivas","likes":1123,"comments":67,"location":"Loja, Ecuador","timestamp":"2025-11-14T18:00:00Z","hashtags":["fiavl2025","artesvivas"]},
    {"id":"ig_034","user":"lojanews","caption":"El FIAVL 2025 bate récord de asistencia con más de 50.000 visitantes #fiavl2025 #record #loja #turismo","likes":2234,"comments":156,"location":"Loja, Ecuador","timestamp":"2025-11-20T10:00:00Z","hashtags":["fiavl2025","record","loja","turismo"]},
    {"id":"ig_035","user":"artistas_mundo","caption":"Representando a Argentina en el Festival Internacional de Artes Vivas de Loja 🇦🇷 #fiavl #artesvivas #loja","likes":678,"comments":39,"location":"Teatro Benjamín Carrión","timestamp":"2025-11-15T16:00:00Z","hashtags":["fiavl","artesvivas","loja"]},
    {"id":"ig_036","user":"cisnefiel","caption":"Caminando 70km para llegar al santuario de El Cisne, la fe mueve montañas 🙏 #romeria #ElCisne #fe #loja","likes":3456,"comments":234,"location":"El Cisne, Loja","timestamp":"2025-08-12T05:00:00Z","hashtags":["romeria","ElCisne","fe","loja"]},
    {"id":"ig_037","user":"paisajes_ec","caption":"El amanecer en el Valle de Vilcabamba es pura magia 🌅 #Vilcabamba #amanecer #loja #naturaleza","likes":4123,"comments":289,"location":"Valle de Vilcabamba","timestamp":"2025-06-01T06:00:00Z","hashtags":["Vilcabamba","amanecer","loja","naturaleza"]},
    {"id":"ig_038","user":"turismo_sur","caption":"5 razones para visitar Loja: 1) FIAVL 2) Vilcabamba 3) Podocarpus 4) Gastronomía 5) Su gente 💛 #loja #turismo","likes":5678,"comments":345,"location":"Loja, Ecuador","timestamp":"2025-09-15T10:00:00Z","hashtags":["loja","turismo"]},
    {"id":"ig_039","user":"arquitectura_ec","caption":"La arquitectura colonial del centro histórico de Loja, patrimonio que hay que preservar 🏛️ #loja #patrimonio","likes":789,"comments":45,"location":"Centro Histórico Loja","timestamp":"2025-02-28T11:00:00Z","hashtags":["loja","patrimonio"]},
    {"id":"ig_040","user":"birdwatching_ec","caption":"Avistamiento de aves endémicas en Podocarpus, paraíso para los amantes de la naturaleza 🦅 #Podocarpus #aves","likes":1234,"comments":78,"location":"Parque Nacional Podocarpus","timestamp":"2025-05-10T07:00:00Z","hashtags":["Podocarpus","aves"]},
    {"id":"ig_041","user":"loja_noches","caption":"Las noches del FIAVL en el Parque Central, arte y comunidad reunidos ⭐ #fiavl #parquecentral #loja","likes":567,"comments":34,"location":"Parque Central de Loja","timestamp":"2025-11-17T23:00:00Z","hashtags":["fiavl","parquecentral","loja"]},
    {"id":"ig_042","user":"ecuador_trips","caption":"Road trip por el sur del Ecuador: Loja, Vilcabamba y Podocarpus 🚗 #roadtrip #loja #ecuador #travel","likes":2345,"comments":167,"location":"Loja, Ecuador","timestamp":"2025-07-20T08:00:00Z","hashtags":["roadtrip","loja","ecuador","travel"]},
    {"id":"ig_043","user":"mochileros_ec","caption":"Hospedaje económico en Loja para el FIAVL, la ciudad se prepara para recibir al mundo 🌍 #fiavl #loja #mochileros","likes":345,"comments":23,"location":"Loja, Ecuador","timestamp":"2025-11-10T14:00:00Z","hashtags":["fiavl","loja","mochileros"]},
    {"id":"ig_044","user":"independencia_loja","caption":"El 18 de noviembre Loja celebra su gesta libertadora 🇪🇨 #independencialoja #18noviembre #loja #historia","likes":892,"comments":56,"location":"Parque Central de Loja","timestamp":"2024-11-18T11:00:00Z","hashtags":["independencialoja","18noviembre","loja","historia"]},
    {"id":"ig_045","user":"food_tour_ec","caption":"Tour gastronómico por Loja: repe, cecina, tamales y humitas 🍲 #gastronomialoja #loja #foodtour #ecuadorfood","likes":3456,"comments":234,"location":"Mercado Central Loja","timestamp":"2025-09-05T13:00:00Z","hashtags":["gastronomialoja","loja","foodtour","ecuadorfood"]},
    {"id":"ig_046","user":"cultura_lojana","caption":"El teatro benjamín carrión, epicentro cultural de Loja y sede del FIAVL 🎭 #teatrobenjamincarrion #fiavl #loja","likes":678,"comments":41,"location":"Teatro Benjamín Carrión","timestamp":"2025-11-13T10:00:00Z","hashtags":["teatrobenjamincarrion","fiavl","loja"]},
    {"id":"ig_047","user":"cisne_devoto","caption":"La Virgen del Cisne, patrona de Loja y símbolo de fe del Ecuador 🕊️ #virgendecisne #ElCisne #loja #fe","likes":4567,"comments":312,"location":"Santuario de El Cisne","timestamp":"2025-08-15T08:00:00Z","hashtags":["virgendecisne","ElCisne","loja","fe"]},
    {"id":"ig_048","user":"loja_verde","caption":"Senderos ecológicos en Loja, ciudad y naturaleza en perfecta armonía 🌳 #loja #ecoturismo #naturaleza #verde","likes":1234,"comments":78,"location":"Parque Nacional Podocarpus","timestamp":"2025-04-18T08:00:00Z","hashtags":["loja","ecoturismo","naturaleza","verde"]},
    {"id":"ig_049","user":"festival_lovers","caption":"El FIAVL es el festival más importante del Ecuador y uno de los más relevantes de Latinoamérica 🌎 #fiavl #loja","likes":2345,"comments":156,"location":"Loja, Ecuador","timestamp":"2025-11-19T16:00:00Z","hashtags":["fiavl","loja"]},
    {"id":"ig_050","user":"south_ec","caption":"Loja, la capital del sur del Ecuador que te sorprenderá con su cultura, naturaleza y gente 💛 #loja #surdelecuador","likes":3456,"comments":234,"location":"Loja, Ecuador","timestamp":"2025-10-01T10:00:00Z","hashtags":["loja","surdelecuador"]},
]

def _ahora():
    return datetime.now(timezone.utc).isoformat()

class ConectorInstagramMock(ConectorBase):
    """
    ══════════════════════════════════════════════════════════
    CONECTOR INSTAGRAM — MODO MOCK
    ══════════════════════════════════════════════════════════
    API REAL: Instagram Graph API (requiere Facebook App aprobada)

    1. Crea app en: https://developers.facebook.com/
    2. Solicita permisos: instagram_basic, instagram_manage_insights
    3. Agrega al .env:
         INSTAGRAM_ACCESS_TOKEN=EAABsb...
         INSTAGRAM_BUSINESS_ID=123456...

    4. Flujo real:
       # Buscar hashtag
       GET /ig_hashtag_search?q={tag}&user_id={business_id}
       # Obtener posts del hashtag
       GET /{hashtag_id}/recent_media?fields=id,caption,like_count,
           comments_count,timestamp,location&access_token={token}

    5. Mapeo al esquema:
       origen.id_externo  = item["id"]
       metadata.texto_original = item["caption"]
       metadata.metricas.likes = item["like_count"]
    ══════════════════════════════════════════════════════════
    """
    nombre = "Instagram"

    def extraer_raw(self, tags: list[str]) -> list[dict]:
        """Devuelve datos crudos tal como los devolvería la API real."""
        if not tags:
            return POSTS_RAW
        q = [t.lower() for t in tags]
        return [
            p for p in POSTS_RAW
            if any(
                t in p["caption"].lower() or
                any(t in h.lower() for h in p["hashtags"]) or
                t in (p.get("location") or "").lower()
                for t in q
            )
        ]
