import os
import sys
from pathlib import Path

# Add project root to sys.path so backend modules import properly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Flag Vercel environment
os.environ["VERCEL"] = "1"

# Import base FastAPI app
from backend.main import app as base_app

# ASGI Middleware to correct Vercel path rewrites
class VercelPathMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            path = scope.get("path", "")
            if "/index.py" in path:
                scope["path"] = path.replace("/api/index.py", "/api")
            else:
                for name, val in scope.get("headers", []):
                    name_lower = name.lower()
                    if name_lower in (b"x-forwarded-uri", b"x-matched-path", b"x-vercel-forwarded-path"):
                        decoded = val.decode("utf-8").split("?")[0]
                        if decoded and "/index.py" not in decoded:
                            scope["path"] = decoded
                            break
        await self.app(scope, receive, send)

app = VercelPathMiddleware(base_app)
