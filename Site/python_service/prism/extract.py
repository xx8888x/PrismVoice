"""Fetch an article page and pull out its body text."""
import requests
from bs4 import BeautifulSoup

from .settings import HTTP_TIMEOUT, USER_AGENT

MIN_BODY_CHARS = 80
NOISE_TAGS = ['script', 'style', 'noscript', 'figure', 'figcaption', 'aside', 'iframe', 'form', 'button']


def _paragraphs(container):
    return [t for t in (p.get_text(' ', strip=True) for p in container.find_all('p')) if t]


def _own_text_length(paragraph):
    # Link text is excluded: related-story lists are paragraphs full of links, real body copy is not.
    total = len(paragraph.get_text(strip=True))
    linked = sum(len(a.get_text(strip=True)) for a in paragraph.find_all('a'))
    return total - linked


def extract_text(html, selector=None):
    """Return (body, extractor). Uses the source's CSS selector, else the parent holding the most non-link paragraph text."""
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(NOISE_TAGS):
        tag.decompose()
    if selector:
        container = soup.select_one(selector)
        if container is not None:
            return '\n'.join(_paragraphs(container)), f'selector:{selector}'
    totals = {}
    for paragraph in soup.find_all('p'):
        length = _own_text_length(paragraph)
        if paragraph.parent is not None and length >= 15:
            score, _ = totals.get(id(paragraph.parent), (0, None))
            totals[id(paragraph.parent)] = (score + length, paragraph.parent)
    if not totals:
        return '', 'density'
    _, container = max(totals.values(), key=lambda item: item[0])
    return '\n'.join(_paragraphs(container)), 'density'


def fetch_article(url, selector=None, session=None):
    """Always returns a dict ready for article_contents; never raises for network or parse problems."""
    http = session or requests
    try:
        response = http.get(url, headers={'User-Agent': USER_AGENT}, timeout=HTTP_TIMEOUT)
    except requests.RequestException as error:
        return {'status': 'failed', 'body': None, 'extractor': None, 'http_status': None, 'error': str(error)[:500]}
    if response.status_code >= 400:
        return {'status': 'failed', 'body': None, 'extractor': None, 'http_status': response.status_code, 'error': f'HTTP {response.status_code}'}
    try:
        # Raw bytes let BeautifulSoup honour the page's <meta charset> (many sites omit it from headers).
        body, extractor = extract_text(response.content, selector)
    except Exception as error:  # malformed markup must not stop the run
        return {'status': 'failed', 'body': None, 'extractor': None, 'http_status': response.status_code, 'error': f'parse: {error}'[:500]}
    status = 'ok' if len(body) >= MIN_BODY_CHARS else 'empty'
    return {'status': status, 'body': body or None, 'extractor': extractor, 'http_status': response.status_code, 'error': None}
