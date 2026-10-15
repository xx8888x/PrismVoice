"""Mirror of Laravel's PerspectiveService::dimensions()/assess(); both read shared/perspective.json."""
import json
from functools import lru_cache

from .settings import SHARED_DIR


@lru_cache(maxsize=None)
def definition():
    with open(SHARED_DIR / 'perspective.json', encoding='utf-8') as handle:
        return json.load(handle)


def dimensions(question=None):
    spec = definition()
    return [{**d, 'question': d['question'].replace('{question}', question or spec['default_question'])} for d in spec['dimensions']]


def unscored():
    spec = definition()
    return {'score': None, 'confidence': 0, 'evidence': '', 'actor': '', 'reason': spec['unscored']['reason'], 'method': spec['method']}


def assess(title):
    # Headline tone is not the author's political position: position is never scored here.
    spec = definition()
    rules = spec['headline_rules']
    result = {d['key']: unscored() for d in spec['dimensions']}
    for key, words in rules['dimensions'].items():
        pos = [w for w in words['positive'] if w in title]
        neg = [w for w in words['negative'] if w in title]
        if bool(pos) != bool(neg):
            result[key] = {'score': 1 if pos else -1, 'confidence': rules['confidence'], 'evidence': (pos or neg)[0],
                           'actor': rules['actor'], 'reason': rules['reason'], 'method': spec['method']}
    return result


def assessments_for(event_dimensions, title):
    """Assessments keyed exactly by the event's dimension keys, so compare() always finds every key."""
    scored = assess(title)
    return {d['key']: scored.get(d['key'], unscored()) for d in event_dimensions}
