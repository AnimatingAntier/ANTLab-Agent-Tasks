import json
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from unittest.mock import patch
from test_runtime import required_module
from test_provider import CONFIG


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.module = required_module(self, 'app.server')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.server = self.module.make_server(CONFIG, port=0, runs_dir=Path(self.tmp.name))
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.stop)
        self.base = 'http://127.0.0.1:' + str(self.server.server_port)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()

    def request(self, path, data=None, token=True):
        headers = {'X-Assessment-Session': self.server.token} if token else {}
        req = urllib.request.Request(self.base+path, data=json.dumps(data).encode() if data is not None else None, headers=headers)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)

    def spec(self):
        return dict(case_id='D01', condition='R0', variant='baseline')

    def test_preview_without_model_or_private_config(self):
        with patch('app.runner.call_model') as call:
            status, obj = self.request('/api/preview', self.spec())
        self.assertEqual(status, 200)
        call.assert_not_called()
        self.assertNotIn('endpoint', json.dumps(obj))
        self.assertEqual(len(obj['visible_passages']), 7)

    def test_dry_run_preview_mismatch_rejected_and_exact_preview_saved(self):
        _, preview = self.request('/api/preview', self.spec())
        body = dict(self.spec(), mode='dry', **{k: preview[k] for k in
            ('question','visible_passages','input_sha256','public_config_sha256')})
        wrong = dict(body, input_sha256='stale')
        self.assertEqual(self.request('/api/run', wrong)[0], 409)
        code, record = self.request('/api/run', body)
        self.assertEqual(code, 200)
        self.assertTrue(record['preview_verified'])
        self.assertEqual(record['messages'], preview['messages'])
        self.assertEqual(record['call_count'], 0)
        self.assertEqual(self.request('/api/runs/'+record['run_id'])[1]['run_id'], record['run_id'])

    def test_paid_disabled_and_missing_session_rejected(self):
        self.assertEqual(self.request('/api/run', dict(self.spec(), mode='paid'))[0], 403)
        self.assertEqual(self.request('/api/preview', self.spec(), token=False)[0], 403)

    def test_unknown_case_and_record_traversal(self):
        self.assertEqual(self.request('/api/preview', dict(self.spec(), case_id='unknown'))[0], 400)
        self.assertEqual(self.request('/api/runs/..%2Fconfig%2Flocal.json')[0], 400)
        self.assertEqual(self.request('/api/runs/no-such-record')[0], 404)

    def test_listing_and_comparison_are_read_only(self):
        a = self.request('/api/run', dict(self.spec(), mode='mock'))[1]
        b = self.request('/api/run', dict(self.spec(), variant='improved', mode='dry'))[1]
        with patch('app.runner.call_model') as call:
            status, rows = self.request('/api/runs')
        call.assert_not_called()
        self.assertEqual(status, 200)
        self.assertEqual({r['run_id'] for r in rows}, {a['run_id'],b['run_id']})
