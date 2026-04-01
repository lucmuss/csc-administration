from django.utils.cache import add_never_cache_headers


class NoStorePageCacheMiddleware:
    """Prevent browsers from re-showing protected pages after logout via history cache."""

    AUTH_PATH_PREFIXES = (
        "/accounts/login/",
        "/accounts/logout/",
        "/accounts/password-reset/",
        "/accounts/reset/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        should_disable_cache = (
            getattr(getattr(request, "user", None), "is_authenticated", False)
            or any(request.path.startswith(prefix) for prefix in self.AUTH_PATH_PREFIXES)
        )
        if should_disable_cache:
            add_never_cache_headers(response)
            response.headers.setdefault("Pragma", "no-cache")
            response.headers.setdefault("Expires", "0")
        return response
