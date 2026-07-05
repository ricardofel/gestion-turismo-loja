from .youtube import ConectorYouTubeReal
from .base    import ConectorBase

# Flickr quedó fuera: su API dejó de emitir keys nuevas a cuentas gratuitas
# (ahora exige suscripción Flickr Pro). El conector real sigue escrito en
# flickr.py por si el proyecto consigue una key Pro más adelante.
#
# TikTok, Instagram, TripAdvisor, Eventbrite y Google Reviews siguen en modo
# mock en sus archivos respectivos — quedan fuera de este registro hasta tener
# credenciales reales aprobadas (ver guia_implementacion_apis.md). Para
# reactivar una fuente, impórtala aquí y agrégala al diccionario.
CONECTORES: dict[str, ConectorBase] = {
    "YouTube": ConectorYouTubeReal(),
}
