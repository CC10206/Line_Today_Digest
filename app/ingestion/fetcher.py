import logging
from datetime import UTC, datetime

import feedparser
from bs4 import BeautifulSoup

from app.config import settings

logger = logging.getLogger(__name__)


def fetch_all() -> dict[str, list[dict]]:
    results: dict[str, list[dict]] = {}
    for feed in settings.feeds:
        try:
            results[feed.name] = _fetch_one(feed.name, feed.url)
        except Exception:
            logger.warning("failed to fetch feed %s (%s)", feed.name, feed.url, exc_info=True)
            results[feed.name] = []
    return results


def _fetch_one(source: str, url: str) -> list[dict]:
    parsed = feedparser.parse(url)
    rows = []
    for entry in parsed.entries:
        published_at = _parse_published(entry)
        if published_at is None or "link" not in entry or "title" not in entry:
            continue
        rows.append(
            {
                "url": entry.link,
                "source": source,
                "title": entry.title,
                "content": _clean_html(entry.get("summary", "")),
                "image_url": None,
                "published_at": published_at,
            }
        )
    return rows


def _clean_html(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)


def _parse_published(entry) -> datetime | None:
    parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed_time is None:
        return None
    return datetime(*parsed_time[:6], tzinfo=UTC)
