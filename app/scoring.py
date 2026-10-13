"""Offline scoring: answer correctness and evidence support remain independent."""
import csv
import json
import re
import statistics
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from .run_records import read_json, write_json


def answer_matches(answer, label):
    def clean(value):
        return unicodedata.normalize('NFKC', str(value)).strip()
    actual, expected = clean(answer), clean(label['expected_answer'])
    if label['answer_type'] in ('number', 'percent'):
        if label['answer_type'] == 'percent':
            if not actual.endswith('%') or not expected.endswith('%'):
                return False
            actual, expected = actual[:-1].strip(), expected[:-1].strip()
        if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)', actual):
            return False
        try:
            return Decimal(actual) == Decimal(expected)
        except InvalidOperation:
            return False
    return actual in [expected] + [clean(x) for x in label.get('aliases', [])]


def score_record(record, label=None, review=None):
    review = review or {}
    if review and not review.get('reason'):
        raise ValueError('review_requires_reason')
    parsed = record.get('parsed_output') or {}
    technical = record.get('api_status') == 'ok' and record.get('format_status') == 'valid'
    correct = answer_matches(parsed.get('answer', ''), label) if technical and label else (None if technical else False)
    if technical and isinstance(review.get('task_correct'), bool):
        correct = review['task_correct']
    semantic = review.get('semantic_support', 'not_checked')
    if semantic not in ('supported', 'contradicted', 'insufficient', 'not_checked'):
        raise ValueError('invalid_semantic_support')
    keys = ('run_id', 'case_id', 'condition', 'variant', 'experiment_id', 'is_primary',
            'attempt_index', 'retry_of', 'run_kind', 'api_status', 'status', 'format_status',
            'locator_status', 'call_count', 'elapsed_seconds', 'usage', 'usage_source')
    row = {key: record.get(key) for key in keys}
    row.update(job_id=record.get('job_id') or ':'.join(str(record.get(k)) for k in ('case_id','condition','variant')),
               model=(record.get('config') or {}).get('model'), content_raw=parsed.get('content_raw'),
               answer=parsed.get('answer'), citations=parsed.get('citations', []),
               task_correct=correct, semantic_support=semantic,
               evidence_coverage=review.get('evidence_coverage', 'not_checked'),
               abstention_reasonable=review.get('abstention_reasonable'),
               judgment_source=review.get('judgment_source', 'unverified'),
               reason=review.get('reason', (label or {}).get('reason', '未建立参考判断')),
               technical_ok=technical, review_pending=correct is None or semantic == 'not_checked',
               label_source=(label or {}).get('provenance'))
    return row


def summarize(rows, manifest):
    eligible = [r for r in rows if r.get('experiment_id') == manifest['experiment_id']
                and r.get('run_kind') == 'live_api']
    jobs = {j['job_id']: j for j in manifest['jobs']}
    primary = {}
    for row in eligible:
        if not row.get('is_primary'):
            continue
        job = row['job_id']
        if job not in jobs or job in primary:
            raise ValueError('unexpected_or_duplicate_primary_job')
        primary[job] = row
    groups = {}
    for job_id, job in jobs.items():
        name = job['condition'] if job['variant'] == 'baseline' else job['condition'] + '_improved'
        groups.setdefault(name, []).append(primary.get(job_id))
    conditions = {}
    for name, entries in groups.items():
        observed = [r for r in entries if r is not None]
        correct = sum(r['task_correct'] is True for r in observed)
        pending = sum(r is None or r['task_correct'] is None for r in entries)
        interrupted = sum(r.get('status') == 'started' for r in observed)
        times = [r['elapsed_seconds'] for r in observed if isinstance(r.get('elapsed_seconds'), (int, float))]
        good = [r for r in observed if r['technical_ok']]
        success_times = [r['elapsed_seconds'] for r in good if isinstance(r.get('elapsed_seconds'), (int,float))]
        conditions[name] = dict(
            denominator=len(entries), observed=len(observed), correct=correct,
            accuracy=correct / len(entries), pending=pending, provisional=bool(pending or interrupted),
            technical_failures=sum(not r['technical_ok'] and r.get('status') != 'started' for r in observed),
            interrupted=interrupted, technical_successes=len(good),
            accuracy_after_technical_success=(sum(r['task_correct'] is True for r in good)/len(good) if good else None),
            format_valid=sum(r.get('format_status') == 'valid' for r in observed),
            citation_membership_valid=sum(r.get('locator_status') == 'valid' for r in observed),
            semantic_supported=sum(r['semantic_support'] == 'supported' for r in observed),
            semantic_pending=sum(r['semantic_support'] == 'not_checked' for r in observed),
            non_abstaining=sum(r.get('answer') not in (None, '', '证据不足') for r in observed),
            median_elapsed_seconds=statistics.median(times) if times else None,
            median_success_elapsed_seconds=statistics.median(success_times) if success_times else None)
    pairs = []
    for cid in sorted({j['case_id'] for j in jobs.values()}):
        b, i = primary.get(cid + ':R0:baseline'), primary.get(cid + ':R0:improved')
        bv, iv = (b or {}).get('task_correct'), (i or {}).get('task_correct')
        outcome = 'pending' if bv is None or iv is None else ('unchanged' if bv == iv else ('improved' if iv else 'worsened'))
        pairs.append(dict(case_id=cid, baseline=bv, improved=iv, outcome=outcome))
    return dict(experiment_id=manifest['experiment_id'], conditions=conditions, pairs=pairs,
                missing_jobs=sorted(set(jobs)-set(primary)),
                retry_count=sum(bool(r.get('retry_of')) for r in eligible),
                total_calls=sum(r.get('call_count') or 0 for r in eligible))


def load_reviews(path):
    path = Path(path)
    reviews = {}
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if line.strip():
                row = json.loads(line)
                reviews[row['run_id']] = row
    return reviews


def write_csv(path, rows, fields=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0]) if rows else ['run_id'])
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list,dict)) else v
                             for k,v in row.items()})


def score_directory(runs, manifest_path, labels_path, reviews_path, output_dir):
    manifest, labels = read_json(manifest_path), read_json(labels_path)
    reviews = load_reviews(reviews_path)
    rows = []
    for path in sorted(Path(runs).glob('*.json')):
        record = read_json(path)
        row = score_record(record, labels.get(record['case_id']), reviews.get(record['run_id']))
        row['record_path'] = str(path)
        rows.append(row)
    summary = summarize(rows, manifest)
    out = Path(output_dir)
    write_csv(out / 'results.csv', rows)
    write_json(out / 'basic-summary.json', summary)
    write_csv(out / 'basic-pairs.csv', summary['pairs'])
    return summary
