"""
connectors/tripadvisor.py — Conector TripAdvisor (modo mock).

API REAL: TripAdvisor Content API
  https://tripadvisor-content-api.readme.io/
  - Requiere API Key (plan gratuito disponible)
  - Endpoint: GET /location/{id}/reviews
  - Agrega al .env: TRIPADVISOR_API_KEY=...
"""
from datetime import datetime, timezone
from .base import ConectorBase

REVIEWS_RAW = [
    # Teatro Benjamín Carrión
    {"review_id":"ta_001","title":"El mejor teatro del sur del Ecuador","text":"El Teatro Benjamín Carrión es una joya arquitectónica y cultural. Durante el FIAVL pudimos ver actuaciones increíbles de compañías internacionales. El personal fue muy amable.","rating":5,"author":"Maria_G_Quito","date":"2025-11-20","location_name":"Teatro Benjamín Carrión","location_type":"Teatro","helpful_votes":34},
    {"review_id":"ta_002","title":"Espectáculo impresionante","text":"Fui al teatro durante el Festival de Artes Vivas y quedé maravillada. La acústica es perfecta y la programación del FIAVL fue de nivel internacional. Totalmente recomendado.","rating":5,"author":"Carlos_M_Madrid","date":"2025-11-18","location_name":"Teatro Benjamín Carrión","location_type":"Teatro","helpful_votes":28},
    {"review_id":"ta_003","title":"Buen teatro pero poca señalización","text":"El teatro en sí es hermoso y tiene buena capacidad. Vine al FIAVL y el espectáculo fue magnífico. Solo mejoraría la señalización exterior para encontrarlo más fácil.","rating":4,"author":"Ana_T_Guayaquil","date":"2025-11-17","location_name":"Teatro Benjamín Carrión","location_type":"Teatro","helpful_votes":15},
    # Santuario El Cisne
    {"review_id":"ta_004","title":"Experiencia espiritual única","text":"La peregrinación a El Cisne es una experiencia que transforma. Miles de devotos caminan juntos en fe. El santuario es hermoso y la Virgen del Cisne irradia una paz especial.","rating":5,"author":"Rosa_P_Lima","date":"2025-08-16","location_name":"Santuario de El Cisne","location_type":"Iglesia","helpful_votes":89},
    {"review_id":"ta_005","title":"La romería más emotiva que he vivido","text":"Vine desde Perú especialmente para la romería y no me arrepiento. El camino es largo pero la recompensa espiritual es enorme. El santuario y el pueblo de El Cisne son bellísimos.","rating":5,"author":"Jorge_L_Lima","date":"2025-08-15","location_name":"Santuario de El Cisne","location_type":"Iglesia","helpful_votes":67},
    {"review_id":"ta_006","title":"Fe y tradición","text":"La Virgen del Cisne es la patrona de Loja y su fiesta en agosto es imperdible. El recorrido procesional es imponente. Recomiendo ir con tiempo y buena condición física.","rating":4,"author":"Patricia_V_Cuenca","date":"2025-08-14","location_name":"Santuario de El Cisne","location_type":"Iglesia","helpful_votes":45},
    {"review_id":"ta_007","title":"Devoción que emociona","text":"La romería de El Cisne es uno de los eventos religiosos más importantes de Ecuador. Vine con mi familia y fue una experiencia que fortalece la fe y la unión familiar.","rating":5,"author":"Luis_H_Machala","date":"2025-08-15","location_name":"Santuario de El Cisne","location_type":"Iglesia","helpful_votes":56},
    # Parque Nacional Podocarpus
    {"review_id":"ta_008","title":"Paraíso de biodiversidad","text":"Podocarpus es simplemente extraordinario. En un día vimos más de 40 especies de aves, incluyendo el colibrí cola de raqueta. La flora es única y los guías son excelentes.","rating":5,"author":"David_N_Berlin","date":"2025-05-22","location_name":"Parque Nacional Podocarpus","location_type":"Área Natural","helpful_votes":112},
    {"review_id":"ta_009","title":"Trekking impresionante","text":"Las rutas de senderismo en Podocarpus son bien mantenidas y señalizadas. El lago en la ruta Cajanuma es espectacular. Ideal para ecoturistas y amantes de la naturaleza.","rating":5,"author":"Sophie_K_Paris","date":"2025-04-10","location_name":"Parque Nacional Podocarpus","location_type":"Área Natural","helpful_votes":98},
    {"review_id":"ta_010","title":"El bosque nublado más hermoso","text":"Visite Podocarpus en la ruta de Bombuscaro y fue mágico. Los ríos cristalinos y la selva tropical son increíbles. Lleva ropa impermeable porque puede llover.","rating":4,"author":"Marco_R_Italia","date":"2025-03-15","location_name":"Parque Nacional Podocarpus","location_type":"Área Natural","helpful_votes":76},
    {"review_id":"ta_011","title":"Must visit en el sur del Ecuador","text":"Si visitas Loja no puedes perderte Podocarpus. Hay dos entradas: Cajanuma (páramo) y Bombuscaro (selva). Ambas son espectaculares y muy diferentes entre sí.","rating":5,"author":"Emma_W_Londres","date":"2025-06-08","location_name":"Parque Nacional Podocarpus","location_type":"Área Natural","helpful_votes":134},
    # Vilcabamba
    {"review_id":"ta_012","title":"El valle de la longevidad es real","text":"Vilcabamba es un lugar mágico. El clima es perfecto todo el año, la gente es amable y el paisaje es de postal. Entiendo por qué tanta gente viene a vivir aquí.","rating":5,"author":"Michael_B_USA","date":"2025-07-14","location_name":"Valle de Vilcabamba","location_type":"Área Natural","helpful_votes":189},
    {"review_id":"ta_013","title":"Paz y tranquilidad garantizadas","text":"Estuve 5 días en Vilcabamba y fue exactamente lo que necesitaba. Rutas de caballo, yoga, comida orgánica y naturaleza sin igual. Me quedo con las ganas de volver.","rating":5,"author":"Lisa_M_Canada","date":"2025-08-20","location_name":"Valle de Vilcabamba","location_type":"Área Natural","helpful_votes":156},
    {"review_id":"ta_014","title":"Algo turístico pero aún auténtico","text":"Vilcabamba se ha vuelto popular pero conserva su encanto. Los restaurantes y hostales son de buena calidad. Las caminatas por los alrededores son espectaculares.","rating":4,"author":"Peter_H_Alemania","date":"2025-09-05","location_name":"Valle de Vilcabamba","location_type":"Área Natural","helpful_votes":87},
    # Centro Histórico
    {"review_id":"ta_015","title":"Centro histórico bien conservado","text":"El centro histórico de Loja tiene una arquitectura colonial bien preservada. Las iglesias, plazas y museos hacen de un paseo por el centro una experiencia cultural enriquecedora.","rating":4,"author":"Isabella_R_Colombia","date":"2025-03-28","location_name":"Centro Histórico Loja","location_type":"Zona Histórica","helpful_votes":67},
    {"review_id":"ta_016","title":"Loja, ciudad cultural por excelencia","text":"Me sorprendió gratamente la cantidad de oferta cultural que tiene Loja. Museos, teatros, festivales y una gastronomía excelente. La ciudad merece más reconocimiento turístico.","rating":5,"author":"Andrés_C_Bogotá","date":"2025-04-15","location_name":"Centro Histórico Loja","location_type":"Zona Histórica","helpful_votes":92},
    # Plaza San Sebastián
    {"review_id":"ta_017","title":"El corazón de la ciudad","text":"La Plaza San Sebastián es el punto de encuentro de los lojanos. Siempre hay animación, artistas callejeros y eventos culturales. Ideal para sentir el pulso de la ciudad.","rating":4,"author":"Valentina_G_Quito","date":"2025-05-10","location_name":"Plaza San Sebastián","location_type":"Plaza Pública","helpful_votes":43},
    {"review_id":"ta_018","title":"Perfecta para descansar y observar","text":"Me senté en la plaza San Sebastián durante el FIAVL y fue espectacular ver las actuaciones callejeras. El ambiente es muy seguro y acogedor.","rating":5,"author":"Robert_T_USA","date":"2025-11-16","location_name":"Plaza San Sebastián","location_type":"Plaza Pública","helpful_votes":38},
    # Catedral
    {"review_id":"ta_019","title":"Arquitectura impresionante","text":"La Catedral de la Inmaculada Concepción de Loja es imponente. Su arquitectura neogótica y los vitrales son espectaculares. Vale la pena visitarla por dentro.","rating":5,"author":"Fernanda_L_Argentina","date":"2025-02-20","location_name":"Catedral de la Inmaculada Concepción","location_type":"Iglesia","helpful_votes":78},
    {"review_id":"ta_020","title":"Joya del patrimonio lojano","text":"La catedral domina el centro histórico de Loja. Fue reconstruida en el siglo XX y tiene elementos arquitectónicos muy llamativos. La vista desde afuera es magnífica.","rating":4,"author":"Sofía_M_Chile","date":"2025-03-12","location_name":"Catedral de la Inmaculada Concepción","location_type":"Iglesia","helpful_votes":54},
    # FIAVL reseñas
    {"review_id":"ta_021","title":"Festival de talla mundial","text":"El FIAVL 2025 superó todas mis expectativas. Artistas de 20 países, espectáculos gratuitos en la calle y una organización impecable. Loja se transforma en noviembre.","rating":5,"author":"Antoine_B_Francia","date":"2025-11-21","location_name":"Festival Internacional de Artes Vivas","location_type":"Festival","helpful_votes":234},
    {"review_id":"ta_022","title":"El mejor festival de Ecuador","text":"He ido a muchos festivales en Ecuador pero el FIAVL es sin duda el mejor. La calidad de los artistas internacionales es extraordinaria y la ciudad entera participa.","rating":5,"author":"Monica_S_Guayaquil","date":"2025-11-20","location_name":"Festival Internacional de Artes Vivas","location_type":"Festival","helpful_votes":189},
    {"review_id":"ta_023","title":"Arte vivo en las calles","text":"El concepto del FIAVL de llevar el arte a las calles es brillante. Cualquier esquina puede convertirse en un escenario. Una experiencia artística única en Ecuador.","rating":5,"author":"Juan_P_Madrid","date":"2025-11-19","location_name":"Festival Internacional de Artes Vivas","location_type":"Festival","helpful_votes":145},
    {"review_id":"ta_024","title":"Muy bueno pero algo desorganizado","text":"El FIAVL es espectacular en cuanto a calidad artística pero la logística podría mejorar. A veces hay mucha gente en poco espacio. Aun así, vale totalmente la pena.","rating":4,"author":"Catalina_R_Medellín","date":"2025-11-18","location_name":"Festival Internacional de Artes Vivas","location_type":"Festival","helpful_votes":98},
    {"review_id":"ta_025","title":"Loja vibra con el FIAVL","text":"La energía durante el FIAVL es inigualable. La ciudad entera celebra y los lojanos son los mejores anfitriones. Volveré el próximo año sin duda.","rating":5,"author":"Ricardo_T_Lima","date":"2025-11-17","location_name":"Festival Internacional de Artes Vivas","location_type":"Festival","helpful_votes":167},
    # Más lugares
    {"review_id":"ta_026","title":"Puerta de la Ciudad imponente","text":"La Puerta de la Ciudad de Loja es una estructura monumental que da la bienvenida. Tiene museo dentro con historia de la ciudad. Muy recomendable como primera parada.","rating":4,"author":"Helena_W_Polonia","date":"2025-03-05","location_name":"Puerta de la Ciudad","location_type":"Monumento","helpful_votes":45},
    {"review_id":"ta_027","title":"Museo de música único","text":"El Museo de la Música de Loja es fascinante. Explica por qué Loja es la capital musical del Ecuador. Instrumentos históricos y exhibiciones interactivas muy bien curadas.","rating":5,"author":"Alessandro_V_Italia","date":"2025-04-20","location_name":"Museo de la Música de Loja","location_type":"Museo","helpful_votes":67},
    {"review_id":"ta_028","title":"Gastronomía sorprendente","text":"Probé el repe lojano, los tamales y la cecina por primera vez y quedé enamorado. La gastronomía de Loja es una razón más para visitar esta ciudad maravillosa.","rating":5,"author":"Catherine_D_USA","date":"2025-06-15","location_name":"Mercado Central Loja","location_type":"Mercado","helpful_votes":89},
    {"review_id":"ta_029","title":"Mercado lleno de sabores","text":"El mercado central de Loja es un festín de colores, aromas y sabores. Los jugos de frutas tropicales son increíbles y los precios muy accesibles.","rating":4,"author":"Marcos_F_Brasil","date":"2025-07-08","location_name":"Mercado Central Loja","location_type":"Mercado","helpful_votes":56},
    {"review_id":"ta_030","title":"Ciudad perfecta para el turismo cultural","text":"Loja tiene de todo: naturaleza, cultura, gastronomía e historia. El FIAVL, la romería de El Cisne y Vilcabamba son razones más que suficientes para visitarla.","rating":5,"author":"Natalie_K_Canada","date":"2025-10-15","location_name":"Loja, Ecuador","location_type":"Ciudad","helpful_votes":234},
    # Más reseñas variadas
    {"review_id":"ta_031","title":"Ideal para turismo de naturaleza","text":"Podocarpus y Vilcabamba hacen de Loja un destino ideal para el ecoturismo. La combinación de biodiversidad y cultura es difícil de encontrar en otro lugar de Ecuador.","rating":5,"author":"Oliver_H_Suecia","date":"2025-09-20","location_name":"Parque Nacional Podocarpus","location_type":"Área Natural","helpful_votes":112},
    {"review_id":"ta_032","title":"Festival que hay que vivir","text":"El FIAVL es de esas experiencias que te cambian la percepción del arte. Ver circo contemporáneo y danza de talla mundial en las calles de una ciudad andina es mágico.","rating":5,"author":"Marie_C_Bélgica","date":"2025-11-19","location_name":"Festival Internacional de Artes Vivas","location_type":"Festival","helpful_votes":178},
    {"review_id":"ta_033","title":"La romería es una experiencia de vida","text":"Caminar con miles de peregrinos hacia El Cisne bajo la lluvia y el sol es una experiencia que marca. La solidaridad y fe de la gente es conmovedora.","rating":5,"author":"Carmen_S_México","date":"2025-08-16","location_name":"Santuario de El Cisne","location_type":"Iglesia","helpful_votes":143},
    {"review_id":"ta_034","title":"Vilcabamba, el secreto mejor guardado","text":"No entiendo cómo Vilcabamba no es más famoso. El microclima es perfecto, la naturaleza es espectacular y el ambiente es increíblemente tranquilo y seguro.","rating":5,"author":"James_B_Australia","date":"2025-08-25","location_name":"Valle de Vilcabamba","location_type":"Área Natural","helpful_votes":198},
    {"review_id":"ta_035","title":"Arte urbano en el FIAVL","text":"El arte callejero durante el FIAVL transforma la ciudad. Cada esquina es una galería viva. Los artistas interactúan con el público de manera brillante.","rating":5,"author":"Lucia_M_Uruguay","date":"2025-11-16","location_name":"Centro Histórico Loja","location_type":"Zona Histórica","helpful_votes":87},
    {"review_id":"ta_036","title":"Loja supera expectativas","text":"Vine con expectativas moderadas y Loja las superó con creces. Ciudad limpia, segura, cultural y con una naturaleza extraordinaria a 30 minutos del centro.","rating":5,"author":"Hans_G_Suiza","date":"2025-10-28","location_name":"Loja, Ecuador","location_type":"Ciudad","helpful_votes":156},
    {"review_id":"ta_037","title":"Podocarpus en temporada lluviosa","text":"Visité Podocarpus en época de lluvia y fue igualmente impresionante. El bosque nublado cobra vida con la niebla. Lleva buen impermeable y botas.","rating":4,"author":"Patricia_A_Venezuela","date":"2025-02-18","location_name":"Parque Nacional Podocarpus","location_type":"Área Natural","helpful_votes":67},
    {"review_id":"ta_038","title":"El FIAVL debe ser Patrimonio","text":"El Festival Internacional de Artes Vivas de Loja debería ser declarado Patrimonio Cultural. Es un evento de una calidad artística que pocas ciudades latinoamericanas pueden ofrecer.","rating":5,"author":"Felipe_R_Santiago","date":"2025-11-20","location_name":"Festival Internacional de Artes Vivas","location_type":"Festival","helpful_votes":234},
    {"review_id":"ta_039","title":"La fe de El Cisne conmueve","text":"Aunque no soy muy religioso, la romería de El Cisne me conmovió profundamente. La fe colectiva y la tradición que se mantiene por siglos es algo muy especial.","rating":5,"author":"Daniel_M_Francia","date":"2025-08-15","location_name":"Santuario de El Cisne","location_type":"Iglesia","helpful_votes":123},
    {"review_id":"ta_040","title":"Disfruté cada momento en Loja","text":"Pasé una semana en Loja y no me aburrí ni un momento. FIAVL, gastronomía, naturaleza, museos... la ciudad tiene una oferta cultural y turística impresionante.","rating":5,"author":"Angela_P_Ecuador","date":"2025-11-22","location_name":"Loja, Ecuador","location_type":"Ciudad","helpful_votes":189},
    {"review_id":"ta_041","title":"Guías excelentes en Podocarpus","text":"Los guías del Parque Podocarpus conocen cada planta y animal. Fue una clase de biología en vivo. El parque está bien conservado gracias a su gestión.","rating":5,"author":"Zhang_W_China","date":"2025-05-30","location_name":"Parque Nacional Podocarpus","location_type":"Área Natural","helpful_votes":78},
    {"review_id":"ta_042","title":"Vilcabamba para retiro espiritual","text":"Vine a Vilcabamba a hacer un retiro de yoga y meditación y fue perfecto. El ambiente de paz y la naturaleza facilitan la introspección. Hay excelentes opciones de bienestar.","rating":5,"author":"Sarah_K_USA","date":"2025-09-12","location_name":"Valle de Vilcabamba","location_type":"Área Natural","helpful_votes":145},
    {"review_id":"ta_043","title":"FIAVL: Arte para todos","text":"Lo que más me gustó del FIAVL es que es completamente gratuito y accesible para todos. Arte de nivel mundial sin exclusiones. Eso dice mucho de Loja como ciudad.","rating":5,"author":"Esther_N_Países Bajos","date":"2025-11-18","location_name":"Festival Internacional de Artes Vivas","location_type":"Festival","helpful_votes":212},
    {"review_id":"ta_044","title":"Independencia de Loja, fiesta cívica","text":"Asistí a los festejos del 18 de noviembre, aniversario de la independencia de Loja. El desfile fue emotivo y lleno de orgullo. La ciudad vibra con patriotismo en esa fecha.","rating":4,"author":"Gabriela_T_Quito","date":"2024-11-19","location_name":"Centro Histórico Loja","location_type":"Zona Histórica","helpful_votes":56},
    {"review_id":"ta_045","title":"Atardecer desde la Puerta de la Ciudad","text":"Ver el atardecer desde la Puerta de la Ciudad de Loja es un espectáculo. La ciudad se pinta de dorado y la vista del valle es simplemente hermosa.","rating":5,"author":"Thomas_B_Alemania","date":"2025-07-22","location_name":"Puerta de la Ciudad","location_type":"Monumento","helpful_votes":89},
    {"review_id":"ta_046","title":"Música en el ADN de Loja","text":"El Museo de la Música de Loja explica perfectamente por qué esta ciudad es conocida como la capital musical del Ecuador. Salí con más respeto aún por la cultura lojana.","rating":5,"author":"Pilar_S_España","date":"2025-05-08","location_name":"Museo de la Música de Loja","location_type":"Museo","helpful_votes":67},
    {"review_id":"ta_047","title":"Loja en el top de Ecuador","text":"Después de visitar Quito, Cuenca y Loja, puedo decir que Loja tiene una personalidad única. Menos turística que las otras dos pero igual de fascinante en cultura y naturaleza.","rating":5,"author":"Kevin_M_Irlanda","date":"2025-09-28","location_name":"Loja, Ecuador","location_type":"Ciudad","helpful_votes":167},
    {"review_id":"ta_048","title":"El arte vive en Loja","text":"El FIAVL 2025 fue mi primera vez en Loja y me enamoré de la ciudad. La combinación del festival con el contexto andino es única en el mundo. Regresaré sin duda.","rating":5,"author":"Amelia_T_Nueva Zelanda","date":"2025-11-21","location_name":"Festival Internacional de Artes Vivas","location_type":"Festival","helpful_votes":198},
    {"review_id":"ta_049","title":"Cisne, más que una romería","text":"La romería de El Cisne no es solo un evento religioso, es una manifestación cultural y social única. La unión que se genera entre los peregrinos es algo muy especial.","rating":5,"author":"Valentín_P_Argentina","date":"2025-08-16","location_name":"Santuario de El Cisne","location_type":"Iglesia","helpful_votes":134},
    {"review_id":"ta_050","title":"Experiencia completa en Loja","text":"En 10 días en Loja viví el FIAVL, hice trekking en Podocarpus, visité Vilcabamba y conocí El Cisne. Fue el viaje más completo y emocionante de mi vida.","rating":5,"author":"Lucas_F_Brasil","date":"2025-11-25","location_name":"Loja, Ecuador","location_type":"Ciudad","helpful_votes":278},
]

def _ahora():
    return datetime.now(timezone.utc).isoformat()

class ConectorTripAdvisorMock(ConectorBase):
    """
    ══════════════════════════════════════════════════════════
    CONECTOR TRIPADVISOR — MODO MOCK
    ══════════════════════════════════════════════════════════
    API REAL: TripAdvisor Content API

    1. Regístrate en: https://tripadvisor-content-api.readme.io/
    2. Obtén API Key gratuita (plan básico disponible)
    3. Agrega al .env: TRIPADVISOR_API_KEY=...

    4. Flujo real:
       # Buscar ubicación
       GET /location/search?searchQuery={query}&language=es&key={key}
       # Obtener reseñas
       GET /location/{location_id}/reviews?language=es&key={key}

    5. Mapeo al esquema:
       origen.id_externo  = review["id"]
       origen.formato     = "reseña"
       metadata.metricas.likes = review["helpful_votes"]
       metadata.texto_original = review["text"]
    ══════════════════════════════════════════════════════════
    """
    nombre = "TripAdvisor"

    def extraer_raw(self, tags: list[str]) -> list[dict]:
        if not tags:
            return REVIEWS_RAW
        q = [t.lower() for t in tags]
        return [
            r for r in REVIEWS_RAW
            if any(
                t in r["title"].lower() or
                t in r["text"].lower() or
                t in r["location_name"].lower() or
                t in (r.get("location_type") or "").lower()
                for t in q
            )
        ]
