"""Small persistence boundary shared by execution, audit and scoring."""
import copy
import hashlib
import json
import os
import re
import uuid
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(value):
    raw = value if isinstance(value, bytes) else json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def public_config(config):
    result = copy.deepcopy({k: config[k] for k in ('provider', 'model', 'parameters', 'timeout_seconds') if k in config})
    def check(value):
        if isinstance(value, dict):
            for k, v in value.items():
                if re.fullmatch(r'(?i)(api[_-]?key|authorization|endpoint|password|secret|access_token|token)', k):
                    raise ValueError('sensitive_config_field')
                check(v)
        elif isinstance(value, list):
            for v in value:
                check(v)
    check(result)
    digest(result)  # Disallow NaN/Infinity in serialized settings.
    return result


def source_hashes():
    names = ('student', 'ordering', 'output_checks', 'run_records', 'runner', 'provider',
             'experiment', 'scoring', 'server', 'cli', 'budget', 'lexical', '__init__')
    paths = [ROOT / 'app' / (n + '.py') for n in names] + [ROOT / 'main.py']
    return {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in paths if p.exists()}


@contextmanager
def exclusive_lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        f.write(str(os.getpid()))
    try:
        yield
    finally:
        path.unlink(missing_ok=True)


def start_record(record: dict, outdir: Path) -> Path:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if not re.fullmatch(r'[A-Za-z0-9_-]+', record['run_id']):
        raise ValueError('invalid_run_id')
    path = outdir / (record['run_id'] + '.json')
    with path.open('x', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2, allow_nan=False)
    return path


def finish_record(path: Path, updates: dict) -> dict:
    with exclusive_lock(Path(str(path) + '.lock')):
        original = read_json(path)
        if original['status'] != 'started':
            raise ValueError('terminal_record_is_immutable')
        if 'run_id' in updates and updates['run_id'] != original['run_id']:
            raise ValueError('immutable_run_id')
        original.update(updates)
        write_json(path, original)
        return original
