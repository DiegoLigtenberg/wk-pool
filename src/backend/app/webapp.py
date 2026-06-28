import argparse
import json
import os
import traceback
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app.tournament import build_tournament_view


DEFAULT_HOST = "127.0.0.1"
DEPLOY_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
ALLOWED_ORIGINS_ENV = "WK_POOL_ALLOWED_ORIGINS"
SYNC_SECRET_ENV = "FOOTBALL_SYNC_SECRET"
DEFAULT_ALLOWED_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
    "https://wk-pool.up.railway.app",
)
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; base-uri 'none'; frame-ancestors 'none'",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": "camera=(), geolocation=(), microphone=()",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
}


def health_payload() -> dict[str, str]:
    return {"status": "ok", "service": "wk-pool-backend"}


@lru_cache(maxsize=1)
def cached_tournament_view() -> dict[str, object]:
    """Cache tournament JSON ,  eerste call ~0.5s, daarna instant."""
    return build_tournament_view()


def clear_tournament_cache() -> None:
    cached_tournament_view.cache_clear()


def sync_secret() -> str | None:
    configured = os.environ.get(SYNC_SECRET_ENV)
    if configured is None:
        return None
    configured = configured.strip()
    return configured or None


def authorized_sync(authorization: str | None) -> bool:
    secret = sync_secret()
    if secret is None:
        return False
    if authorization is None or not authorization.startswith("Bearer "):
        return False
    token = authorization[7:].strip()
    return token == secret


def allowed_cors_origins() -> tuple[str, ...]:
    configured_origins = os.environ.get(ALLOWED_ORIGINS_ENV)
    if configured_origins is None:
        return DEFAULT_ALLOWED_ORIGINS

    return tuple(origin.strip() for origin in configured_origins.split(",") if origin.strip())


class WkPoolRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path == "/health":
            self._send_json(health_payload())
            return

        if path == "/api/tournament":
            try:
                self._send_json(cached_tournament_view())
            except (ConnectionAbortedError, BrokenPipeError):
                return
            except Exception as exc:
                traceback.print_exc()
                try:
                    self._send_json(
                        {
                            "error": "Failed to build tournament view",
                            "detail": str(exc),
                        },
                        status=500,
                    )
                except (ConnectionAbortedError, BrokenPipeError):
                    pass
            return

        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path

        if path == "/internal/sync-football":
            self._handle_sync_football()
            return

        self._send_json({"error": "Not found"}, status=404)

    def _handle_sync_football(self) -> None:
        if sync_secret() is None:
            self._send_json({"error": "FOOTBALL_SYNC_SECRET is not configured"}, status=503)
            return

        if not authorized_sync(self.headers.get("Authorization")):
            self._send_json({"error": "Unauthorized"}, status=401)
            return

        provider = os.environ.get("FOOTBALL_DATA_PROVIDER", "espn").strip().lower()
        if provider in {"api-football", "apifootball", "api_football"} and not os.environ.get(
            "FOOTBALL_API_KEY"
        ):
            self._send_json({"error": "FOOTBALL_API_KEY is not configured"}, status=503)
            return

        query = parse_qs(urlparse(self.path).query)
        force_remap = query.get("force-remap", [""])[0] in {"1", "true", "yes"}

        try:
            from app.football_sync import sync_results

            synced = sync_results(force_remap=force_remap)
            clear_tournament_cache()
            self._send_json({"status": "ok", "synced": synced})
        except Exception as exc:
            traceback.print_exc()
            self._send_json(
                {
                    "error": "Football sync failed",
                    "detail": str(exc),
                },
                status=500,
            )

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_common_headers()
        self.end_headers()

    def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._send_common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (ConnectionAbortedError, BrokenPipeError):
            pass

    def _send_common_headers(self) -> None:
        self._send_cors_headers()
        for header, value in SECURITY_HEADERS.items():
            self.send_header(header, value)

    def _send_cors_headers(self) -> None:
        origin = self.headers.get("Origin")
        if origin not in allowed_cors_origins():
            return

        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Vary", "Origin")

    def log_message(self, format: str, *args: object) -> None:
        return


def create_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), WkPoolRequestHandler)


def default_host() -> str:
    configured_host = os.environ.get("HOST")
    if configured_host:
        return configured_host

    if os.environ.get("PORT") or os.environ.get("RAILWAY_ENVIRONMENT"):
        return DEPLOY_HOST

    return DEFAULT_HOST


def default_port() -> int:
    configured_port = os.environ.get("PORT")
    if configured_port is None:
        return DEFAULT_PORT

    return int(configured_port)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the WK Pool backend.")
    parser.add_argument("--host", default=default_host())
    parser.add_argument("--port", default=default_port(), type=int)
    args = parser.parse_args(argv)

    server = create_server(args.host, args.port)
    print(f"Serving WK Pool backend at http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping WK Pool backend.")
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
