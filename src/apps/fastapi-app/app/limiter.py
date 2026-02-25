"""
Per-session inbound rate limiter (slowapi).

Key function uses the session_id set by SessionMiddleware on request.state.
One session = one anonymous user browser tab.
"""
from slowapi import Limiter


def _get_session_id(request):
    return getattr(request.state, "session_id", request.client.host if request.client else "unknown")


limiter = Limiter(key_func=_get_session_id)
