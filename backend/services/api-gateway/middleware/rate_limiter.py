import sys
import os
import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "shared"))

from redis_client import get_redis, CacheService

EXCLUDED_PATHS = {"/health", "/ready"}
RATE_LIMIT = 60  # requests per minute


class RateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            # Use IP address for unauthenticated requests
            user_id = request.client.host if request.client else "anonymous"

        endpoint = request.url.path
        try:
            redis = await get_redis()
            cache = CacheService(redis)
            allowed = await cache.check_rate_limit(user_id, endpoint, limit=RATE_LIMIT)
            if not allowed:
                return JSONResponse(
                    {"detail": "Rate limit exceeded. Try again in 60 seconds."},
                    status_code=429,
                    headers={"Retry-After": "60"},
                )
        except Exception as e:
            logging.warning(f"Rate limiter error (allowing request): {e}")

        return await call_next(request)
