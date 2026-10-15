"""Turn a source's RSS bytes into clean, validated article candidates."""
import calendar
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import feedparser

TRACKING_PREFIXES = ('utm_', 'at_')
TRACKING_KEYS = {'maca', 'fbclid', 'gclid'}


def normalize_url(url):
    """Drop fragments and tracking parameters so one story always hashes the same."""
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith(TRACKING_PREFIXES) and k.lower() not in TRACKING_KEYS]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, urlencode(query), ''))


def resolve_link(link, source):
    """Apply the source's rewrite, make the link absolute and normalised, and return it only if it matches link_pattern."""
    if not link:
        return None
    rewrite = source.get('link_rewrite')
    if rewrite:
        link = re.sub(rewrite[0], rewrite[1], link)
    url = normalize_url(urljoin(source['homepage_url'] + '/', link))
    return url if re.match(source['link_pattern'], url) else None


def to_utc_naive(value):
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value


def parse_published(entry):
    """UTC naive datetime (the app stores UTC), or None when the feed gives no usable date."""
    for key in ('published_parsed', 'updated_parsed'):
        parsed = entry.get(key)
        if parsed:
            return datetime.fromtimestamp(calendar.timegm(parsed), timezone.utc).replace(tzinfo=None)
    for key in ('published', 'updated', 'dc_date'):
        raw = entry.get(key)
        if not raw:
            continue
        # Some feeds emit "Thu,15 Oct 2026 14:45:00  +0800", which feedparser rejects.
        cleaned = re.sub(r'\s+', ' ', re.sub(r'^(\w{3}),(?=\S)', r'\1, ', raw.strip()))
        try:
            return to_utc_naive(parsedate_to_datetime(cleaned))
        except (TypeError, ValueError):
            pass
        try:
            return to_utc_naive(datetime.fromisoformat(cleaned))
        except ValueError:
            pass
    return None


def parse_entries(content, source):
    feed = feedparser.parse(content)
    if not feed.entries and feed.get('bozo'):
        raise ValueError(f"RSS 無法解析：{feed.get('bozo_exception')}")
    rows, seen = [], set()
    for entry in feed.entries:
        url = resolve_link(entry.get('link'), source)
        title = re.sub(r'\s+', ' ', entry.get('title') or '').strip()
        if not url or not title or len(title) > 1000 or url in seen:
            continue
        seen.add(url)
        tags = entry.get('tags') or []
        rows.append({
            'url': url,
            'title': title,
            'published_at': parse_published(entry),
            'author': (entry.get('author') or '')[:255] or None,
            'category': ((tags[0].get('term') if tags else '') or '')[:255] or None,
        })
    return rows
