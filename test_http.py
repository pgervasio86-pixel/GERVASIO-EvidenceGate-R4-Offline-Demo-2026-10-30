import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from evidencegate.server import Handler


class LocalHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever,daemon=True)
        cls.thread.start()
        cls.port=cls.httpd.server_port

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown();cls.httpd.server_close();cls.thread.join(timeout=5)

    def call(self, method, path, body=None):
        c=http.client.HTTPConnection("127.0.0.1",self.port,timeout=5)
        try:
            headers={"Content-Type":"application/json"} if body is not None else {}
            c.request(method,path,body=body,headers=headers)
            r=c.getresponse();return r.status,r.getheader("Content-Type"),r.read()
        finally:
            c.close()

    def test_frontpage(self):
        status,mime,body=self.call("GET","/")
        self.assertEqual(status,200);self.assertIn(b"EvidenceGate",body)

    def test_javascript(self):
        status,mime,body=self.call("GET","/app.js")
        self.assertEqual(status,200);self.assertIn(b"offlineVerify",body)

    def test_css(self):
        status,mime,body=self.call("GET","/styles.css")
        self.assertEqual(status,200);self.assertIn(b".panel",body)

    def test_404(self):
        status,_,_=self.call("GET","/secret.env")
        self.assertEqual(status,404)

    def test_status_without_model(self):
        with patch.dict("os.environ",{"NEBIUS_LIVE_ENABLED":"0"},clear=True):
            status,_,body=self.call("GET","/api/status")
        self.assertEqual(status,200);self.assertFalse(json.loads(body)["live_enabled"])

    def test_post_verify(self):
        obj={"claims":["Demo vehicle has 4 axles."],"evidence":[{"id":"X1","title":"Synthetic","content":"Demo vehicle has 4 axles."}]}
        status,_,body=self.call("POST","/api/verify",json.dumps(obj))
        self.assertEqual(status,200);self.assertEqual(json.loads(body)["results"][0]["verdict"],"SOURCE_TEXT_MATCH")

    def test_bad_json(self):
        status,_,body=self.call("POST","/api/verify","{")
        self.assertEqual(status,400)

    def test_bad_payload(self):
        status,_,body=self.call("POST","/api/verify",json.dumps({"claims":[]}))
        self.assertEqual(status,400)

    def test_no_unrequested_live_call(self):
        obj={"claims":["A"],"evidence":[{"id":"X1","title":"X","content":"A"}]}
        with patch("evidencegate.server.advise",side_effect=AssertionError("called")):
            status,_,body=self.call("POST","/api/verify",json.dumps(obj))
        self.assertEqual(status,200);self.assertEqual(json.loads(body)["nemotron"]["status"],"not_requested")

    def test_traversal_404(self):
        status,_,_=self.call("GET","/../../.env")
        self.assertEqual(status,404)
