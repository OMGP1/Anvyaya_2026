"""The deployment WSGI transport runs the same authenticated workflows under Waitress."""
from http.client import HTTPConnection
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_api import Client
import server
import wsgi
from waitress.server import create_server


class RuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.original_db = server.DB
        server.DB = Path(cls.temp.name) / 'runtime.sqlite'
        cls.httpd = create_server(wsgi.create_app(), host='127.0.0.1', port=0, threads=2, max_request_body_size=800000)
        cls.stopping = False
        def serve():
            try:
                cls.httpd.run()
            except OSError:
                if not cls.stopping:
                    raise
        cls.thread = threading.Thread(target=serve, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.httpd.effective_port}'

    @classmethod
    def tearDownClass(cls):
        cls.stopping = True
        cls.httpd.task_dispatcher.shutdown()
        cls.httpd.close()
        cls.thread.join(timeout=2)
        server.DB = cls.original_db
        cls.temp.cleanup()

    def test_static_health_and_security_headers(self):
        for path in ['/', '/app.js', '/workflows.js', '/safety.js', '/style.css', '/api/health']:
            with urlopen(self.base + path) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
                self.assertTrue(response.read())
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(self.base + '/api/data', method='PUT'))
        self.assertEqual(error.exception.code, 405)
        error.exception.close()

    def test_authenticated_mutation_scope_and_export(self):
        admin = Client(self.base).login('admin')
        self.assertEqual(admin.call('/api/data')[0], 200)
        payload = {'study_id': 'AIIA-001', 'age': 35, 'sex': 'F', 'prakriti': 'Not assessed', 'consent': True, 'consent_version': '2.1', 'consent_language': 'English'}
        self.assertEqual(admin.call('/api/enrolments', payload, {'X-CSRF-Token': 'wrong'})[0], 403)
        self.assertEqual(admin.call('/api/enrolments', payload)[0], 200)
        self.assertTrue(admin.call('/api/exchange/check')[1]['passed'])
        self.assertEqual(admin.call('/api/export/fhir?study=AIIA-001')[1]['resourceType'], 'Bundle')
        regulator = Client(self.base).login('regulator')
        self.assertEqual(regulator.call('/api/enrolments', payload)[0], 403)
        self.assertTrue(admin.call('/api/audit')[1]['verification']['valid'])

    def test_cross_origin_and_body_boundary(self):
        client = Client(self.base).login('admin')
        self.assertEqual(client.call('/api/logout', {}, {'Origin': 'https://wrong.example'})[0], 403)
        connection = HTTPConnection('127.0.0.1', self.httpd.effective_port, timeout=5)
        connection.putrequest('POST', '/api/login')
        connection.putheader('Content-Length', '800001')
        connection.endheaders()
        response = connection.getresponse()
        self.assertEqual(response.status, 413)
        response.read()
        connection.close()
        self.assertEqual(client.call('/api/logout', {})[0], 200)
        self.assertEqual(client.call('/api/data')[0], 401)


if __name__ == '__main__':
    unittest.main(verbosity=2)
