"""Deterministic, label-free reordering. Nothing is removed or rewritten."""
import re

VERSION = re.compile(r'(?<![A-Za-z0-9])R\d+(?![A-Za-z0-9])')
MONTH = re.compile(r'\d{4}-\d{2}(?!\d)')
IDENTIFIER = re.compile(r'(?<![A-Za-z0-9_])[A-Za-z]+[A-Za-z0-9_-]*\d[A-Za-z0-9_-]*(?![A-Za-z0-9_])')


def order_passages(question: str, passages: list[dict]) -> list[dict]:
    project = re.search(r'([\u4e00-\u9fffA-Za-z0-9_-]+项目)', question)
    project = re.sub(r'^(?:请问|请核对|核对|关于|查询|按)', '', project[1]) if project else ''
    versions, months = set(VERSION.findall(question)), set(MONTH.findall(question))
    facets = ([project] if project else []) + sorted(versions | months)
    if not facets or not passages:
        return list(passages)
    grams = {question[i:i+2] for i in range(len(question)-1)}

    def matches(token, body):
        if token in versions:
            return token in VERSION.findall(body)
        return token in body

    def score(p):
        return (sum(matches(t, p['text']) for t in facets),
                sum(g in p['text'] for g in grams))

    ranked = sorted(passages, key=lambda p: (-score(p)[0], -score(p)[1], p['text']))
    anchor = ranked[0]
    if score(anchor)[0] != len(facets):
        return list(passages)
    if len(ranked) > 1 and score(ranked[1]) == score(anchor):
        return list(passages)
    identifiers = set(IDENTIFIER.findall(anchor['text'])) - set(VERSION.findall(anchor['text']))

    def linked(p):
        pv, pm = set(VERSION.findall(p['text'])), set(MONTH.findall(p['text']))
        conflict = (bool(versions and pv and not versions & pv)
                    or bool(months and pm and not months & pm))
        return not conflict and bool(identifiers & set(IDENTIFIER.findall(p['text'])))

    return [anchor] + [p for p in ranked[1:] if linked(p)] + [p for p in ranked[1:] if not linked(p)]
