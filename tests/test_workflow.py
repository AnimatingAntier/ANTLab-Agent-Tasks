import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_runtime import required_module
from app.run_records import write_json
from app.runner import get_case


class WorkflowTests(unittest.TestCase):
    def test_cli_help_works_on_non_chinese_windows_encoding(self):
        import os, subprocess, sys
        from app.run_records import ROOT
        result=subprocess.run([sys.executable,'main.py','--help'],cwd=ROOT,
            env=dict(os.environ,PYTHONIOENCODING='cp1252'),capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))

    def test_runner_checks_shared_budget_before_any_live_request(self):
        from app.runner import execute
        from test_provider import CONFIG
        with patch('app.budget.reserve', side_effect=ValueError('budget')):
            with self.assertRaises(ValueError):
                execute('D01','E','baseline',CONFIG)

    def test_budget_counts_interrupted_and_failed_across_directories(self):
        m=required_module(self,'app.budget')
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for folder,status,count in [('dev','http_error',1),('main','started',0),('preflight','dry_run',0)]:
                write_json(root/folder/'one.json',dict(run_id=folder,status=status,run_kind='live_api' if folder!='preflight' else 'dry_run',call_count=count))
            self.assertEqual(m.consumed(root),2)
            with self.assertRaises(ValueError):
                with m.reserve(root,2):
                    self.fail('over-budget action must not run')

    def test_equivalence_saves_prediction_before_execution_without_api(self):
        m=required_module(self,'app.robustness')
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            from app.student import improve
            def check(question, passages):
                self.assertTrue((root/'prediction.json').exists())
                return improve(question,passages)
            with patch('app.robustness.improve',side_effect=check),patch('app.provider.call_model') as call:
                result=m.check_case('D01','both',17,root)
            call.assert_not_called()
            self.assertTrue(result['same_text_set'])
            self.assertTrue(result['same_content_order'])
            self.assertTrue(result['same_linked_prefix'])
            self.assertEqual(result['call_count'],0)

    def test_credentials_parser_only_loads_selected_key(self):
        m=required_module(self,'app.cli')
        import os
        with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,{},clear=True):
            p=Path(t)/'test.env';p.write_text('OTHER=do-not-load\nDEEPSEEK_API_KEY="fixture"\n',encoding='utf-8')
            m.load_credentials(p)
            self.assertEqual(os.environ['ASSESSMENT_API_KEY'],'fixture')
            self.assertNotIn('OTHER',os.environ)
