import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_workbench_reasoning import validate_reasoning

class ReasoningEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((ROOT/'data/workbench-reasoning.json').read_text())

    def test_missing_strategy_judgment_is_rejected(self):
        self.data['strategies'][0]['judgmentIds']=['nonexistent']
        with self.assertRaisesRegex(ValueError,'Strategy must link'):validate_reasoning(self.data)

    def test_missing_primary_evidence_is_rejected(self):
        self.data['judgments'][0]['sourceIds']=[]
        with self.assertRaisesRegex(ValueError,'Missing knowledge evidence'):validate_reasoning(self.data)

    def test_an_observation_does_not_require_an_action(self):
        self.data['strategies']=[]
        result=validate_reasoning(self.data)
        self.assertTrue(result['judgments'])
        self.assertFalse(result['strategies'])

if __name__=='__main__':unittest.main()
