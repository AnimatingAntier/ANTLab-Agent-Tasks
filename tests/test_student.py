import copy
import json
import random
import unittest

from app import student


def passages():
    return [
        {'id': 'noise', 'source': 's1', 'text': '长青研究项目R8在2026-07的压力组ZX92，耗时2秒。'},
        {'id': 'appendix', 'source': 's2', 'text': '批次LM71复核补页：LM71有27项通过。'},
        {'id': 'old', 'source': 's3', 'text': '长青研究项目R7在2026-07正式回归批次OLD70，共80项。'},
        {'id': 'anchor', 'source': 's4', 'text': '长青研究项目R8在2026-07正式回归批次LM71，共30项。'},
    ]


QUERY = '长青研究项目R8在2026-07正式回归批次的核验率是多少？'


class StudentTests(unittest.TestCase):
    def test_baseline_preserves_exact_text_source_and_order(self):
        inputs = passages()
        for items in (inputs, list(reversed(inputs))):
            try:
                messages = student.prepare_messages(QUERY, items)
            except NotImplementedError:
                self.fail('prepare_messages has not implemented the request contract')
            self.assertEqual([m['role'] for m in messages], ['system', 'user'])
            payload = json.loads(messages[-1]['content'])
            self.assertEqual(payload, {'question': QUERY, 'passages': items})

    def test_groups_anchor_and_linked_appendix_without_dropping_text(self):
        inputs = passages()
        original = copy.deepcopy(inputs)
        output = student.improve(QUERY, inputs)
        self.assertEqual([p['id'] for p in output[:2]], ['anchor', 'appendix'])
        self.assertCountEqual(output, original)
        self.assertEqual(inputs, original)

    def test_remapping_ids_and_sources_does_not_change_content_order(self):
        inputs = passages()
        remapped = [dict(p, id=f'ref-{99-i}', source=f'changed-{i}') for i,p in enumerate(inputs)]
        random.Random(33).shuffle(remapped)
        self.assertEqual([p['text'] for p in student.improve(QUERY, inputs)],
                         [p['text'] for p in student.improve(QUERY, remapped)])

    def test_other_batch_and_wrong_version_do_not_join_evidence_group(self):
        inputs = passages()
        inputs.insert(0, {'id': 'false', 'source': 's', 'text': '批次ZX92的核验率99%。'})
        inputs.insert(0, {'id': 'version', 'source': 's', 'text': 'R7批次LM71的补页有99项通过。'})
        output = student.improve(QUERY, inputs)
        self.assertEqual([p['id'] for p in output[:2]], ['anchor', 'appendix'])

    def test_unknown_scope_falls_back_without_guessing_or_mutation(self):
        inputs = passages()
        self.assertEqual(student.improve('材料是否提供GPU型号？', inputs), inputs)


if __name__ == '__main__':
    unittest.main()
