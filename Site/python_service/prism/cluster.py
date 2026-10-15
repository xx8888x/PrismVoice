"""Group articles about the same story by IDF-weighted character-bigram overlap of their titles.

Interim method until embeddings: deliberately conservative, because merging two different
stories produces a false comparison, while a missed merge only leaves a single-article event.
"""
import functools
import math
import re

import opencc

THRESHOLD = 0.30
MIN_SHARED_BIGRAMS = 3
WINDOW_DAYS = 3

# Short bracketed tags such as 【影】 or 《獨家》 say nothing about the story.
_TAG = re.compile(r'[【\[〔〈《(（][^】\]〕〉》)）]{0,6}[】\]〕〉》)）]')
_NON_WORD = re.compile(r'[^\w]+')
_S2TW = opencc.OpenCC('s2tw')
# Outlets mix 台 and 臺 (and s2tw turns 台灣 into 臺灣), so fold them to one form.
_VARIANTS = str.maketrans({'臺': '台'})


@functools.lru_cache(maxsize=4096)
def to_traditional(title):
    """Simplified → Taiwan traditional, so DW's simplified titles share bigrams with everyone else's.

    Applied to every title, traditional ones included: both sides of a comparison are converted the same way.
    """
    return _S2TW.convert(title).translate(_VARIANTS)


def bigrams(title):
    text = _NON_WORD.sub(' ', _TAG.sub(' ', to_traditional(title).lower()))
    grams = set()
    for chunk in text.split():
        if len(chunk) == 1:
            grams.add(chunk)
        grams.update(chunk[i:i + 2] for i in range(len(chunk) - 1))
    return grams


def best_event(title, candidates):
    """candidates: [(event_id, title)] of recent real articles. Returns (event_id or None, best score)."""
    target = bigrams(title)
    docs = [(event_id, bigrams(text)) for event_id, text in candidates]
    if not target or not docs:
        return None, 0.0
    frequency = {}
    for _, grams in docs:
        for gram in grams:
            frequency[gram] = frequency.get(gram, 0) + 1
    total = len(docs) + 1
    idf = lambda gram: math.log((total + 1) / (frequency.get(gram, 0) + 1)) + 1
    target_weight = sum(idf(g) for g in target)
    best_id, best_score = None, 0.0
    for event_id, grams in docs:
        shared = target & grams
        if len(shared) < MIN_SHARED_BIGRAMS:
            continue
        score = 2 * sum(idf(g) for g in shared) / (target_weight + sum(idf(g) for g in grams))
        if score > best_score:
            best_id, best_score = event_id, score
    return (best_id, best_score) if best_score >= THRESHOLD else (None, best_score)
