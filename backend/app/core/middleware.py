import hashlib
import json
import logging
import time
import uuid
from starlette.responses import JSONResponse
from .errors import PublicError

logger = logging.getLogger("plantcare.requests")


class RequestBoundaryMiddleware:
    """Bound bodies BEFORE multipart parsing; never stores more than the configured cap.

    This bounded in-memory buffer also makes partial multipart cleanup predictable.
    A global admission cap covers uploads and analysis, including slow-body requests.
    """
    def __init__(self, app, settings):
        self.app = app
        self.settings = settings
        self.active_uploads = 0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id = str(uuid.uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        started = time.perf_counter()
        status = 500
        disconnected = False
        acquired = False

        async def wrapped_send(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message.setdefault("headers", []).append((b"x-request-id", request_id.encode()))
                message["headers"].append((b"x-content-type-options", b"nosniff"))
                message["headers"].append((b"cache-control", b"no-store"))
            await send(message)

        try:
            if scope["path"] == "/api/analyze" and scope["method"] == "POST":
                if self.active_uploads >= self.settings.max_concurrent_analyses:
                    raise PublicError(503, "service_busy", "Analysis is busy. Please try again shortly.", 2)
                self.active_uploads += 1
                acquired = True
                headers = dict(scope["headers"])
                declared = headers.get(b"content-length")
                if declared:
                    try:
                        if int(declared) > self.settings.max_request_bytes:
                            raise PublicError(413, "image_too_large", "The image exceeds the 10 MiB upload limit.")
                    except ValueError:
                        raise PublicError(400, "invalid_request", "Invalid Content-Length.")
                body = bytearray()
                # Reading is bounded in size and time, including chunked requests.
                import asyncio
                async with asyncio.timeout(20):
                    while True:
                        message = await receive()
                        if message["type"] == "http.disconnect":
                            disconnected = True
                            return
                        if message["type"] != "http.request":
                            continue
                        chunk = message.get("body", b"")
                        if len(body) + len(chunk) > self.settings.max_request_bytes:
                            raise PublicError(413, "image_too_large", "The image exceeds the 10 MiB upload limit.")
                        body.extend(chunk)
                        if not message.get("more_body", False):
                            break
                body_bytes = bytes(body)
                body.clear()
                delivered = False
                original_receive = receive

                async def bounded_receive():
                    nonlocal delivered, body_bytes
                    if not delivered:
                        delivered = True
                        result = body_bytes
                        body_bytes = b""
                        return {"type": "http.request", "body": result, "more_body": False}
                    return await original_receive()
                await self.app(scope, bounded_receive, wrapped_send)
            else:
                await self.app(scope, receive, wrapped_send)
        except PublicError as exc:
            response = JSONResponse(
                {"code": exc.code, "message": exc.message, "request_id": request_id},
                status_code=exc.status_code,
                headers={"Retry-After": str(exc.retry_after)} if exc.retry_after else None,
            )
            await response(scope, receive, wrapped_send)
        except TimeoutError:
            await JSONResponse(
                {"code": "upload_timeout", "message": "Image upload timed out. Please try again.", "request_id": request_id},
                status_code=408,
            )(scope, receive, wrapped_send)
        finally:
            if acquired:
                self.active_uploads -= 1
            logger.info(json.dumps({
                "event": "http_request", "request_id": request_id,
                "method": scope["method"], "path": scope["path"], "status": status,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "disconnected": disconnected,
            }))


class QuotaService:
    """Redis provides shared atomic quotas. The fallback is explicitly per process."""
    def __init__(self, settings):
        self.settings = settings
        self.redis = None
        self.counters = {}

    async def start(self):
        if self.settings.redis_url:
            from redis.asyncio import Redis
            self.redis = Redis.from_url(self.settings.redis_url, socket_timeout=2, socket_connect_timeout=2)
            await self.redis.ping()

    async def close(self):
        if self.redis:
            await self.redis.aclose()

    async def take(self, key: str, limit: int, period: int):
        now = int(time.time())
        bucket = now // period
        cache_key = "plantcare:" + key + ":" + str(bucket)
        if self.redis:
            # Atomic INCR + expiry; failures fail closed instead of allowing uncapped paid calls.
            script = "local n=redis.call('INCR',KEYS[1]);if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end;return n"
            try:
                count = await self.redis.eval(script, 1, cache_key, period + 1)
            except Exception:
                raise PublicError(503, "quota_service_unavailable", "Request limiting is temporarily unavailable.")
        else:
            if len(self.counters) > 10000:
                self.counters = {k: v for k, v in self.counters.items() if v[1] > now}
            current = self.counters.get(cache_key, (0, now + period + 1))
            count = current[0] + 1
            self.counters[cache_key] = (count, current[1])
        if count > limit:
            raise PublicError(429, "rate_limited", "Too many requests. Please try again later.", period - now % period)

    async def take_request(self, address: str):
        digest = hashlib.sha256((self.settings.rate_limit_salt + address).encode()).hexdigest()
        await self.take("request:" + digest, self.settings.rate_limit_per_minute, 60)

    async def take_gemini(self):
        await self.take("gemini:global", self.settings.gemini_daily_request_limit, 86400)
