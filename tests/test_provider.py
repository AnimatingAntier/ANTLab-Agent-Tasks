import io
import os
import unittest
from urllib.error import HTTPError
from unittest.mock import patch
from app.provider import call_model

CONFIG = {'provider': 'test', 'model': 'test-model', 'endpoint': 'https://private.invalid/chat',
          'parameters': {}, 'timeout_seconds': 1}


class Reply(io.BytesIO):
    status = 200


class ProviderTests(unittest.TestCase):
    def test_missing_key_does_not_send_request(self):
        with patch.dict(os.environ, {'ASSESSMENT_API_KEY': ''}):
            try:
                r = call_model([], CONFIG)
            except ValueError:
                self.fail('missing credentials should return a countable safe error')
        self.assertEqual(r['status'], 'config_error')
        self.assertEqual(r['call_count'], 0)

    def test_success_preserves_raw_and_usage(self):
        raw = b'{"choices":[{"message":{"content":"answer"}}],"usage":{"completion_tokens":3}}'
        with patch.dict(os.environ, {'ASSESSMENT_API_KEY': 'fixture-secret'}):
            with patch('urllib.request.urlopen', return_value=Reply(raw)):
                r = call_model([], CONFIG)
        self.assertEqual(r.get('response_raw'), raw.decode())
        self.assertEqual(r.get('call_count'), 1)
        self.assertEqual(r['usage']['completion_tokens'], 3)

    def test_http_error_retains_code_but_not_secret_error_page(self):
        error = HTTPError(CONFIG['endpoint'], 401, 'private error', {}, io.BytesIO(b'fixture-secret'))
        with patch.dict(os.environ, {'ASSESSMENT_API_KEY': 'fixture-secret'}):
            with patch('urllib.request.urlopen', side_effect=error):
                r = call_model([], CONFIG)
        self.assertEqual(r['status'], 'http_error')
        self.assertEqual(r['http_status'], 401)
        self.assertNotIn('fixture-secret', str(r))
        self.assertEqual(r.get('call_count'), 1)
