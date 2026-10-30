import json
import unittest

from evidencegate.engine import verify
from evidencegate.nebius import DEFAULT_ENDPOINT, DEFAULT_MODEL, ModelError, advise, enabled

REPORT = verify({"claims":["Sample machine has 4 axles."],
                 "evidence":[{"id":"D1","title":"Sample","content":"Sample machine has 4 axles."}]})


class Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self, n):
        return json.dumps({"choices": [{"message": {"content": "Review independent certification."}}]}).encode()


class AdapterTests(unittest.TestCase):
    def test_disabled_without_key(self):
        self.assertFalse(enabled({"NEBIUS_LIVE_ENABLED":"1"}))

    def test_disabled_without_optin(self):
        self.assertFalse(enabled({"NEBIUS_API_KEY":"secret"}))

    def test_enabled_only_with_both(self):
        self.assertTrue(enabled({"NEBIUS_LIVE_ENABLED":"1", "NEBIUS_API_KEY":"secret"}))

    def test_never_call_when_disabled(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("No network call expected")
        with self.assertRaises(ModelError): advise(REPORT, env={}, opener=forbidden)

    def test_mock_live_inference(self):
        requests=[]
        def mock(request, timeout):
            requests.append(request)
            return Response()
        result=advise(REPORT, env={"NEBIUS_LIVE_ENABLED":"1", "NEBIUS_API_KEY":"test-only"},opener=mock)
        self.assertEqual(result["model"],DEFAULT_MODEL)
        self.assertTrue(result["verified_live_call"])
        self.assertEqual(len(requests),1)
        self.assertEqual(requests[0].full_url,DEFAULT_ENDPOINT)
        self.assertEqual(json.loads(requests[0].data)["model"],DEFAULT_MODEL)

    def test_wrong_model_rejected(self):
        with self.assertRaises(ModelError):
            advise(REPORT, env={"NEBIUS_LIVE_ENABLED":"1", "NEBIUS_API_KEY":"x", "NEBIUS_MODEL":"other/model"}, opener=lambda *a,**k:Response())

    def test_no_raw_document_in_model_prompt(self):
        record=verify({"claims":["Claim absent"],"evidence":[{"id":"D1","title":"Source","content":"PRIVATE_TEST_RECORD_123"}]})
        captured=[]
        def mock(request, timeout):
            captured.append(request.data.decode());return Response()
        advise(record, env={"NEBIUS_LIVE_ENABLED":"1", "NEBIUS_API_KEY":"x"},opener=mock)
        self.assertNotIn("PRIVATE_TEST_RECORD_123", captured[0])

    def test_transport_failure_is_redacted(self):
        import urllib.error
        def broken(*args,**kwargs):
            raise urllib.error.URLError("super secret error")
        with self.assertRaisesRegex(ModelError,"Nebius request failed") as err:
            advise(REPORT,env={"NEBIUS_LIVE_ENABLED":"1","NEBIUS_API_KEY":"secret"},opener=broken)
        self.assertNotIn("secret",str(err.exception))
