import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from briefing_analyzer import AnalysisResult

logger = logging.getLogger(__name__)

LOCAL_CONTEXT_DIR = "/tmp/wpb_context"
HISTORY_DAYS = int(os.getenv("BRIEFING_HISTORY_DAYS", "30"))


class ContextStore:
    """
    Persists article coverage history to prevent repeated talking points.
    Primary backend: GCS. Falls back to local /tmp on GCS failure.
    """

    def __init__(self):
        self._gcs_client = None
        self._bucket_name = os.getenv("GCS_BUCKET_NAME", "")
        os.makedirs(LOCAL_CONTEXT_DIR, exist_ok=True)

    def _gcs(self):
        if self._gcs_client is None and self._bucket_name:
            try:
                from google.cloud import storage
                self._gcs_client = storage.Client()
            except Exception as e:
                logger.warning(f"GCS client unavailable: {e}")
        return self._gcs_client

    def _gcs_key(self, user_id: str) -> str:
        return f"context/{user_id}_context.json"

    def _local_path(self, user_id: str) -> str:
        return os.path.join(LOCAL_CONTEXT_DIR, f"{user_id}_context.json")

    def load_context(self, user_id: str) -> dict:
        raw = self._load_raw(user_id)
        if not raw:
            return {"covered_urls": [], "covered_topics": [], "last_updated": None}

        cutoff = datetime.now(timezone.utc) - timedelta(days=HISTORY_DAYS)
        raw["covered_urls"] = [
            entry for entry in raw.get("covered_urls", [])
            if self._is_recent(entry.get("date"), cutoff)
        ]
        return {
            "covered_urls": [e["url"] for e in raw["covered_urls"]],
            "covered_topics": raw.get("covered_topics", [])[-30:],
            "last_updated": raw.get("last_updated"),
        }

    def update_context(self, user_id: str, analysis: AnalysisResult, date_str: str):
        raw = self._load_raw(user_id) or {"covered_urls": [], "covered_topics": []}

        existing_urls = {e["url"] for e in raw.get("covered_urls", [])}
        for article in analysis.scored_articles:
            if article.article_url not in existing_urls:
                raw["covered_urls"].append({"url": article.article_url, "date": date_str})

        new_topics = [tp.headline for tp in analysis.talking_points]
        raw["covered_topics"] = (raw.get("covered_topics", []) + new_topics)[-60:]
        raw["last_updated"] = date_str

        self._save_raw(user_id, raw)

    def _load_raw(self, user_id: str) -> Optional[dict]:
        gcs = self._gcs()
        if gcs and self._bucket_name:
            try:
                bucket = gcs.bucket(self._bucket_name)
                blob = bucket.blob(self._gcs_key(user_id))
                if blob.exists():
                    return json.loads(blob.download_as_text())
            except Exception as e:
                logger.warning(f"GCS context load failed, using local: {e}")

        local = self._local_path(user_id)
        if os.path.exists(local):
            try:
                with open(local) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Local context load failed: {e}")
        return None

    def _save_raw(self, user_id: str, data: dict):
        payload = json.dumps(data, indent=2)

        gcs = self._gcs()
        if gcs and self._bucket_name:
            try:
                bucket = gcs.bucket(self._bucket_name)
                bucket.blob(self._gcs_key(user_id)).upload_from_string(
                    payload, content_type="application/json"
                )
            except Exception as e:
                logger.warning(f"GCS context save failed: {e}")

        try:
            with open(self._local_path(user_id), "w") as f:
                f.write(payload)
        except Exception as e:
            logger.error(f"Local context save failed: {e}")

    @staticmethod
    def _is_recent(date_str: Optional[str], cutoff: datetime) -> bool:
        if not date_str:
            return True
        try:
            dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
            return dt >= cutoff
        except Exception:
            return True
