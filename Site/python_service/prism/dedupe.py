"""Detect reprints: an article whose body is (nearly) the same text as an earlier one, e.g. UDN or Yahoo running a CNA wire story.

Two steps, because SimHash alone cannot separate them: on live data an unrelated pair sat at Hamming distance 15
while real Yahoo reprints of LTN (which append their own lines) sat at 11–13.
1. SimHash (stored per body, 64 bits) is a cheap filter the database can apply with BIT_COUNT.
2. The few candidates that pass are confirmed by exact overlap of 4-character shingles, plus a loose title check.
"""
import hashlib
import re

from . import cluster

SHINGLE = 4
MIN_CHARS = 200          # shorter bodies share too few shingles to judge; they are never marked
MAX_DISTANCE = 20        # SimHash filter: reprints measured 4–13, ~0.2% of unrelated pairs pass and get the exact check
MIN_JACCARD = 0.5        # reprints measured 0.77–0.97; two different stories on one event at most 0.52
MIN_CONTAINMENT = 0.8    # share of the shorter body found in the longer: reprints 0.89–1.00, other stories at most 0.70
MIN_SHARED_TITLE_BIGRAMS = 3  # reprint titles measured 7+ shared bigrams; guards against bodies mis-extracted from a shared block

_NON_WORD = re.compile(r'[^\w]+')


def shingles(body):
    text = _NON_WORD.sub('', body.lower())
    return {text[i:i + SHINGLE] for i in range(len(text) - SHINGLE + 1)}


def simhash(body):
    """64-bit SimHash of the body's shingles, or None when the body is too short to fingerprint."""
    if not body or len(body) < MIN_CHARS:
        return None
    weights = [0] * 64
    for gram in shingles(body):
        value = int.from_bytes(hashlib.blake2b(gram.encode('utf-8'), digest_size=8).digest(), 'big')
        for bit in range(64):
            weights[bit] += 1 if value >> bit & 1 else -1
    return sum(1 << bit for bit, weight in enumerate(weights) if weight > 0)


def overlap(body_a, body_b):
    """(Jaccard, containment of the smaller set) of the two bodies' shingle sets."""
    a, b = shingles(body_a), shingles(body_b)
    if not a or not b:
        return 0.0, 0.0
    shared = len(a & b)
    return shared / len(a | b), shared / min(len(a), len(b))


def best_original(title, body, candidates):
    """candidates: dicts with 'title' and 'body' (already past the SimHash filter). Returns (best reprint match or None, its Jaccard)."""
    best, best_jaccard = None, 0.0
    title_grams = cluster.bigrams(title)
    for candidate in candidates:
        # Identical bodies under unrelated titles mean extraction grabbed a shared block (seen on Yahoo: two pages, one
        # related-story text), not a reprint. Real reprints keep the headline or lightly edit it.
        if len(title_grams & cluster.bigrams(candidate['title'])) < MIN_SHARED_TITLE_BIGRAMS:
            continue
        jaccard, containment = overlap(body, candidate['body'])
        if jaccard >= MIN_JACCARD and containment >= MIN_CONTAINMENT and jaccard > best_jaccard:
            best, best_jaccard = candidate, jaccard
    return best, best_jaccard
