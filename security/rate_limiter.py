"""
Rate Limiting Module
Protects against API abuse and brute force attacks
"""
import time
import redis
import hashlib
from typing import Dict, Optional
from flask import request, jsonify
from functools import wraps
import logging
import os

logger = logging.getLogger(__name__)

# Check if Redis is available
REDIS_AVAILABLE = True
try:
    redis_client = redis.Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
    redis_client.ping()
    logger.info("✓ Redis available")
except Exception as e:
    logger.warning(f"Redis not available: {e}")
    REDIS_AVAILABLE = False


class RateLimiter:
    """Redis-based rate limiter with sliding window"""

    def __init__(self, redis_client=None):
        """Initialize rate limiter with optional Redis client"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available. Rate limiting disabled.")
            self.redis_client = None
            self.use_redis = False
            self.fallback_cache = {}
            return

        self.redis_client = redis_client
        self.fallback_cache = {}  # In-memory fallback
        self.use_redis = redis_client is not None

    def _get_client_id(self) -> str:
        """Generate unique client identifier"""
        # Use IP + User-Agent for identification
        ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        return hashlib.md5(f"{ip}:{user_agent}".encode()).hexdigest()

    def _get_key(self, endpoint: str, client_id: str = None) -> str:
        """Generate Redis key for rate limiting"""
        if not client_id:
            client_id = self._get_client_id()
        return f"rate_limit:{endpoint}:{client_id}"

    def is_allowed(self, endpoint: str, limit: int, window: int) -> tuple[bool, Dict]:
        """
        Check if request is allowed under rate limit

        Args:
            endpoint: API endpoint name
            limit: Number of requests allowed
            window: Time window in seconds

        Returns:
            (allowed: bool, info: dict)
        """
        key = self._get_key(endpoint)
        current_time = int(time.time())

        if not REDIS_AVAILABLE:
             return True, {
                    'limit': limit,
                    'remaining': limit,
                    'reset_time': current_time + window,
                    'request_count': 0
                }

        if self.use_redis and self.redis_client:
            try:
                # Redis sliding window implementation
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, current_time - window)
                pipe.zadd(key, {str(current_time): current_time})
                pipe.zcount(key, current_time - window, current_time)
                pipe.expire(key, window)
                results = pipe.execute()

                request_count = results[2]
                allowed = request_count <= limit

                return allowed, {
                    'limit': limit,
                    'remaining': max(0, limit - request_count),
                    'reset_time': current_time + window,
                    'request_count': request_count
                }

            except Exception as e:
                logger.error(f"Redis rate limiting error: {e}")
                self.use_redis = False
                self.redis_client = None
                # Fall back to in-memory

        # Fallback in-memory implementation
        if key not in self.fallback_cache:
            self.fallback_cache[key] = []

        # Clean old requests
        self.fallback_cache[key] = [
            req_time for req_time in self.fallback_cache[key]
            if req_time > current_time - window
        ]

        # Add current request
        self.fallback_cache[key].append(current_time)

        request_count = len(self.fallback_cache[key])
        allowed = request_count <= limit

        return allowed, {
            'limit': limit,
            'remaining': max(0, limit - request_count),
            'reset_time': current_time + window,
            'request_count': request_count
        }


# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(limit: int, window: int = 60, endpoint: str = None):
    """
    Rate limiting decorator

    Args:
        limit: Number of requests allowed
        window: Time window in seconds (default: 60)
        endpoint: Custom endpoint name (default: auto-detect)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            endpoint_name = endpoint or f.__name__

            allowed, info = rate_limiter.is_allowed(endpoint_name, limit, window)

            if not allowed:
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Limit: {limit} per {window} seconds',
                    'retry_after': info['reset_time'] - int(time.time())
                })
                response.status_code = 429
                response.headers['X-RateLimit-Limit'] = str(limit)
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(info['reset_time'])
                response.headers['Retry-After'] = str(info['reset_time'] - int(time.time()))
                return response

            # Add rate limit headers to successful responses
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(limit)
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(info['reset_time'])

            return response
        return decorated_function
    return decorator


# Common rate limiting configurations
RATE_LIMITS = {
    'login': (5, 300),          # 5 attempts per 5 minutes
    'register': (3, 3600),      # 3 registrations per hour
    'api_general': (100, 60),   # 100 requests per minute
    'trading': (20, 60),        # 20 trading requests per minute
    'password_reset': (3, 3600) # 3 password resets per hour
}

def apply_rate_limit(endpoint_type: str):
    """Apply predefined rate limit for endpoint type"""
    if endpoint_type in RATE_LIMITS:
        limit, window = RATE_LIMITS[endpoint_type]
        return rate_limit(limit, window, endpoint_type)
    return rate_limit(100, 60)  # Default rate limit