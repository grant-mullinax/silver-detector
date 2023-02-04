from requests_cache import CacheMixin
from requests_ratelimiter import LimiterMixin
from requests import Session


class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    """Session class with caching and rate-limiting behavior. Accepts arguments for both

    LimiterSession and CachedSession.

    """
