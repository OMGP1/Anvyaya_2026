"""Integration proof using an isolated database; never mutates the demo database."""
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from datetime import timedelta
from http.cookiejar import CookieJar
from urllib.error import HTTPError
from urllib.request import build_opener, HTTPCookieProcessor, Request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class Client:
    def __init__(self, base):
        self.base = base
        self.http = build_opener(HTTPCookieProcessor(CookieJar()))
        self.csrf = ''

    def call(self, path, body=None, headers=None):
        request = Request(self.base + path, data=None if body is None else json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'X-CSRF-Token': self.csrf, **(headers or {})})
        try:
            with self.http.open(request) as response:
                raw = response.read()
                return response.status, json.loads(raw) if 'json' in response.headers['Content-Type'] else raw
        except HTTPError as error:
            try:
                return error.code, json.loads(error.read())
            finally:
                error.close()

    def login(self, role):
        assert self.call('/api/login', {'role': role, 'password': server.PASSWORD})[0] == 200
        self.csrf = self.call('/api/me')[1]['csrf']
        return self


class WorkflowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        server.DB = Path(cls.temp.name) / 'test.sqlite'
        server.initialize()
        cls.httpd = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.httpd.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.temp.cleanup()

    def setUp(self):
        self.admin = Client(self.base).login('admin')

    def enrol(self, **changes):
        return {'study_id': 'AIIA-001', 'age': 35, 'sex': 'F', 'prakriti': 'Not assessed', 'consent': True, 'consent_version': '2.1', 'consent_language': 'English', **changes}

    def test_01_authentication_and_csrf(self):
        anon = Client(self.base)
        self.assertEqual(anon.call('/api/data')[0], 401)
        self.assertEqual(anon.call('/api/login', {'role': 'admin', 'password': 'wrong'})[0], 401)
        self.assertEqual(self.admin.call('/api/enrolments', self.enrol(), {'X-CSRF-Token': 'wrong'})[0], 403)
        self.assertEqual(self.admin.call('/api/enrolments', self.enrol(), {'Origin': 'https://untrusted.example'})[0], 403)

    def test_02_enrolment_guards_and_atomicity(self):
        before = self.admin.call('/api/data')[1]['kpis']['enrolled']
        for payload, code in [(self.enrol(consent=False), 400), (self.enrol(consent='true'), 400), (self.enrol(study_id='AIIA-004'), 409), (self.enrol(consent_version='1.0'), 409), (self.enrol(age=True), 400), (self.enrol(age=17), 400)]:
            self.assertEqual(self.admin.call('/api/enrolments', payload)[0], code)
        self.assertEqual(self.admin.call('/api/data')[1]['kpis']['enrolled'], before)
        status, result = self.admin.call('/api/enrolments', self.enrol())
        self.assertEqual(status, 200)
        data = self.admin.call('/api/data')[1]
        self.assertEqual(data['kpis']['enrolled'], before + 1)
        self.assertEqual(sum(v['participant_id'] == result['record']['id'] for v in data['visits']), 2)

    def test_03_scope_and_readonly(self):
        pi = Client(self.base).login('pi')
        data = pi.call('/api/data')[1]
        self.assertEqual({s['id'] for s in data['studies']}, {'AIIA-001', 'AIIA-002'})
        self.assertTrue(all(p['study_id'] in ['AIIA-001', 'AIIA-002'] for p in data['participants']))
        self.assertEqual(pi.call('/api/enrolments', self.enrol(study_id='AIIA-003'))[0], 403)
        self.assertEqual(pi.call('/api/export/fhir?study=AIIA-003')[0], 403)
        regulator = Client(self.base).login('regulator')
        self.assertEqual(regulator.call('/api/enrolments', self.enrol())[0], 403)
        self.assertEqual(regulator.call('/api/queries/DQ-001/resolve', {'resolution': 'changed'})[0], 403)

    def test_04_leadership_redaction(self):
        lead = Client(self.base).login('leadership')
        data = lead.call('/api/data')[1]
        for key in ['participants', 'events', 'queries', 'visits']:
            self.assertEqual(data[key], [])
        self.assertGreater(data['kpis']['enrolled'], 0)
        self.assertEqual(lead.call('/api/export/fhir')[0], 403)
        self.assertEqual(lead.call('/api/audit')[0], 403)

    def test_05_safety_clocks_and_duplicate_reporting(self):
        occurrence = server.utcnow() - timedelta(hours=26)
        payload = {'participant_id': 'SYN-01-003', 'term': 'Synthetic hospitalisation', 'narrative': 'Workflow verification only', 'seriousness': 'Hospitalisation', 'severity': 'Mild', 'occurred_at': server.stamp(occurrence), 'awareness_at': server.stamp(occurrence + timedelta(hours=20))}
        status, result = self.admin.call('/api/safety', payload)
        self.assertEqual(status, 200)
        event = result['record']
        self.assertTrue(event['serious'])
        self.assertEqual(event['initial_due'], server.stamp(occurrence + timedelta(hours=24)))
        self.assertEqual(event['analysis_due'], server.stamp(occurrence + timedelta(days=14)))
        report = {'phase': 'analysis', 'reference': 'DEMO-ACK', 'reason': 'Test evidence'}
        endpoint = '/api/safety/' + event['id'] + '/report'
        self.assertEqual(self.admin.call(endpoint, report)[0], 409)
        report['phase'] = 'initial'
        self.assertEqual(self.admin.call(endpoint, report)[0], 200)
        self.assertEqual(self.admin.call(endpoint, report)[0], 409)
        payload['participant_id'] = 'SYN-02-004'
        non_ndct = self.admin.call('/api/safety', payload)[1]['record']
        self.assertIsNone(non_ndct['analysis_due'])
        self.assertIn('Protocol SOP', non_ndct['rule'])

    def test_06_consent_withdrawal_blocks_visits_preserves_safety(self):
        pid = 'SYN-01-005'
        self.assertEqual(self.admin.call(f'/api/participants/{pid}/withdraw', {'reason': 'Synthetic withdrawal request'})[0], 200)
        self.assertEqual(self.admin.call(f'/api/visits/{pid}-V1/complete', {'reason': 'Attempt after withdrawal'})[0], 409)
        payload = {'participant_id': pid, 'term': 'Follow-up safety report', 'narrative': 'Safety reporting remains available after withdrawal', 'seriousness': 'Non-serious', 'severity': 'Mild', 'occurred_at': server.stamp(), 'awareness_at': server.stamp()}
        self.assertEqual(self.admin.call('/api/safety', payload)[0], 200)

    def test_07_export_references_and_mapping(self):
        status, bundle = self.admin.call('/api/export/fhir')
        self.assertEqual(status, 200)
        self.assertEqual(bundle['type'], 'collection')
        urls = {entry['fullUrl'] for entry in bundle['entry']}
        for entry in bundle['entry']:
            resource = entry['resource']
            self.assertEqual(resource['text']['status'], 'generated')
            self.assertIn('http://www.w3.org/1999/xhtml', resource['text']['div'])
            for key in ['study', 'individual', 'patient', 'consent']:
                if key in resource:
                    self.assertIn(resource[key]['reference'], urls)
            if resource['resourceType'] == 'ResearchSubject':
                self.assertIn(resource['status'], ['on-study', 'withdrawn'])
        status, raw = self.admin.call('/api/export/dm')
        records = list(csv.DictReader(io.StringIO(raw.decode())))
        self.assertEqual(status, 200)
        self.assertEqual(len(records), self.admin.call('/api/data')[1]['kpis']['enrolled'])
        self.assertEqual(records[0]['DOMAIN'], 'DM')

    def test_08_query_resolution_and_audit(self):
        endpoint = '/api/queries/DQ-001/resolve'
        self.assertEqual(self.admin.call(endpoint, {'resolution': 'Source verified in synthetic record'})[0], 200)
        self.assertEqual(self.admin.call(endpoint, {'resolution': 'Duplicate'})[0], 409)
        ledger = self.admin.call('/api/audit')[1]
        self.assertTrue(ledger['verification']['valid'])
        self.assertTrue(any(e['action'] == 'QUERY_RESOLVED' and e['before']['status'] == 'Open' for e in ledger['entries']))
        with server.connect() as conn:
            with self.assertRaises(server.sqlite3.IntegrityError):
                conn.execute("UPDATE audit SET hash='bad' WHERE seq=1")
            with self.assertRaises(server.sqlite3.IntegrityError):
                conn.execute('DELETE FROM audit WHERE seq=1')

    def test_09_static_allowlist_and_settings(self):
        self.assertEqual(self.admin.call('/server.py')[0], 404)
        self.assertEqual(self.admin.call('/data/ctms.sqlite')[0], 404)
        self.assertEqual(self.admin.call('/api/settings', {'enrolment_threshold': 70, 'iec_days': 500, 'query_days': 7})[0], 400)
        self.assertEqual(self.admin.call('/api/settings', {'enrolment_threshold': 75, 'iec_days': 20, 'query_days': 5})[0], 200)

    def test_10_withdrawn_future_visits_do_not_reduce_compliance(self):
        with server.connect() as conn:
            p = server.get(conn, 'participants', 'SYN-01-006')
            p.update(consent=False, status='Withdrawn', withdrawn_at=server.stamp(server.utcnow()-timedelta(days=1)))
            server.save(conn, 'participants', p)
            v = server.get(conn, 'visits', p['id']+'-V1')
            v.update(due=server.utcnow().date().isoformat(), completed_at=None)
            server.save(conn, 'visits', v)
            before = server.snapshot(conn, 'admin')
            cancelled = next(x for x in before['visits'] if x['id']==v['id'])
            self.assertTrue(cancelled['cancelled'])
            self.assertFalse(cancelled['consent_active'])
            conn.execute('DELETE FROM visits WHERE id=?', (v['id'],))
            after = server.snapshot(conn, 'admin')
            self.assertEqual(before['kpis']['visits_due'], after['kpis']['visits_due'])

    def test_11_initialization_preserves_existing_records(self):
        before = self.admin.call('/api/data')[1]
        server.initialize()
        after = self.admin.call('/api/data')[1]
        self.assertEqual(before['participants'], after['participants'])
        self.assertEqual(before['events'], after['events'])
        self.assertEqual(before['queries'], after['queries'])

    def test_12_tampering_is_detected_even_if_database_trigger_is_removed(self):
        with server.connect() as conn:
            conn.execute('SAVEPOINT tamper_check')
            conn.execute('DROP TRIGGER audit_no_update')
            conn.execute("UPDATE audit SET payload='{}' WHERE seq=1")
            self.assertFalse(server.verify_audit(conn)['valid'])
            conn.execute('ROLLBACK TO tamper_check')
            conn.execute('RELEASE tamper_check')
            self.assertTrue(server.verify_audit(conn)['valid'])

    def new_study(self, **changes):
        status, result = self.admin.call('/api/studies', {'title': 'Synthetic activation proof', 'condition': 'Workflow testing', 'target': 10, 'type': 'Compound formulation', 'formulation': 'Fictional protocol formulation', 'site': 'Delhi', **changes})
        self.assertEqual(status, 200)
        return result['record']

    def setup_payload(self, study, **changes):
        today = server.utcnow().date()
        return {'revision': study['revision'], 'protocol': 'P-3', 'consent_version': 'ICF-2', 'formulation': 'Reviewed fictional formulation', 'pi': 'Synthetic investigator', 'batch': 'DEMO-BATCH-TEST', 'ctri': 'DEMO-CTRI-TEST', 'registered_at': today.isoformat(), 'iec_reference': 'DEMO-IEC-TEST', 'iec_approved_at': today.isoformat(), 'iec_expiry': (today + timedelta(days=30)).isoformat(), 'start': today.isoformat(), 'end': (today + timedelta(days=90)).isoformat(), 'reason': 'Synthetic source evidence reviewed', **changes}

    def test_13_setup_activation_and_separate_consent_versions(self):
        study = self.new_study()
        endpoint = '/api/studies/' + study['id']
        decision = {'revision': study['revision'], 'reviewed': True, 'reason': 'Synthetic activation review'}
        self.assertEqual(self.admin.call(endpoint + '/activate', decision)[0], 409)
        status, result = self.admin.call(endpoint + '/setup', self.setup_payload(study))
        self.assertEqual(status, 200)
        configured = result['record']
        self.assertTrue(configured['readiness']['ready'])
        self.assertEqual(configured['status'], 'Setup')
        self.assertEqual(self.admin.call(endpoint + '/activate', decision)[0], 409)
        decision['revision'] = configured['revision']
        self.assertEqual(self.admin.call(endpoint + '/activate', {**decision, 'reviewed': 'true'})[0], 400)
        status, result = self.admin.call(endpoint + '/activate', decision)
        self.assertEqual(status, 200)
        self.assertEqual(result['record']['status'], 'Recruiting')
        self.assertEqual(result['record']['activated_by'], 'demo:admin')
        self.assertEqual(self.admin.call(endpoint + '/activate', decision)[0], 409)
        self.assertEqual(self.admin.call(endpoint + '/setup', self.setup_payload(result['record']))[0], 409)
        self.assertEqual(self.admin.call('/api/enrolments', self.enrol(study_id=study['id'], consent_version='P-3'))[0], 409)
        self.assertEqual(self.admin.call('/api/enrolments', self.enrol(study_id=study['id'], consent_version='ICF-2'))[0], 200)
        ledger = self.admin.call('/api/audit')[1]
        activations = [e for e in ledger['entries'] if e['entity'] == study['id'] and e['action'] == 'STUDY_ACTIVATED']
        self.assertEqual(len(activations), 1)
        self.assertEqual(activations[0]['before']['status'], 'Setup')
        self.assertEqual(activations[0]['after']['status'], 'Recruiting')
        self.assertEqual(activations[0]['reason'], decision['reason'])
        self.assertTrue(ledger['verification']['valid'])
        server.initialize()
        reloaded = next(s for s in self.admin.call('/api/data')[1]['studies'] if s['id'] == study['id'])
        self.assertEqual(reloaded['status'], 'Recruiting')
        self.assertEqual(reloaded['consent_version'], 'ICF-2')

    def test_14_setup_validation_and_readiness_blockers(self):
        study = self.new_study(formulation='Pending')
        endpoint = '/api/studies/' + study['id']
        before = self.admin.call('/api/audit')[1]['verification']['entries']
        for changes in [{'registered_at': '2026-02-30'}, {'start': '2026-9-1'}, {'end': '2020-01-01'}, {'iec_expiry': '2020-01-01'}, {'reason': ''}, {'revision': True}]:
            self.assertEqual(self.admin.call(endpoint + '/setup', self.setup_payload(study, **changes))[0], 400)
        self.assertEqual(self.admin.call('/api/audit')[1]['verification']['entries'], before)
        status, corrected = self.admin.call(endpoint + '/setup', self.setup_payload(study))
        self.assertEqual(status, 200)
        study = corrected['record']
        self.assertTrue(study['readiness']['ready'])
        self.assertEqual(study['formulation'], 'Reviewed fictional formulation')
        future = (server.utcnow() + timedelta(days=1)).date().isoformat()
        for changes, blocked_key in [({'ctri': 'REF/2026/123'}, 'registration'), ({'registered_at': future}, 'registration'), ({'iec_reference': '', 'iec_approved_at': '', 'iec_expiry': ''}, 'ethics'), ({'iec_approved_at': future}, 'ethics'), ({'pi': ''}, 'investigator'), ({'batch': ''}, 'product'), ({'start': future}, 'period')]:
            status, result = self.admin.call(endpoint + '/setup', self.setup_payload(study, **changes))
            self.assertEqual(status, 200)
            study = result['record']
            self.assertFalse(study['readiness']['ready'])
            self.assertFalse(next(c for c in study['readiness']['checks'] if c['key'] == blocked_key)['passed'])
            self.assertEqual(self.admin.call(endpoint + '/activate', {'revision': study['revision'], 'reviewed': True, 'reason': 'Blocked proof'})[0], 409)
            self.assertEqual(self.admin.call('/api/data')[0], 200)

    def test_15_setup_permissions_and_stale_updates(self):
        study = self.new_study()
        endpoint = '/api/studies/' + study['id']
        payload = self.setup_payload(study)
        for role in ['regulator', 'pi', 'coordinator']:
            client = Client(self.base).login(role)
            self.assertEqual(client.call(endpoint + '/setup', payload)[0], 403)
            self.assertEqual(client.call(endpoint + '/activate', {'revision': study['revision'], 'reviewed': True, 'reason': 'Unauthorised attempt'})[0], 403)
        self.assertEqual(self.admin.call(endpoint + '/setup', payload)[0], 200)
        self.assertEqual(self.admin.call(endpoint + '/setup', {**payload, 'pi': 'Stale overwrite'})[0], 409)
        stored = next(s for s in self.admin.call('/api/data')[1]['studies'] if s['id'] == study['id'])
        self.assertEqual(stored['pi'], payload['pi'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
