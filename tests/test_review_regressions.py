import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_provider import CONFIG
from app.run_records import read_json, write_json
from app.experiment import freeze_manifest, run_batch
from app.budget import reserve
from app.scoring import score_directory, score_record, summarize
from test_scoring import record


class ReviewRegressions(unittest.TestCase):
    def test_resume_rejects_existing_primary_from_another_frozen_version(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);cfg=root/'config.json';manifest=root/'manifest.json'
            write_json(cfg,CONFIG);m=freeze_manifest(cfg,manifest)
            r=dict(m['jobs'][0],run_id='old',experiment_id=m['experiment_id'],is_primary=True,
                run_kind='live_api',status='ok',source_hashes={'old':'version'},
                config_sha256=m['config_sha256'],data_sha256=m['data_sha256'],call_count=1)
            write_json(root/'runs/old.json',r)
            with patch('app.experiment.validate_config'),patch('app.experiment.execute', return_value=r) as call:
                with self.assertRaisesRegex(ValueError,'version'):
                    run_batch(manifest,cfg,root/'runs',paid=True,resume=True)
                call.assert_not_called()

    def test_score_rejects_mixed_versions_before_publishing(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);cfg=root/'config.json';manifest=root/'manifest.json'
            write_json(cfg,CONFIG);m=freeze_manifest(cfg,manifest)
            r=record();r.update(experiment_id=m['experiment_id'],source_hashes={'old':'code'})
            write_json(root/'runs/old.json',r);write_json(root/'labels.json',{})
            with self.assertRaisesRegex(ValueError,'version'):
                score_directory(root/'runs',manifest,root/'labels.json',root/'reviews.jsonl',root/'results')
            self.assertFalse((root/'results/results.csv').exists())

    def test_development_cap_reserves_main_allowance(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for i in range(16):
                write_json(root/f'{i}.json',dict(run_kind='live_api',split='dev',status='http_error',call_count=1))
            with self.assertRaisesRegex(ValueError,'development'):
                with reserve(root,64,development=True):
                    self.fail('seventeenth development request allowed')

    def test_retry_cap_counts_unknown_interruption(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for i in range(8):
                write_json(root/f'{i}.json',dict(run_kind='live_api',retry_of='first',status='started',call_count=0))
            with self.assertRaisesRegex(ValueError,'retry'):
                with reserve(root,64,retry=True):
                    self.fail('ninth retry allowed')

    def test_unreviewed_semantics_keep_summary_provisional(self):
        r=record();row=score_record(r,{'answer_type':'percent','expected_answer':'80%'})
        manifest={'experiment_id':'main','jobs':[dict(job_id='T01:R0:baseline',case_id='T01',condition='R0',variant='baseline')]}
        self.assertTrue(summarize([row],manifest)['conditions']['R0']['provisional'])
