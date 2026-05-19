"""ActivityWatch data fetcher module.

Handles connection to ActivityWatch REST API and retrieves event data.
"""

import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo


class ActivityWatchFetcher:
    """Fetches data from ActivityWatch server."""
    
    def __init__(self, host: str = "localhost", port: int = 5600, timezone_str: str = "Asia/Shanghai"):
        self.base_url = f"http://{host}:{port}/api/0"
        self.session = requests.Session()
        self.timezone = ZoneInfo(timezone_str)
        self.utc = timezone.utc
        
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """Make GET request to ActivityWatch API."""
        url = urljoin(self.base_url + "/", endpoint)
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to ActivityWatch at {self.base_url}. "
                "Please ensure ActivityWatch is running."
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(
                f"Connection to ActivityWatch at {self.base_url} timed out."
            )
    
    def get_buckets(self) -> Dict[str, Any]:
        """Get all available buckets."""
        return self._get("buckets/")
    
    def get_bucket_events(
        self, 
        bucket_id: str, 
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 10000
    ) -> List[Dict[str, Any]]:
        """Get events from a specific bucket within time range."""
        params = {"limit": limit}
        
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()
            
        return self._get(f"buckets/{bucket_id}/events", params)
    
    def get_today_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch all relevant data for today."""
        now = datetime.now(self.timezone)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        buckets = self.get_buckets()
        
        # Find bucket IDs
        window_bucket = None
        web_bucket = None
        afk_bucket = None
        
        for bucket_id, info in buckets.items():
            if info.get("type") == "currentwindow":
                window_bucket = bucket_id
            elif info.get("type") == "web.tab.current":
                web_bucket = bucket_id
            elif info.get("type") == "afkstatus":
                afk_bucket = bucket_id
        
        data = {
            "window": [],
            "web": [],
            "afk": []
        }
        
        if window_bucket:
            data["window"] = self.get_bucket_events(window_bucket, start, end)
        if web_bucket:
            data["web"] = self.get_bucket_events(web_bucket, start, end)
        if afk_bucket:
            data["afk"] = self.get_bucket_events(afk_bucket, start, end)
            
        return data
    
    def get_date_data(
        self, 
        date: datetime
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch all relevant data for a specific date."""
        # Ensure date has timezone info
        if date.tzinfo is None:
            date = date.replace(tzinfo=self.timezone)
        
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        buckets = self.get_buckets()
        
        window_bucket = None
        web_bucket = None
        afk_bucket = None
        
        for bucket_id, info in buckets.items():
            if info.get("type") == "currentwindow":
                window_bucket = bucket_id
            elif info.get("type") == "web.tab.current":
                web_bucket = bucket_id
            elif info.get("type") == "afkstatus":
                afk_bucket = bucket_id
        
        data = {
            "window": [],
            "web": [],
            "afk": []
        }
        
        if window_bucket:
            data["window"] = self.get_bucket_events(window_bucket, start, end)
        if web_bucket:
            data["web"] = self.get_bucket_events(web_bucket, start, end)
        if afk_bucket:
            data["afk"] = self.get_bucket_events(afk_bucket, start, end)
            
        return data
    
    def check_connection(self) -> bool:
        """Check if ActivityWatch server is accessible."""
        try:
            response = self.session.get(
                urljoin(self.base_url + "/", "info"), 
                timeout=5
            )
            return response.status_code == 200
        except:
            return False