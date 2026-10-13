"""Serialize paid attempts and count unknown interrupted calls conservatively."""
from contextlib import contextmanager
from pathlib import Path
from .run_records import ROOT, read_json, exclusive_lock


def counts(root):
    totals = dict(total=0, development=0, retries=0)
    for path in Path(root).rglob('*.json'):
        r=read_json(path)
        if r.get('run_kind')=='live_api':
            cost=max(r.get('call_count') or 0, 1 if r.get('status')=='started' else 0)
            totals['total'] += cost
            if r.get('split') == 'dev':
                totals['development'] += cost
            if r.get('retry_of'):
                totals['retries'] += cost
    return totals


def consumed(root):
    return counts(root)['total']


@contextmanager
def reserve(root, limit, *, development=False, retry=False):
    with exclusive_lock(Path(root)/'.paid.lock'):
        totals=counts(root)
        authorization=read_json(ROOT/'config/authorization.json')
        if totals['total'] >= min(limit, authorization['total_request_limit']):
            raise ValueError('authorized_call_budget_exhausted')
        if development and totals['development'] >= authorization['development_limit']:
            raise ValueError('development_call_budget_exhausted')
        if retry and totals['retries'] >= authorization['retry_limit']:
            raise ValueError('retry_call_budget_exhausted')
        yield
