"""Canonical case preparation and append-only attempts, adapted from the starter."""
import copy
import datetime
import time
import uuid
from pathlib import Path
from . import student
from .provider import call_model, validate_config
from .output_checks import parse_output, check_citations
from .run_records import ROOT, read_json, digest, public_config, source_hashes, start_record, finish_record

BASE = ROOT


def cases():
    return read_json(ROOT / 'data/cases.json')


def get_case(cid):
    return next((c for c in cases() if c['id'] == cid), None)


def load_config(path):
    config = read_json(path)
    validate_config(config)
    public_config(config)
    return config


def prepare(cid, condition, variant):
    case = get_case(cid)
    if case is None or condition not in case['conditions']:
        raise ValueError('invalid_case_or_condition')
    if variant not in ('baseline', 'improved'):
        raise ValueError('invalid_variant')
    by_id = {p['id']: p for p in case['passages']}
    original = [copy.deepcopy(by_id[i]) for i in case['conditions'][condition]]
    selected = copy.deepcopy(original)
    if variant == 'improved':
        selected = student.improve(case['question'], selected)
    allowed = {p['id']: p for p in original}
    if (not isinstance(selected, list)
            or any(not isinstance(p, dict) or p.get('id') not in allowed or p != allowed[p['id']] for p in selected)
            or len({p['id'] for p in selected}) != len(selected)):
        raise ValueError('improvement_changed_or_exceeded_visible_material')
    messages = student.prepare_messages(case['question'], copy.deepcopy(selected))
    if (not isinstance(messages, list) or not messages
            or any(not isinstance(m, dict) or set(m) != {'role', 'content'}
                   or m['role'] not in ('system', 'user', 'assistant') or not isinstance(m['content'], str) for m in messages)):
        raise ValueError('invalid_messages')
    return case, original, selected, messages


def preview(cid, condition, variant, config):
    c, original, selected, messages = prepare(cid, condition, variant)
    return dict(case_id=cid, condition=condition, variant=variant, question=c['question'],
                visible_passages=original, selected_passages=selected, messages=messages,
                input_sha256=digest(messages), config=public_config(config),
                public_config_sha256=digest(public_config(config)))


def execute(cid, condition, variant, config, *, mock=False, dry=False, outdir=None, metadata=None):
    if mock or dry:
        return _execute(cid, condition, variant, config, mock=mock, dry=dry, outdir=outdir, metadata=metadata)
    from .budget import reserve
    with reserve(ROOT / 'runs', 64):
        return _execute(cid, condition, variant, config, outdir=outdir, metadata=metadata)


def _execute(cid, condition, variant, config, *, mock=False, dry=False, outdir=None, metadata=None):
    metadata = metadata or {}
    allowed_meta = {'experiment_id', 'job_id', 'purpose', 'attempt_index', 'retry_of', 'is_primary', 'preview_verified'}
    if set(metadata) - allowed_meta:
        raise ValueError('invalid_record_metadata')
    case = get_case(cid)
    record = dict(schema_version=2, run_id=str(uuid.uuid4()),
                  utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  case_id=cid, split=case['split'] if case else None, condition=condition, variant=variant,
                  experiment_id=None, purpose='dev', attempt_index=1, retry_of=None, is_primary=False,
                  status='started', mode='dry' if dry else ('mock' if mock else 'paid'),
                  run_kind='dry_run' if dry else ('offline_replay' if mock else 'live_api'),
                  config=public_config(config), config_sha256=digest(public_config(config)),
                  data_sha256=digest((ROOT / 'data/cases.json').read_bytes()),
                  dataset_version=read_json(ROOT / 'data/manifest.json')['version'],
                  source_hashes=source_hashes(), question=case['question'] if case else None,
                  original_passages=[], selected_passages=[], messages=[], call_count=0,
                  support_status='not_checked', judgment_source='unverified',
                  response=None, response_raw=None, usage=None, usage_source='unavailable',
                  elapsed_seconds=None, preparation_ms=None, api_status='not_called', **{})
    record.update(metadata)
    destination = Path(outdir) if outdir else ROOT / 'runs' / ('dev' if record['split'] == 'dev' else 'exploratory')
    path = start_record(record, destination)
    t0 = time.perf_counter()
    try:
        c, original, selected, messages = prepare(cid, condition, variant)
        record.update(original_passages=original, selected_passages=selected, messages=messages,
                      original_passage_ids=[p['id'] for p in original], selected_passage_ids=[p['id'] for p in selected],
                      input_sha256=digest(messages), input_characters=sum(len(m['content']) for m in messages),
                      preparation_ms=(time.perf_counter() - t0) * 1000)
        # Persist the actual messages BEFORE the external side effect.
        from .run_records import write_json
        write_json(path, record)
    except Exception as exc:
        return finish_record(path, dict(status='preparation_error', api_status='preparation_error',
            error_code=type(exc).__name__, format_status='absent', locator_status='absent',
            preparation_ms=(time.perf_counter() - t0) * 1000))
    if dry:
        result = dict(status='dry_run', call_count=0)
    else:
        try:
            result = call_model(messages, config, mock=mock)
        except Exception as exc:
            result = dict(status='internal_error', error_code=type(exc).__name__, call_count=0 if mock else 1)
    parsed = parse_output(result.get('response'))
    locators = check_citations(parsed['citations'], selected)
    updates = {**result, 'api_status': result['status'], 'parsed_output': parsed,
               'format_status': parsed['format_status'], **locators,
               'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    return finish_record(path, updates)
