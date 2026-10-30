"""144 strictly synthetic scenarios, not real production verification."""
import unittest
from evidencegate.engine import verify


class SyntheticEvaluationTests(unittest.TestCase):
    def test_144_synthetic_cases(self):
        counts={"SOURCE_TEXT_MATCH":0,"POSSIBLE_NUMERIC_CONFLICT":0,"INSUFFICIENT_EVIDENCE":0}
        for i in range(48):
            claim=f"Test rig T{i} supports {i+100} kilograms of load."
            cases=[
                (f"Test rig T{i} supports {i+100} kilograms of load.","SOURCE_TEXT_MATCH"),
                (f"Test rig T{i} supports {i+101} kilograms of load.","POSSIBLE_NUMERIC_CONFLICT"),
                ("A blank inventory note about warehouse lighting only.","INSUFFICIENT_EVIDENCE"),
            ]
            for source, expected in cases:
                data={"claims":[claim],"evidence":[{"id":"D1","title":"Synthetic", "content":source}]}
                got=verify(data)["results"][0]["verdict"]
                self.assertEqual(got,expected,(i,source,got))
                counts[got]+=1
        self.assertEqual(sum(counts.values()),144)
        self.assertEqual(counts["SOURCE_TEXT_MATCH"],48)
        self.assertEqual(counts["POSSIBLE_NUMERIC_CONFLICT"],48)
        self.assertEqual(counts["INSUFFICIENT_EVIDENCE"],48)
