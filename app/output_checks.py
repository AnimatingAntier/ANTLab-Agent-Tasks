"""Validate syntax and provenance, never infer semantic support."""
import json


def parse_output(response: dict | str | None) -> dict:
    result = dict(content_raw=None, answer=None, citations=[], format_status='absent', error_code=None)
    try:
        content = response['choices'][0]['message']['content']
    except (TypeError, KeyError, IndexError):
        return result
    result['content_raw'] = content
    if not isinstance(content, str) or not content.strip():
        return result
    def unique_object(pairs):
        d = {}
        for key, value in pairs:
            if key in d:
                raise ValueError('duplicate key')
            d[key] = value
        return d
    try:
        obj = json.loads(content, object_pairs_hook=unique_object,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))
        if (not isinstance(obj, dict) or set(obj) != {'answer', 'citations'}
                or not isinstance(obj['answer'], str) or not obj['answer'].strip()
                or not isinstance(obj['citations'], list)
                or any(not isinstance(c, str) or not c for c in obj['citations'])):
            raise ValueError('schema')
        result.update(answer=obj['answer'], citations=obj['citations'], format_status='valid')
    except (ValueError, TypeError):
        result.update(format_status='invalid', error_code='invalid_model_json')
    return result


def check_citations(citations: list[str], passages: list[dict]) -> dict:
    known = {p['id'] for p in passages}
    unknown = sorted(set(citations) - known)
    return {'locator_status': 'absent' if not citations else ('invalid' if unknown else 'valid'),
            'unknown_citations': unknown}
