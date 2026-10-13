import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_runtime import required_module
from test_provider import CONFIG
from app.runner import cases
from app.run_records import write_json


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        budget = patch('app.budget.counts', return_value={'total':0,'development':0,'retries':0})
        budget.start()
        self.addCleanup(budget.stop)
        self.m = required_module(self, 'app.experiment')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root/'config.json'
        write_json(self.config, CONFIG)
        self.manifest = self.root/'manifest.json'
        self.m.freeze_manifest(self.config, self.manifest, max_calls=48)

    def test_plan_is_40_unique_eval_only_and_reproducible(self):
        jobs = self.m.build_jobs(cases(), 20261006)
        self.assertEqual(len(jobs),40)
        self.assertEqual(len({j['job_id'] for j in jobs}),40)
        self.assertTrue(all(j['case_id'].startswith('T') and j['condition']!='E' for j in jobs))
        self.assertEqual(sum(j['variant']=='improved' for j in jobs),8)
        self.assertEqual(jobs,self.m.build_jobs(cases(),20261006))

    def fake(self, *args, **kw):
        from app.runner import execute
        response = {'status':'ok','call_count':1,'response':{'choices':[{'message':{'content':'{"answer":"test","citations":[]}'}}]}}
        with patch('app.runner.call_model', return_value=response):
            return execute(*args, **kw)

    def test_full_run_resume_never_repeats_and_retry_is_separate(self):
        dest=self.root/'runs'
        with patch('app.experiment.validate_config'), patch('app.experiment.execute',side_effect=self.fake) as call:
            self.m.run_batch(self.manifest,self.config,dest,paid=True)
            self.assertEqual(call.call_count,40)
            self.m.run_batch(self.manifest,self.config,dest,paid=True,resume=True)
            self.assertEqual(call.call_count,40)
            first=next(dest.glob('*.json')).stem
            self.m.run_batch(self.manifest,self.config,dest,paid=True,retry_of=first)
            self.assertEqual(call.call_count,41)
        audit=self.m.audit_manifest(self.manifest,dest)
        self.assertEqual(audit['completed'],40)
        self.assertEqual(audit['retries'],1)
        self.assertEqual(audit['pending'],0)

    def test_started_attempt_blocks_automatic_resend(self):
        from app.run_records import read_json
        manifest=read_json(self.manifest)
        job=manifest['jobs'][0]
        write_json(self.root/'runs'/'interrupted.json',dict(job,run_id='interrupted',experiment_id='basic-main-v1',
            status='started',run_kind='live_api',is_primary=True,call_count=0,
            source_hashes=manifest['source_hashes'],config_sha256=manifest['config_sha256'],data_sha256=manifest['data_sha256']))
        with patch('app.experiment.validate_config'), patch('app.experiment.execute',side_effect=self.fake) as call:
            self.m.run_batch(self.manifest,self.config,self.root/'runs',paid=True,resume=True)
        self.assertEqual(call.call_count,39)
        self.assertEqual(self.m.audit_manifest(self.manifest,self.root/'runs')['interrupted'],1)

    def test_config_and_code_drift_rejected_before_call(self):
        from app.run_records import read_json
        cfg=dict(CONFIG,model='other');write_json(self.config,cfg)
        with patch('app.experiment.execute') as call:
            with self.assertRaises(ValueError):
                self.m.run_batch(self.manifest,self.config,self.root/'runs',paid=True)
        call.assert_not_called()
        write_json(self.config,CONFIG)
        with patch('app.experiment.source_hashes',return_value={'drift':'yes'}):
            with self.assertRaises(ValueError):
                self.m.run_batch(self.manifest,self.config,self.root/'runs',paid=True)

    def test_dry_does_not_occupy_primary_jobs_and_duplicate_rejected(self):
        self.m.run_batch(self.manifest,self.config,self.root/'runs',dry=True)
        audit=self.m.audit_manifest(self.manifest,self.root/'runs')
        self.assertEqual(audit['pending'],40)
        self.assertEqual(audit['completed'],0)
        from app.run_records import read_json
        job=read_json(self.manifest)['jobs'][0]
        for name in ('one','two'):
            write_json(self.root/'dup'/f'{name}.json',dict(job,run_id=name,experiment_id='basic-main-v1',
                status='ok',run_kind='live_api',is_primary=True))
        self.assertTrue(self.m.audit_manifest(self.manifest,self.root/'dup')['duplicate_jobs'])
        with patch('app.experiment.validate_config'),patch('app.experiment.execute') as call:
            with self.assertRaises(ValueError):
                self.m.run_batch(self.manifest,self.config,self.root/'dup',paid=True,resume=True)
        call.assert_not_called()

    def test_auth_failure_stops_and_budget_counts_attempts(self):
        def failed(*a,**kw):
            from app.runner import execute
            with patch('app.runner.call_model',return_value={'status':'http_error','http_status':401,'call_count':1}):
                return execute(*a,**kw)
        with patch('app.experiment.validate_config'),patch('app.experiment.execute',side_effect=failed) as call:
            result=self.m.run_batch(self.manifest,self.config,self.root/'runs',paid=True)
        self.assertEqual(call.call_count,1)
        self.assertEqual(result['pending'],39)
