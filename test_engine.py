import copy
import json
import unittest

from evidencegate.engine import InputError, validate_request, verify, _terms, _numbers


BASE = {"claims": ["Demo cart has four hydraulic ramps."],
        "evidence": [{"id": "D1", "title": "Demo", "content": "Demo cart has four hydraulic ramps."}]}


class EvidenceEngineTests(unittest.TestCase):
    def data(self):
        return copy.deepcopy(BASE)

    def verdict(self, data=None):
        return verify(data or self.data())["results"][0]["verdict"]

    def test_literal_match(self):
        self.assertEqual(self.verdict(), "SOURCE_TEXT_MATCH")

    def test_match_case_insensitive(self):
        p = self.data(); p["evidence"][0]["content"] = p["evidence"][0]["content"].upper()
        self.assertEqual(self.verdict(p), "SOURCE_TEXT_MATCH")

    def test_match_whitespace_insensitive(self):
        p = self.data(); p["evidence"][0]["content"] = "Demo   cart\n has four hydraulic   ramps."
        self.assertEqual(self.verdict(p), "SOURCE_TEXT_MATCH")

    def test_multiple_claims(self):
        p = self.data(); p["claims"].append("Something absent entirely")
        self.assertEqual(len(verify(p)["results"]), 2)

    def test_multiple_sources(self):
        p = self.data(); p["evidence"].append({"id":"D2", "title":"Alternative", "content": "Other text."})
        self.assertEqual(self.verdict(p), "SOURCE_TEXT_MATCH")

    def test_missing_evidence(self):
        p = self.data(); p["evidence"][0]["content"] = "This note says nothing about the claim."
        self.assertEqual(self.verdict(p), "INSUFFICIENT_EVIDENCE")

    def test_numeric_conflict_flag(self):
        p = self.data(); p["claims"] = ["Prototype machine supports 12 tonnes ramp load."]
        p["evidence"][0]["content"] = "Prototype machine supports 10 tonnes ramp load."
        self.assertEqual(self.verdict(p), "POSSIBLE_NUMERIC_CONFLICT")

    def test_numeric_agreement_not_enough(self):
        p = self.data(); p["claims"] = ["Prototype machine supports 12 tonnes ramp load."]
        p["evidence"][0]["content"] = "Prototype machine has 12 tyres."
        self.assertEqual(self.verdict(p), "INSUFFICIENT_EVIDENCE")

    def test_mixed_sources(self):
        p = self.data(); p["claims"] = ["Prototype machine supports 12 tonnes ramp load."]
        p["evidence"] = [
            {"id":"A", "title":"A", "content": "Prototype machine supports 12 tonnes ramp load."},
            {"id":"B", "title":"B", "content": "Prototype machine supports 10 tonnes ramp load."}]
        self.assertEqual(self.verdict(p), "MIXED_EVIDENCE_REVIEW")

    def test_no_external_truth_claim(self):
        report = verify(self.data())
        self.assertIn("not establish external truth", report["results"][0]["note"])

    def test_digest_stable(self):
        self.assertEqual(verify(self.data())["input_sha256"], verify(self.data())["input_sha256"])

    def test_digest_changes_on_content_change(self):
        p = self.data(); p["evidence"][0]["content"] += " new"
        self.assertNotEqual(verify(self.data())["input_sha256"], verify(p)["input_sha256"])

    def test_digest_is_sha256(self):
        self.assertEqual(len(verify(self.data())["input_sha256"]), 64)

    def test_provenance_in_result(self):
        self.assertEqual(verify(self.data())["results"][0]["matches"][0]["id"], "D1")

    def test_input_object_required(self):
        with self.assertRaises(InputError): validate_request([])

    def test_claim_list_required(self):
        p = self.data(); p["claims"] = "text"
        with self.assertRaises(InputError): validate_request(p)

    def test_claim_nonempty(self):
        p = self.data(); p["claims"] = [" "]
        with self.assertRaises(InputError): validate_request(p)

    def test_claim_too_long(self):
        p = self.data(); p["claims"] = ["z"*501]
        with self.assertRaises(InputError): validate_request(p)

    def test_too_many_claims(self):
        p = self.data(); p["claims"] = ["claim"]*9
        with self.assertRaises(InputError): validate_request(p)

    def test_empty_evidence_list(self):
        p = self.data(); p["evidence"] = []
        with self.assertRaises(InputError): validate_request(p)

    def test_too_many_evidence(self):
        p = self.data(); p["evidence"] = [{"id":str(i), "title":"X", "content":"Y"} for i in range(13)]
        with self.assertRaises(InputError): validate_request(p)

    def test_duplicate_evidence_id(self):
        p = self.data(); p["evidence"].append(copy.deepcopy(p["evidence"][0]))
        with self.assertRaises(InputError): validate_request(p)

    def test_evidence_id_not_filepath(self):
        p = self.data(); p["evidence"][0]["id"] = "../etc/passwd"
        with self.assertRaises(InputError): validate_request(p)

    def test_nonstring_evidence(self):
        p = self.data(); p["evidence"][0]["content"] = None
        with self.assertRaises(InputError): validate_request(p)

    def test_long_content(self):
        p = self.data(); p["evidence"][0]["content"] = "x" * 12001
        with self.assertRaises(InputError): validate_request(p)

    def test_bad_url(self):
        p = self.data(); p["evidence"][0]["source_url"] = "file:///etc/passwd"
        with self.assertRaises(InputError): validate_request(p)

    def test_http_source_accepted_not_fetched(self):
        p = self.data(); p["evidence"][0]["source_url"] = "https://example.com/a"
        self.assertEqual(verify(p)["results"][0]["matches"][0]["source_url"], "https://example.com/a")

    def test_numbers_ignore_identifier_digits(self):
        self.assertEqual(_numbers("Trailer X7 has 12 tonnes"), {"12"})

    def test_terms_ignore_stop_words(self):
        self.assertNotIn("the", _terms("The trailer is ready"))

    def test_json_serializable(self):
        self.assertTrue(json.loads(json.dumps(verify(self.data())))["results"])
