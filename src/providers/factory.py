"""Factory for creating and resolving Instagram data providers."""
import os
from typing import Optional

from src.providers.base import BaseInstagramProvider, ProviderError
from src.providers.mock_provider import MockInstagramProvider


def get_provider(name: Optional[str] = None) -> BaseInstagramProvider:
    """Resolve and return an active Instagram data provider.
    
    Order of precedence:
    1. Explicit `name` argument ("instagrapi", "mock")
    2. INSTAGRAM_PROVIDER or INSTAGRAM_BACKEND environment variables
    3. Auto-detection: if a saved instagrapi session exists, use instagrapi
    4. Otherwise, fallback to MockInstagramProvider (safe offline default)
    """
    provider_name = (
        name
        or os.getenv("INSTAGRAM_PROVIDER")
        or os.getenv("INSTAGRAM_BACKEND")
        or ""
    ).lower().strip()

    if provider_name == "hikerapi":
        raise ProviderError(
            "HikerAPI is a paid service and has been removed from Osgram. "
            "Please use the free 'instagrapi' provider or 'mock' for offline testing."
        )

    if provider_name in ("mock", "test", "synthetic"):
        return MockInstagramProvider()

    if provider_name == "instagrapi":
        from src.providers.instagrapi_provider import (
            InstagrapiProvider,
            resolve_instagrapi_credentials,
            session_exists,
        )

        if not session_exists():
            raise ProviderError(
                "instagrapi provider selected but no saved session found at "
                "config/instagrapi_session.json. Run `python scripts/instagrapi_login.py` "
                "first to log in."
            )
        u, p = resolve_instagrapi_credentials()
        return InstagrapiProvider(username=u, password=p)

    # Auto-detection
    from src.providers.instagrapi_provider import (
        InstagrapiProvider,
        resolve_instagrapi_credentials,
        session_exists,
    )

    if session_exists():
        u, p = resolve_instagrapi_credentials()
        return InstagrapiProvider(username=u, password=p)

    raise ProviderError(
        "No configured provider or authenticated session found. "
        "To use the free real Instagram provider, configure config/credentials.ini and run "
        "`python scripts/instagrapi_login.py`. To run offline tests with synthetic data, "
        "explicitly specify `-p mock` or set `INSTAGRAM_BACKEND=mock`."
    )

