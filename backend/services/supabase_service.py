import httpx
from typing import Dict, Any, Optional
from backend.config import settings

class SupabaseService:
    """
    Supabase REST Client & Sync Service.
    Connects to the upay Ops Intelligence Supabase project.
    """

    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def check_health(self) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(f"{self.url}/auth/v1/health", headers={"apikey": self.key})
                return {
                    "connected": r.status_code == 200,
                    "url": self.url,
                    "status_code": r.status_code,
                    "service": "Supabase GoTrue & PostgREST"
                }
        except Exception as e:
            return {
                "connected": False,
                "url": self.url,
                "error": str(e)
            }

    def sync_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upserts a dispute case to Supabase cases table via REST."""
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{self.url}/rest/v1/cases",
                    headers=self.headers,
                    json=case_data
                )
                if resp.status_code in [200, 201]:
                    return {"synced": True, "data": resp.json()}
                return {"synced": False, "status_code": resp.status_code, "detail": resp.text}
        except Exception as e:
            return {"synced": False, "error": str(e)}

supabase_service = SupabaseService()
