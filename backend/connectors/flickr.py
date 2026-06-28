"""
connectors/flickr.py — Conector Flickr (modo mock).

API REAL: Flickr API (100% gratuita)
  https://www.flickr.com/services/api/
  - Requiere API Key gratuita
  - Endpoint: flickr.photos.search con geo y tags
  - Agrega al .env: FLICKR_API_KEY=...
"""
from datetime import datetime, timezone
from .base import ConectorBase

PHOTOS_RAW = [
    {"photo_id":"fl_001","title":"FIAVL 2025 - Teatro de calle","description":"Compañía de teatro física de Colombia durante el Festival Internacional de Artes Vivas de Loja","owner":"lojafotos","tags":["fiavl","artesvivas","loja","teatro","festival"],"views":2341,"favorites":89,"date_taken":"2025-11-15","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Teatro Benjamín Carrión"},
    {"photo_id":"fl_002","title":"Romería El Cisne 2025","description":"Miles de peregrinos en el camino hacia el Santuario de la Virgen del Cisne","owner":"ecuador_faith","tags":["romeria","ElCisne","loja","fe","peregrinacion"],"views":5678,"favorites":234,"date_taken":"2025-08-14","geo":{"lat":-3.9833,"lon":-79.9167},"place":"El Cisne, Loja"},
    {"photo_id":"fl_003","title":"Podocarpus - Laguna de Cajanuma","description":"Amanecer sobre la laguna en el sector Cajanuma del Parque Nacional Podocarpus","owner":"nature_ec","tags":["Podocarpus","laguna","naturaleza","loja","parquenacional"],"views":8901,"favorites":456,"date_taken":"2025-03-20","geo":{"lat":-4.1167,"lon":-79.1833},"place":"Parque Nacional Podocarpus"},
    {"photo_id":"fl_004","title":"Vilcabamba atardecer","description":"El valle de la longevidad pintado de oro al atardecer","owner":"travel_sur","tags":["Vilcabamba","atardecer","loja","valle","longevidad"],"views":12345,"favorites":678,"date_taken":"2025-06-15","geo":{"lat":-4.2631,"lon":-79.2236},"place":"Valle de Vilcabamba"},
    {"photo_id":"fl_005","title":"Plaza San Sebastián FIAVL","description":"Actuación de circo contemporáneo en la Plaza San Sebastián durante el FIAVL","owner":"culturaloja","tags":["FIAVL","plaza","circo","loja","artesvivas"],"views":3456,"favorites":123,"date_taken":"2025-11-16","geo":{"lat":-3.9928,"lon":-79.2003},"place":"Plaza San Sebastián"},
    {"photo_id":"fl_006","title":"Catedral de Loja - Amanecer","description":"La majestuosa Catedral de la Inmaculada Concepción al amanecer desde el parque central","owner":"arquiloja","tags":["catedral","loja","arquitectura","amanecer","colonial"],"views":4567,"favorites":189,"date_taken":"2025-01-10","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Catedral de la Inmaculada Concepción"},
    {"photo_id":"fl_007","title":"Orquídeas de Podocarpus","description":"Orquídea endémica fotografiada en el sector Bombuscaro del Parque Podocarpus","owner":"botanica_ec","tags":["orquideas","Podocarpus","flora","loja","biodiversidad"],"views":6789,"favorites":345,"date_taken":"2025-04-05","geo":{"lat":-4.0500,"lon":-78.9667},"place":"Parque Nacional Podocarpus"},
    {"photo_id":"fl_008","title":"FIAVL - Danza contemporánea","description":"Grupo de danza contemporánea del Brasil en el escenario principal del FIAVL 2025","owner":"danzaloja","tags":["FIAVL","danza","contemporanea","loja","festival"],"views":2890,"favorites":134,"date_taken":"2025-11-17","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Teatro Benjamín Carrión"},
    {"photo_id":"fl_009","title":"Virgen del Cisne - Procesión","description":"La imagen de la Virgen del Cisne en la procesión anual por las calles de Loja","owner":"fecatolica","tags":["virgendecisne","procesion","ElCisne","loja","fe"],"views":9012,"favorites":567,"date_taken":"2025-08-15","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Centro Histórico Loja"},
    {"photo_id":"fl_010","title":"Puerta de la Ciudad de Loja","description":"La monumental Puerta de la Ciudad, símbolo de Loja y primer monumento al visitante","owner":"loja_icons","tags":["puertaciudad","loja","monumento","arquitectura"],"views":7890,"favorites":345,"date_taken":"2025-02-14","geo":{"lat":-3.9811,"lon":-79.2067},"place":"Puerta de la Ciudad"},
    {"photo_id":"fl_011","title":"Aves en Podocarpus","description":"Tucán andino capturado en la ruta de avistamiento del Parque Nacional Podocarpus","owner":"birdwatcher_ec","tags":["aves","tucan","Podocarpus","birdwatching","loja"],"views":5432,"favorites":267,"date_taken":"2025-05-12","geo":{"lat":-4.1167,"lon":-79.1833},"place":"Parque Nacional Podocarpus"},
    {"photo_id":"fl_012","title":"Artistas callejeros FIAVL","description":"Mimos y artistas callejeros interactuando con el público en el FIAVL 2025","owner":"streetart_loja","tags":["FIAVL","artistas","callejeros","mimos","loja"],"views":3210,"favorites":145,"date_taken":"2025-11-15","geo":{"lat":-3.9928,"lon":-79.2003},"place":"Plaza San Sebastián"},
    {"photo_id":"fl_013","title":"Mercado de Loja","description":"Vendedoras de frutas tropicales en el colorido mercado central de Loja","owner":"gastronomia_ec","tags":["mercado","frutas","gastronomia","loja","colorido"],"views":4321,"favorites":189,"date_taken":"2025-07-08","geo":{"lat":-3.9950,"lon":-79.2038},"place":"Mercado Central Loja"},
    {"photo_id":"fl_014","title":"Vilcabamba - Sendero ecológico","description":"Senderista en los senderos ecológicos de Vilcabamba con vista del valle","owner":"hiking_loja","tags":["Vilcabamba","senderismo","sendero","loja","naturaleza"],"views":6543,"favorites":312,"date_taken":"2025-08-22","geo":{"lat":-4.2631,"lon":-79.2236},"place":"Valle de Vilcabamba"},
    {"photo_id":"fl_015","title":"Centro histórico nocturno","description":"Las calles coloniales del centro histórico de Loja iluminadas durante el FIAVL","owner":"nightloja","tags":["centrohistorico","nocturno","FIAVL","loja","colonial"],"views":5678,"favorites":234,"date_taken":"2025-11-18","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Centro Histórico Loja"},
    {"photo_id":"fl_016","title":"Colibrí cola de raqueta","description":"El extraordinario colibrí cola de raqueta, especie endémica del sur del Ecuador","owner":"wildlife_ec","tags":["colibri","aves","Podocarpus","endemica","loja"],"views":15678,"favorites":890,"date_taken":"2025-04-18","geo":{"lat":-4.1167,"lon":-79.1833},"place":"Parque Nacional Podocarpus"},
    {"photo_id":"fl_017","title":"FIAVL - Fuego y acrobacia","description":"Grupo de acróbatas con fuego de Argentina en el festival de artes vivas de Loja","owner":"acrobatismo","tags":["FIAVL","acrobacia","fuego","argentina","loja"],"views":7890,"favorites":456,"date_taken":"2025-11-19","geo":{"lat":-3.9928,"lon":-79.2003},"place":"Plaza San Sebastián"},
    {"photo_id":"fl_018","title":"Peregrinos en El Cisne","description":"Grupo de peregrinos descansando en el camino hacia el Santuario de El Cisne","owner":"peregrinaje","tags":["ElCisne","peregrinos","romeria","fe","loja"],"views":8901,"favorites":512,"date_taken":"2025-08-13","geo":{"lat":-3.9833,"lon":-79.9167},"place":"El Cisne, Loja"},
    {"photo_id":"fl_019","title":"Museo de la Música de Loja","description":"Instrumentos musicales históricos en el Museo de la Música de Loja","owner":"musicaloja","tags":["musica","museo","loja","instrumentos","capitalmusical"],"views":3456,"favorites":178,"date_taken":"2025-06-20","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Museo de la Música de Loja"},
    {"photo_id":"fl_020","title":"Río Zamora en Podocarpus","description":"El cristalino Río Zamora en el sector Bombuscaro del Parque Nacional Podocarpus","owner":"rios_ec","tags":["rio","zamora","Podocarpus","cristalino","loja"],"views":4567,"favorites":223,"date_taken":"2025-03-25","geo":{"lat":-4.0500,"lon":-78.9667},"place":"Parque Nacional Podocarpus"},
    {"photo_id":"fl_021","title":"Fiestas de Independencia Loja","description":"Desfile cívico por las calles de Loja en conmemoración del 18 de noviembre","owner":"historia_ec","tags":["independencia","loja","desfile","18noviembre","civico"],"views":2345,"favorites":123,"date_taken":"2024-11-18","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Av. Salvador Bustamante Celi"},
    {"photo_id":"fl_022","title":"Bromeliáceas en Podocarpus","description":"Increíble concentración de bromeliáceas y epífitas en el bosque nublado de Podocarpus","owner":"flora_andina","tags":["bromeliaceas","flora","Podocarpus","bosquenublado","loja"],"views":3456,"favorites":167,"date_taken":"2025-04-30","geo":{"lat":-4.1167,"lon":-79.1833},"place":"Parque Nacional Podocarpus"},
    {"photo_id":"fl_023","title":"FIAVL circo social","description":"Compañía de circo social para niños de Venezuela durante el FIAVL 2025","owner":"circosocial","tags":["FIAVL","circo","social","ninos","loja"],"views":5432,"favorites":289,"date_taken":"2025-11-16","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Teatro Benjamín Carrión"},
    {"photo_id":"fl_024","title":"Vilcabamba casas coloniales","description":"Arquitectura colonial bien conservada en el pueblo de Vilcabamba","owner":"colonial_ec","tags":["Vilcabamba","colonial","arquitectura","casas","loja"],"views":2890,"favorites":134,"date_taken":"2025-09-10","geo":{"lat":-4.2631,"lon":-79.2236},"place":"Valle de Vilcabamba"},
    {"photo_id":"fl_025","title":"Parque Central de Loja","description":"Vista aérea del Parque Central de Loja con la catedral al fondo","owner":"drone_loja","tags":["parquecentral","loja","aerea","catedral","drone"],"views":9012,"favorites":456,"date_taken":"2025-05-15","geo":{"lat":-3.9943,"lon":-79.2038},"place":"Parque Central de Loja"},
    {"photo_id":"fl_026","title":"El Cisne - Santuario exterior","description":"Fachada principal del Santuario de la Virgen del Cisne al atardecer","owner":"arquitectura_sagrada","tags":["ElCisne","santuario","virgen","loja","arquitectura"],"views":7654,"favorites":398,"date_taken":"2025-08-15","geo":{"lat":-3.9833,"lon":-79.9167},"place":"Santuario de El Cisne"},
    {"photo_id":"fl_027","title":"FIAVL puppets show","description":"Espectáculo de títeres gigantes de la compañía francesa durante el FIAVL 2025","owner":"puppets_world","tags":["FIAVL","titeres","gigantes","Francia","loja","artesvivas"],"views":6543,"favorites":334,"date_taken":"2025-11-17","geo":{"lat":-3.9928,"lon":-79.2003},"place":"Plaza San Sebastián"},
    {"photo_id":"fl_028","title":"Café de Loja","description":"Granos de café arábiga de las fincas cafetaleras de la provincia de Loja","owner":"cafeloja","tags":["cafe","arabiga","loja","agricultura","cafetera"],"views":3210,"favorites":156,"date_taken":"2025-08-10","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Loja, Ecuador"},
    {"photo_id":"fl_029","title":"Senderismo nocturno Podocarpus","description":"Senderismo nocturno con guía en Podocarpus para avistamiento de fauna nocturna","owner":"nocturno_ec","tags":["Podocarpus","nocturno","senderismo","fauna","loja"],"views":4321,"favorites":212,"date_taken":"2025-06-05","geo":{"lat":-4.1167,"lon":-79.1833},"place":"Parque Nacional Podocarpus"},
    {"photo_id":"fl_030","title":"Danzas folclóricas FIAVL","description":"Grupos de danza folclórica ecuatoriana en el escenario del FIAVL 2025","owner":"folklore_ec","tags":["FIAVL","folklore","danza","ecuatoriana","loja"],"views":5678,"favorites":267,"date_taken":"2025-11-18","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Teatro Benjamín Carrión"},
    {"photo_id":"fl_031","title":"Niebla en Podocarpus","description":"El mágico bosque nublado de Podocarpus cubierto de niebla matutina","owner":"misty_ec","tags":["Podocarpus","niebla","bosquenublado","magia","loja"],"views":8901,"favorites":445,"date_taken":"2025-02-28","geo":{"lat":-4.1167,"lon":-79.1833},"place":"Parque Nacional Podocarpus"},
    {"photo_id":"fl_032","title":"Panorámica de Loja","description":"Vista panorámica de la ciudad de Loja desde los miradores de los cerros circundantes","owner":"panorama_loja","tags":["panoramica","loja","ciudad","mirador","vista"],"views":12345,"favorites":678,"date_taken":"2025-07-25","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Loja, Ecuador"},
    {"photo_id":"fl_033","title":"FIAVL - Arte urbano","description":"Mural de arte urbano creado durante el festival FIAVL 2025 en el centro de Loja","owner":"graffiti_loja","tags":["FIAVL","arte","urbano","mural","loja"],"views":4567,"favorites":234,"date_taken":"2025-11-14","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Centro Histórico Loja"},
    {"photo_id":"fl_034","title":"Tamales lojanos","description":"Los tradicionales tamales lojanos, envueltos en hoja de achira y rellenos de pollo","owner":"food_loja","tags":["tamales","gastronomia","loja","tradicional","comida"],"views":6789,"favorites":345,"date_taken":"2025-09-20","geo":{"lat":-3.9950,"lon":-79.2038},"place":"Mercado Central Loja"},
    {"photo_id":"fl_035","title":"Río en Vilcabamba","description":"El río Chamba serpenteando por el verde valle de Vilcabamba","owner":"rios_sur","tags":["rio","Vilcabamba","verde","valle","loja"],"views":5432,"favorites":278,"date_taken":"2025-08-30","geo":{"lat":-4.2631,"lon":-79.2236},"place":"Valle de Vilcabamba"},
    {"photo_id":"fl_036","title":"FIAVL 2025 clausura","description":"Espectáculo de clausura del Festival Internacional de Artes Vivas de Loja 2025","owner":"clausura_fiavl","tags":["FIAVL","clausura","artesvivas","loja","festival"],"views":9876,"favorites":512,"date_taken":"2025-11-22","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Teatro Benjamín Carrión"},
    {"photo_id":"fl_037","title":"Peregrinos madrugada El Cisne","description":"Peregrinos caminando de madrugada con velas encendidas hacia El Cisne","owner":"madrugada_fe","tags":["ElCisne","peregrinos","madrugada","velas","loja"],"views":11234,"favorites":623,"date_taken":"2025-08-14","geo":{"lat":-3.9833,"lon":-79.9167},"place":"El Cisne, Loja"},
    {"photo_id":"fl_038","title":"Epífitas Podocarpus","description":"Gran variedad de epífitas incluyendo musgos y líquenes en árboles de Podocarpus","owner":"botanica_andina","tags":["epifitas","Podocarpus","botanica","loja","naturaleza"],"views":3456,"favorites":167,"date_taken":"2025-03-15","geo":{"lat":-4.1167,"lon":-79.1833},"place":"Parque Nacional Podocarpus"},
    {"photo_id":"fl_039","title":"Música en las calles FIAVL","description":"Músicos callejeros animando las noches del FIAVL en el centro histórico de Loja","owner":"musica_calle","tags":["FIAVL","musica","callejeros","noche","loja"],"views":4321,"favorites":212,"date_taken":"2025-11-19","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Centro Histórico Loja"},
    {"photo_id":"fl_040","title":"Lagartija endémica Loja","description":"Lagartija de la especie endémica del sur andino del Ecuador fotografiada en Podocarpus","owner":"herpetologia_ec","tags":["lagartija","endemica","Podocarpus","reptiles","loja"],"views":2345,"favorites":112,"date_taken":"2025-05-08","geo":{"lat":-4.1167,"lon":-79.1833},"place":"Parque Nacional Podocarpus"},
    {"photo_id":"fl_041","title":"Catedral Loja interior","description":"El interior de la Catedral de la Inmaculada Concepción con sus vitrales iluminados","owner":"vitrales_loja","tags":["catedral","interior","vitrales","loja","arquitectura"],"views":5678,"favorites":278,"date_taken":"2025-01-25","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Catedral de la Inmaculada Concepción"},
    {"photo_id":"fl_042","title":"FIAVL - Compañía teatral México","description":"Compañía de teatro físico de México en actuación callejera durante el FIAVL 2025","owner":"teatro_mundo","tags":["FIAVL","teatro","Mexico","callejero","loja"],"views":6789,"favorites":345,"date_taken":"2025-11-17","geo":{"lat":-3.9928,"lon":-79.2003},"place":"Plaza San Sebastián"},
    {"photo_id":"fl_043","title":"Vilcabamba flores silvestres","description":"Campo de flores silvestres en los alrededores de Vilcabamba en primavera","owner":"flores_sur","tags":["Vilcabamba","flores","silvestres","primavera","loja"],"views":7890,"favorites":389,"date_taken":"2025-09-25","geo":{"lat":-4.2631,"lon":-79.2236},"place":"Valle de Vilcabamba"},
    {"photo_id":"fl_044","title":"Repe lojano","description":"El tradicional repe blanco de Loja, sopa a base de guineo verde y queso","owner":"recetas_loja","tags":["repe","gastronomia","loja","tradicional","sopa"],"views":4321,"favorites":212,"date_taken":"2025-10-15","geo":{"lat":-3.9950,"lon":-79.2038},"place":"Mercado Central Loja"},
    {"photo_id":"fl_045","title":"Puente colonial Loja","description":"Puente colonial sobre el Río Malacatos en el centro histórico de Loja","owner":"patrimonio_loja","tags":["puente","colonial","Malacatos","loja","patrimonio"],"views":3456,"favorites":167,"date_taken":"2025-04-10","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Centro Histórico Loja"},
    {"photo_id":"fl_046","title":"FIAVL noche mágica","description":"Vista nocturna del centro histórico de Loja con artistas callejeros iluminados durante el FIAVL","owner":"noche_fiavl","tags":["FIAVL","noche","centrohistorico","artistas","loja"],"views":8901,"favorites":456,"date_taken":"2025-11-18","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Centro Histórico Loja"},
    {"photo_id":"fl_047","title":"El Cisne pueblo","description":"Vista del pintoresco pueblo de El Cisne con su santuario al fondo","owner":"pueblos_ec","tags":["ElCisne","pueblo","santuario","loja","paisaje"],"views":6543,"favorites":323,"date_taken":"2025-08-15","geo":{"lat":-3.9833,"lon":-79.9167},"place":"El Cisne, Loja"},
    {"photo_id":"fl_048","title":"Podocarpus amanecer","description":"El amanecer ilumina las cimas del Parque Nacional Podocarpus desde el sector Cajanuma","owner":"amanecer_ec","tags":["Podocarpus","amanecer","cimas","Cajanuma","loja"],"views":10234,"favorites":567,"date_taken":"2025-06-21","geo":{"lat":-4.1167,"lon":-79.1833},"place":"Parque Nacional Podocarpus"},
    {"photo_id":"fl_049","title":"FIAVL apertura","description":"Ceremonia de apertura del Festival Internacional de Artes Vivas de Loja 2025","owner":"apertura_fiavl","tags":["FIAVL","apertura","ceremonia","artesvivas","loja"],"views":12345,"favorites":678,"date_taken":"2025-11-14","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Teatro Benjamín Carrión"},
    {"photo_id":"fl_050","title":"Loja desde el aire","description":"Vista aérea con dron de la ciudad de Loja y el valle que la rodea","owner":"drone_ec","tags":["loja","aerea","drone","ciudad","valle"],"views":18901,"favorites":987,"date_taken":"2025-10-05","geo":{"lat":-3.9931,"lon":-79.2042},"place":"Loja, Ecuador"},
]

def _ahora():
    return datetime.now(timezone.utc).isoformat()

class ConectorFlickrMock(ConectorBase):
    """
    ══════════════════════════════════════════════════════════
    CONECTOR FLICKR — MODO MOCK
    ══════════════════════════════════════════════════════════
    API REAL: Flickr API (completamente gratuita)

    1. Crea cuenta y API Key en: https://www.flickr.com/services/api/
    2. Agrega al .env: FLICKR_API_KEY=...

    3. Flujo real:
       GET https://api.flickr.com/services/rest/?method=flickr.photos.search
           &api_key={key}&tags={tags}&bbox={loja_bbox}
           &extras=description,date_taken,geo,tags,views,count_faves
           &format=json&nojsoncallback=1

       Bbox de Loja: -79.35,-4.45,-79.05,-3.75

    4. Mapeo al esquema:
       origen.id_externo  = photo["id"]
       origen.formato     = "imagen"
       metadata.urls.cover = f"https://live.staticflickr.com/{farm}-{server}/{id}_{secret}.jpg"
    ══════════════════════════════════════════════════════════
    """
    nombre = "Flickr"

    def extraer_raw(self, tags: list[str]) -> list[dict]:
        if not tags:
            return PHOTOS_RAW
        q = [t.lower() for t in tags]
        return [
            p for p in PHOTOS_RAW
            if any(
                t in p["title"].lower() or
                t in p["description"].lower() or
                any(t in tag.lower() for tag in p["tags"]) or
                t in (p.get("place") or "").lower()
                for t in q
            )
        ]
