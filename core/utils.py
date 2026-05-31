import re
import logging

logger = logging.getLogger(__name__)

DOMAIN_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
)


def sanitize_domain(raw: str) -> str | None:
    raw = (raw or "").strip().lower()
    raw = re.sub(r"^https?://", "", raw)
    raw = raw.split("/")[0].split(":")[0].split("#")[0]
    raw = raw.rstrip(".")
    raw = re.sub(r"[^a-zA-Z0-9.\-]", "", raw)
    if DOMAIN_RE.match(raw):
        return raw
    return None


def safe_truncate(text: str, max_len: int = 300) -> str:
    if not text:
        return ""
    text = str(text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def safe_list_truncate(items: list, max_items: int = 300) -> list:
    if not items:
        return []
    return items[:max_items]
