"""Frozen 40-job protocol. Every attempt is retained; no implicit retry."""
import datetime
import random
import re
import subprocess
from pathlib import Path
from .runner import cases, load_config, execute, preview
from .provider import validate_config
from .run_records import ROOT, read_json, write_json, digest, public_config, source_hashes, exclusive_lock


def build_jobs(dataset, seed=20261006):
    evaluation = [c for c in dataset if c['split'] != 'dev']
    if len(evaluation) != 8:
        raise ValueError('expected_eight_evaluation_cases')
    jobs = []
    for c in evaluation:
        for condition, variant in [('R0','baseline'),('R1','baseline'),('R2','baseline'),('K','baseline'),('R0','improved')]:
            jobs.append(dict(job_id=':'.join((c['id'],condition,variant)),case_id=c['id'],condition=condition,variant=variant))
    random.Random(seed).shuffle(jobs)
    return jobs


def freeze_manifest(config_path, output_path, max_calls=48, experiment_id='basic-main-v1'):
    if not re.fullmatch(r'[A-Za-z0-9_-]+',experiment_id) or max_calls < 40 or max_calls > 64:
        raise ValueError('invalid_experiment_or_budget')
    output_path = Path(output_path)
    config = load_config(config_path)
    manifest = dict(schema_version=1, experiment_id=experiment_id,
        frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        source_hashes=source_hashes(), data_sha256=digest((ROOT/'data/cases.json').read_bytes()),
        config=public_config(config), config_sha256=digest(public_config(config)),
        rubric_sha256=digest((ROOT/'results/scoring/rubric.md').read_bytes()),
        jobs=build_jobs(cases()), seed=20261006, max_calls=max_calls,
        primary_policy='first_attempt_including_failure', development_exposure='D01-D04; evaluation public; no evaluation answer tuning before this freeze',
        stop_policy='budget, source/config/rubric drift, HTTP 401/402/403/429, config errors; no automatic retries')
    output_path.parent.mkdir(parents=True,exist_ok=True)
    with exclusive_lock(str(output_path)+'.lock'):
        if output_path.exists():
            raise ValueError('manifest_already_exists')
        write_json(output_path,manifest)
    return manifest


def verify(manifest, config):
    if manifest['source_hashes'] != source_hashes():
        raise ValueError('frozen_source_drift')
    if manifest['config_sha256'] != digest(public_config(config)):
        raise ValueError('frozen_config_drift')
    if manifest['data_sha256'] != digest((ROOT/'data/cases.json').read_bytes()):
        raise ValueError('frozen_data_drift')
    if manifest['rubric_sha256'] != digest((ROOT/'results/scoring/rubric.md').read_bytes()):
        raise ValueError('frozen_rubric_drift')
    if manifest['jobs'] != build_jobs(cases(),manifest['seed']):
        raise ValueError('frozen_jobs_drift')


def records(runs_dir):
    return [read_json(p) for p in sorted(Path(runs_dir).glob('*.json'))]


def audit_manifest(manifest_path, runs_dir):
    m = read_json(manifest_path)
    rows = [r for r in records(runs_dir) if r.get('experiment_id') == m['experiment_id'] and r.get('run_kind') == 'live_api']
    expected = {j['job_id'] for j in m['jobs']}
    primary = [r for r in rows if r.get('is_primary')]
    groups = {}
    for r in primary:
        groups.setdefault(r.get('job_id'),[]).append(r)
    missing = sorted(expected-set(groups))
    drift = []
    for r in rows:
        if r.get('source_hashes') != m['source_hashes'] or r.get('config_sha256') != m['config_sha256'] or r.get('data_sha256') != m['data_sha256']:
            drift.append(r['run_id'])
    return dict(experiment_id=m['experiment_id'],expected=len(expected),
        completed=sum(r.get('status')!='started' for r in primary),
        failed=sum(r.get('status')!='started' and (r.get('api_status')!='ok' or r.get('format_status')!='valid') for r in primary),
        pending=len(missing),missing_jobs=missing,interrupted=sum(r.get('status')=='started' for r in primary),
        retries=sum(bool(r.get('retry_of')) for r in rows),
        duplicate_jobs=sorted(k for k,v in groups.items() if len(v)>1),
        unexpected_jobs=sorted(set(groups)-expected),version_mismatch_runs=drift,
        consumed_calls=sum(max(r.get('call_count') or 0,1 if r.get('status')=='started' else 0) for r in rows))


def run_batch(manifest_path, config_path, runs_dir, *, paid=False, dry=False, resume=False, retry_of=None):
    if paid == dry:
        raise ValueError('choose_paid_or_dry_run')
    m, cfg = read_json(manifest_path), load_config(config_path)
    verify(m,cfg)
    runs_dir=Path(runs_dir)
    if dry:
        destination=runs_dir/'preflight'
        for job in m['jobs']:
            execute(job['case_id'],job['condition'],job['variant'],cfg,dry=True,outdir=destination,
                metadata=dict(experiment_id=m['experiment_id'],job_id=job['job_id'],purpose='preflight'))
        return audit_manifest(manifest_path,runs_dir)
    validate_config(cfg,require_key=True)
    with exclusive_lock(runs_dir/'.batch.lock'):
        audit=audit_manifest(manifest_path,runs_dir)
        if audit['version_mismatch_runs']:
            raise ValueError('existing_record_version_mismatch_use_new_experiment')
        if audit['duplicate_jobs'] or audit['unexpected_jobs']:
            raise ValueError('invalid_existing_batch')
        rows=[r for r in records(runs_dir) if r.get('experiment_id')==m['experiment_id'] and r.get('run_kind')=='live_api']
        seen={r['job_id'] for r in rows if r.get('is_primary')}
        if rows and not resume and not retry_of:
            raise ValueError('existing_batch_requires_resume')
        retry=None
        if retry_of:
            matches=[r for r in rows if r['run_id']==retry_of]
            if len(matches)!=1:
                raise ValueError('retry_origin_not_found')
            retry=matches[0]
        jobs=[j for j in m['jobs'] if j['job_id']==retry['job_id']] if retry else [j for j in m['jobs'] if j['job_id'] not in seen]
        consumed=audit['consumed_calls']
        for job in jobs:
            if consumed >= m['max_calls']:
                break
            verify(m,cfg)
            count=sum(r['job_id']==job['job_id'] for r in rows)+1
            r=execute(job['case_id'],job['condition'],job['variant'],cfg,outdir=runs_dir,
                metadata=dict(experiment_id=m['experiment_id'],job_id=job['job_id'],purpose='main',
                    attempt_index=count,retry_of=retry_of,is_primary=not bool(retry_of)))
            consumed+=r.get('call_count',0)
            rows.append(r)
            print(job['job_id']+' '+r['status']+' '+r['run_id'],flush=True)
            if r.get('http_status') in (401,402,403,429) or r['status'] in ('config_error','internal_error'):
                break
        return audit_manifest(manifest_path,runs_dir)
