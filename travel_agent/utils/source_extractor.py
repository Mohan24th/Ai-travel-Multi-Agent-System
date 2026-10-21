import re
from urllib.parse import urlparse


def extract_urls(text: str) -> list[str]:
    """Extract unique HTTP(S) URLs from trusted tool output."""
    if not text:
        return []

    candidates = re.findall(r"https?://[^\s<>\"']+", text)
    urls = []

    for candidate in candidates:
        url = candidate.rstrip(".,;:)]}")
        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            continue

        if not parsed.netloc or not parsed.hostname:
            continue

        if url not in urls:
            urls.append(url)

    return urls
