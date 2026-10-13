import importlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app import runner

CONFIG = {'provider': 'test', 'model': 'offline-fixture',
          'endpoint': 'https://private.invalid/v1/chat/completions',
          'parameters': {'temperature': 0}, 'timeout_seconds': 4}


def required_module(test, name):
    test.assertIsNotNone(importlib.util.find_spec(name), f'{name} feature is missing')
    return importlib.import_module(name)


def response(content):
    return {'choices': [{'message': {'content': content}}], 'usage': {'prompt_tokens': 10}}


class RuntimeTests(unittest.TestCase):
    def test_output_is_strict_and_preserves_original_content(self):
        checks = required_module(self, 'app.output_checks')
        for content, want in [
            ('{"answer":"80%","citations":["p1"]}', 'valid'),
            (chr(96)*3+'json\n{"answer":"80%","citations":[]}\n'+chr(96)*3, 'invalid'),
            ('{"answer":80,"citations":[]}', 'invalid'),
            ('{"answer":"80%","citations":[1]}', 'invalid'),
            ('{"citations":[]}', 'invalid'),
            ('{"answer":"","citations":[]}', 'invalid'),
        ]:
            with self.subTest(content=content):
                actual = checks.parse_output(response(content))
                self.assertEqual(actual['format_status'], want)
                self.assertEqual(actual['content_raw'], content)
        self.assertEqual(checks.parse_output({'choices': []})['format_status'], 'absent')

    def test_citation_membership_does_not_check_semantics(self):
        checks = required_module(self, 'app.output_checks')
        known = [{'id': 'p1', 'text': 'only a location', 'source': 's'}]
        self.assertEqual(checks.check_citations(['p1'], known)['locator_status'], 'valid')
        self.assertEqual(checks.check_citations([], known)['locator_status'], 'absent')
        r = checks.check_citations(['p1', 'outside'], known)
        self.assertEqual(r['locator_status'], 'invalid')
        self.assertEqual(r['unknown_citations'], ['outside'])

    def test_improve_cannot_read_outside_current_condition(self):
        case = runner.get_case('D01')
        hidden = next(p for p in case['passages'] if p['id'] not in case['conditions']['K'])
        with patch('app.student.improve', return_value=[hidden]):
            with self.assertRaises(ValueError):
                runner.prepare('D01', 'K', 'improved')

    def test_dry_run_saves_exact_messages_without_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = runner.execute('D01', 'R0', 'baseline', CONFIG, dry=True, outdir=tmp)
            stored = json.loads(next(Path(tmp).glob('*.json')).read_text(encoding='utf-8'))
            self.assertNotIn('endpoint', stored['config'])
            self.assertEqual(stored['schema_version'], 2)
            self.assertEqual(stored['run_kind'], 'dry_run')
            self.assertEqual(stored['call_count'], 0)
            self.assertEqual(stored['messages'], record['messages'])
            self.assertEqual(len(stored['selected_passages']), 7)

    def test_valid_provider_response_does_not_invent_semantic_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = {'status': 'ok', 'response': response('{"answer":"80%","citations":["P312446"]}'),
                      'response_raw': 'wire', 'usage': {}, 'elapsed_seconds': 0.02, 'call_count': 1}
            with patch('app.runner.call_model', return_value=result):
                r = runner.execute('D01', 'R0', 'baseline', CONFIG, outdir=tmp)
            self.assertEqual(r.get('support_status'), 'not_checked')
            self.assertEqual(r.get('format_status'), 'valid')
            self.assertEqual(r.get('locator_status'), 'valid')
            self.assertEqual(r['response_raw'], 'wire')

    def test_prepare_failure_is_saved_with_safe_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('app.student.prepare_messages', side_effect=ValueError('secret-url')):
                try:
                    result = runner.execute('D01', 'R0', 'baseline', CONFIG, dry=True, outdir=tmp)
                except ValueError:
                    self.fail('preparation errors must be recorded rather than lost')
            self.assertEqual(result['api_status'], 'preparation_error')
            self.assertNotIn('secret-url', next(Path(tmp).glob('*.json')).read_text(encoding='utf-8'))

    def test_transport_exception_still_leaves_terminal_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('app.runner.call_model', side_effect=TimeoutError('private endpoint')):
                try:
                    r = runner.execute('D01', 'R0', 'baseline', CONFIG, outdir=tmp)
                except TimeoutError:
                    self.fail('transport exception was not recorded')
            self.assertEqual(r['status'], 'internal_error')
            self.assertEqual(r['error_code'], 'TimeoutError')
            self.assertNotIn('private endpoint', json.dumps(r))

    def test_keyboard_interrupt_leaves_started_and_retry_gets_own_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch('app.runner.call_model', side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    runner.execute('D01', 'R0', 'baseline', CONFIG, outdir=tmp)
            files = list(Path(tmp).glob('*.json'))
            self.assertEqual(len(files), 1)
            first = json.loads(files[0].read_text(encoding='utf-8'))
            self.assertEqual(first['status'], 'started')
            r = runner.execute('D01', 'R0', 'baseline', CONFIG, dry=True, outdir=tmp,
                               metadata={'retry_of': first['run_id'], 'attempt_index': 2})
            self.assertNotEqual(r['run_id'], first['run_id'])
            self.assertEqual(len(list(Path(tmp).glob('*.json'))), 2)

    def test_terminal_record_is_immutable(self):
        records = required_module(self, 'app.run_records')
        with tempfile.TemporaryDirectory() as tmp:
            path = records.start_record({'run_id': 'one', 'status': 'started'}, Path(tmp))
            records.finish_record(path, {'status': 'ok'})
            with self.assertRaises(ValueError):
                records.finish_record(path, {'status': 'ok', 'response': 'replace'})


if __name__ == '__main__':
    unittest.main()
