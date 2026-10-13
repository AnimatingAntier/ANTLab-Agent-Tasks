"""Serialize paid attempts and count unknown interrupted calls conservatively."""
from contextlib import contextmanager
from pathlib import Path
from .run_records import read_json, exclusive_lock


def consumed(root):
    count=0
    for path in Path(root).rglob('*.json'):
        r=read_json(path)
        if r.get('run_kind')=='live_api':
            count+=max(r.get('call_count') or 0, 1 if r.get('status')=='started' else 0)
    return count


@contextmanager
def reserve(root, limit):
    with exclusive_lock(Path(root)/'.paid.lock'):
        if consumed(root)>=limit:
            raise ValueError('authorized_call_budget_exhausted')
        yield
