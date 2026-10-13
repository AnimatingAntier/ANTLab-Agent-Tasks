import unittest
from test_runtime import required_module


def record(answer='80%', **extras):
    return dict(run_id='first', case_id='T01', condition='R0', variant='baseline',
                experiment_id='main', is_primary=True, attempt_index=1, retry_of=None,
                run_kind='live_api', api_status='ok', status='ok', format_status='valid',
                parsed_output={'answer': answer, 'citations': ['wrong']},
                locator_status='valid', call_count=1, elapsed_seconds=0.1, **extras)


class ScoringTests(unittest.TestCase):
    def test_correct_number_does_not_imply_semantic_support(self):
        module = required_module(self, 'app.scoring')
        r = module.score_record(record(), {'answer_type': 'percent', 'expected_answer': '80%'}, None)
        self.assertTrue(r['task_correct'])
        self.assertEqual(r['semantic_support'], 'not_checked')
        r = module.score_record(record(), {'answer_type': 'percent', 'expected_answer': '80%'},
                                {'semantic_support': 'contradicted', 'reason': 'wrong batch',
                                 'judgment_source': 'human'})
        self.assertTrue(r['task_correct'])
        self.assertEqual(r['semantic_support'], 'contradicted')

    def test_reasonable_abstention_on_missing_input_is_not_task_success(self):
        module = required_module(self, 'app.scoring')
        r = module.score_record(record('证据不足'), {'answer_type': 'percent', 'expected_answer': '80%'},
                                {'abstention_reasonable': True, 'reason': 'denominator missing'})
        self.assertFalse(r['task_correct'])
        self.assertTrue(r['abstention_reasonable'])

    def test_numeric_comparison_is_not_substring_matching(self):
        module = required_module(self, 'app.scoring')
        label = {'answer_type': 'number', 'expected_answer': '1.8'}
        self.assertTrue(module.score_record(record('1.80'), label, None)['task_correct'])
        self.assertFalse(module.score_record(record('11.8'), label, None)['task_correct'])
        self.assertFalse(module.score_record(record('大约1.8'), label, None)['task_correct'])

    def test_missing_label_stays_pending_and_failure_is_counted(self):
        module = required_module(self, 'app.scoring')
        self.assertIsNone(module.score_record(record(), None, None)['task_correct'])
        failed = record()
        failed.update(api_status='transport_error', status='transport_error', format_status='absent')
        self.assertFalse(module.score_record(failed, None, None)['task_correct'])

    def test_retry_does_not_replace_failed_first_or_shrink_denominator(self):
        module = required_module(self, 'app.scoring')
        jobs = [{'job_id': f'T{i:02}:R0:baseline', 'case_id': f'T{i:02}',
                 'condition': 'R0', 'variant': 'baseline'} for i in range(1,9)]
        rows = []
        for i in range(1,9):
            r = record()
            r.update(run_id=f'run{i}', case_id=f'T{i:02}', job_id=f'T{i:02}:R0:baseline')
            if i == 1:
                r.update(status='transport_error', api_status='transport_error', format_status='absent')
            rows.append(module.score_record(r, {'answer_type':'percent','expected_answer':'80%'}, None))
        retry = record()
        retry.update(run_id='retry', is_primary=False, attempt_index=2, retry_of='run1')
        rows.append(module.score_record(retry, {'answer_type':'percent','expected_answer':'80%'}, None))
        summary = module.summarize(rows, {'experiment_id':'main','jobs':jobs})
        group = summary['conditions']['R0']
        self.assertEqual(group['denominator'], 8)
        self.assertEqual(group['correct'], 7)
        self.assertEqual(group['accuracy'], 0.875)
        self.assertEqual(group['technical_failures'], 1)
        self.assertEqual(summary['retry_count'], 1)

    def test_duplicate_primary_is_rejected(self):
        module = required_module(self, 'app.scoring')
        row = module.score_record(record(), {'answer_type':'percent','expected_answer':'80%'}, None)
        manifest = {'experiment_id':'main','jobs':[{'job_id':'T01:R0:baseline',
                    'case_id':'T01','condition':'R0','variant':'baseline'}]}
        with self.assertRaises(ValueError):
            module.summarize([row, dict(row, run_id='another')], manifest)
