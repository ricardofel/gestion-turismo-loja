from .tiktok      import ConectorTikTokMock
from .youtube     import ConectorYouTubeMock
from .google      import ConectorGoogleReviewsMock
from .instagram   import ConectorInstagramMock
from .tripadvisor import ConectorTripAdvisorMock
from .flickr      import ConectorFlickrMock
from .eventbrite  import ConectorEventbriteMock
from .base        import ConectorBase

CONECTORES: dict[str, ConectorBase] = {
    "TikTok"       : ConectorTikTokMock(),
    "YouTube"      : ConectorYouTubeMock(),
    "GoogleReviews": ConectorGoogleReviewsMock(),
    "Instagram"    : ConectorInstagramMock(),
    "TripAdvisor"  : ConectorTripAdvisorMock(),
    "Flickr"       : ConectorFlickrMock(),
    "Eventbrite"   : ConectorEventbriteMock(),
}
