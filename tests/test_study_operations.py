"""Site/monitoring/deviation workflow, migration, scope and forecast regression proof."""
import json
import math
from datetime import timedelta
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server
import study_operations as operations
from test_api import Client


class OperationsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_db = server.DB
        cls.httpd = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.base = 'http://127.0.0.1:' + str(cls.httpd.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        server.DB = cls.original_db

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        server.DB = Path(self.temp.name) / 'operations.sqlite'
        server.initialize()
        self.admin = Client(self.base).login('admin')
        self.today = server.utcnow().date()

    def create_site(self, **overrides):
        return self.admin.call('/api/sites', {'study_id': 'AIIA-001', 'code': 'NORTH',
            'name': 'Synthetic north site', 'city': 'Delhi', 'investigator': 'Synthetic PI',
            'target': 10, 'status': 'Setup', 'reason': 'Recorded site review', **overrides})

    def enrol(self, site_id):
        return self.admin.call('/api/enrolments', {'study_id': 'AIIA-001', 'site_id': site_id,
            'age': 35, 'sex': 'F', 'prakriti': 'Not assessed', 'consent': True,
            'consent_version': '2.1', 'consent_language': 'English'})

    def plan(self, **overrides):
        return self.admin.call('/api/monitoring-visits', {'study_id': 'AIIA-001',
            'site_id': 'SITE-AIIA-001', 'scheduled_date': self.today.isoformat(),
            'scope': 'Synthetic consent review', 'monitor': 'Synthetic monitor',
            'reason': 'Risk review schedule', **overrides})

    def deviation(self, **overrides):
        return self.admin.call('/api/deviations', {'study_id': 'AIIA-001', 'site_id': 'SITE-AIIA-001',
            'participant_id': 'SYN-01-003', 'category': 'Major', 'summary': 'Synthetic missed window',
            'occurred_date': self.today.isoformat(), 'owner': 'Coordinator', 'reason': 'Source verified', **overrides})

    def test_site_activation_and_enrolment_cannot_bypass_study_or_consent(self):
        status, response = self.create_site()
        self.assertEqual(status, 200)
        site = response['record']['id']
        self.assertEqual(self.enrol(site)[0], 409)
        self.assertEqual(self.create_site()[0], 409)
        self.assertEqual(self.admin.call('/api/sites/'+site+'/activate', {'reason': 'Reviewed site'})[0], 200)
        self.assertEqual(self.admin.call('/api/sites/'+site+'/activate', {'reason': 'Again'})[0], 409)
        status, response = self.enrol(site)
        self.assertEqual(status, 200)
        self.assertEqual(response['record']['site_id'], site)
        self.assertEqual(self.enrol(None)[1]['record']['site_id'], 'SITE-AIIA-001')
        self.assertEqual(self.enrol('SITE-AIIA-002')[0], 409)
        self.assertEqual(self.create_site(study_id='AIIA-004', status='Active')[0], 409)
        with server.connect() as conn:
            study = server.get(conn, 'studies', 'AIIA-001')
            study['iec_expiry'] = (self.today-timedelta(days=1)).isoformat()
            server.save(conn, 'studies', study)
        self.assertEqual(self.enrol(site)[0], 409)

    def test_monitoring_chronology_completion_and_audit(self):
        status, result = self.plan()
        self.assertEqual(status, 200)
        endpoint = '/api/monitoring-visits/'+result['record']['id']+'/complete'
        payload = {'findings': 'Reviewed source; follow-up documented.', 'reason': 'Visit completed'}
        self.assertEqual(self.admin.call(endpoint, payload)[0], 200)
        self.assertEqual(self.admin.call(endpoint, payload)[0], 409)
        future = self.plan(scheduled_date=(self.today+timedelta(days=2)).isoformat())[1]['record']['id']
        self.assertEqual(self.admin.call('/api/monitoring-visits/'+future+'/complete', payload)[0], 409)
        self.assertEqual(self.plan(site_id='SITE-AIIA-002')[0], 409)
        audit = self.admin.call('/api/audit')[1]
        self.assertTrue(audit['verification']['valid'])
        event = next(e for e in audit['entries'] if e['action'] == 'MONITORING_VISIT_COMPLETED')
        self.assertEqual(event['before']['status'], 'Planned')
        self.assertEqual(event['after']['findings'], payload['findings'])

    def test_deviation_linkage_future_date_closure_and_rollback(self):
        site = self.create_site()[1]['record']['id']
        for extra in ({'site_id': site}, {'participant_id': 'SYN-02-004'},
                      {'occurred_date': (self.today+timedelta(days=1)).isoformat()}, {'reason': ''}):
            self.assertIn(self.deviation(**extra)[0], (400, 409))
        self.assertEqual(len(self.admin.call('/api/data')[1]['deviations']), 3)
        record = self.deviation()[1]['record']
        endpoint = '/api/deviations/'+record['id']+'/close'
        payload = {'reason': 'Independent operational review recorded', 'corrective_action': 'Corrected source and retrained team'}
        self.assertEqual(self.admin.call(endpoint, payload)[0], 200)
        self.assertEqual(self.admin.call(endpoint, payload)[0], 409)

    def test_query_create_resolve_and_age_threshold_alerts(self):
        payload = {'study_id': 'AIIA-001', 'field': 'Consent record', 'message': 'Synthetic discrepancy', 'reason': 'Review'}
        status, response = self.admin.call('/api/queries', payload)
        self.assertEqual(status, 200)
        ident = response['record']['id']
        settings = {'enrolment_threshold': 70, 'iec_days': 30, 'query_days': 1, 'monitoring_days': 1, 'deviation_days': 1}
        self.assertEqual(self.admin.call('/api/settings', settings)[0], 200)
        alerts = self.admin.call('/api/data')[1]['alerts']
        self.assertTrue(any(a['page'] == 'queries' for a in alerts))
        self.assertTrue(any('deviation open' in a['title'] for a in alerts))
        self.assertFalse(any('due in 8 days' in a['title'] for a in alerts))
        self.assertEqual(self.admin.call('/api/queries/'+ident+'/resolve', {'resolution': 'Source reconciled'})[0], 200)
        self.assertEqual(self.admin.call('/api/settings', {**settings, 'monitoring_days': True})[0], 400)

    def test_scope_readonly_and_leadership_redaction(self):
        self.deviation(summary='PRIVATE_MARKER', owner='PRIVATE_OWNER', occurred_date=(self.today-timedelta(days=14)).isoformat())
        pi = Client(self.base).login('pi')
        snapshot = pi.call('/api/data')[1]
        for key in ('sites', 'monitoring_visits', 'deviations', 'forecasts', 'batch_context'):
            self.assertTrue(all(r['study_id'] in ['AIIA-001','AIIA-002'] for r in snapshot[key]))
        self.assertEqual(pi.call('/api/operations/inspection?study=AIIA-003')[0], 403)
        regulator = Client(self.base).login('regulator')
        self.assertEqual(regulator.call('/api/deviations/DEV-001/close', {'reason': 'x','corrective_action':'x'})[0], 403)
        leadership = Client(self.base).login('leadership')
        data = leadership.call('/api/data')[1]
        self.assertEqual(data['deviations'], [])
        self.assertNotIn('PRIVATE_MARKER', json.dumps(data))
        self.assertNotIn('PRIVATE_OWNER', json.dumps(data))
        report = leadership.call('/api/operations/inspection')[1]
        self.assertGreater(report['checks']['open_deviations'], 0)
        self.assertIsNone(report['audit'])

    def test_inspection_counts_saved_records_with_scope(self):
        report = self.admin.call('/api/operations/inspection?study=AIIA-001')[1]
        self.assertEqual(report['study_ids'], ['AIIA-001'])
        self.assertEqual(report['checks']['open_deviations'], 1)
        self.assertEqual(report['current_consent'], {'active':38,'current':38})
        self.assertTrue(report['audit']['valid'])
        self.admin.call('/api/participants/SYN-01-003/withdraw', {'reason':'Synthetic withdrawal'})
        report = self.admin.call('/api/operations/inspection?study=AIIA-001')[1]
        self.assertEqual(report['current_consent'], {'active':37,'current':37})
        self.assertEqual(self.admin.call('/api/operations/inspection?study=UNKNOWN')[0], 404)

    def test_migration_preserves_original_records_and_is_idempotent(self):
        with server.connect() as conn:
            before = {table: [tuple(row) for row in conn.execute('SELECT * FROM '+table)] for table in ('participants','studies','events')}
            conn.execute('DELETE FROM sites')
            conn.execute('DELETE FROM monitoring_visits')
            conn.execute('DELETE FROM deviations')
        server.initialize()
        with server.connect() as conn:
            for table, expected in before.items():
                self.assertEqual(expected, [tuple(row) for row in conn.execute('SELECT * FROM '+table)])
            self.assertEqual(len(server.rows(conn, 'sites')), 6)
            self.assertEqual(server.rows(conn, 'monitoring_visits'), [])
            self.assertEqual(server.rows(conn, 'deviations'), [])
            head = server.verify_audit(conn)['head']
        server.initialize()
        with server.connect() as conn:
            self.assertEqual(server.verify_audit(conn)['head'], head)

    def test_batch_context_does_not_invent_exposure_or_signal(self):
        data = self.admin.call('/api/data')[1]['batch_context']
        row = next(b for b in data if b['study_id']=='AIIA-001')
        self.assertEqual(row['participants_with_events'], 3)
        self.assertEqual(row['serious_events'], 2)
        self.assertNotIn('prr', row)
        self.assertNotIn('exposed', row)
        self.assertNotIn('AIIA-003', {b['study_id'] for b in data})

    def test_predictive_probability_and_interval_math(self):
        probability, interval = operations._predictive(1, 14, 14, 3)
        self.assertAlmostEqual(probability, .125, places=12)  # geometric P(N >= 3)
        self.assertEqual(interval, [0, 4])
        self.assertEqual(operations._predictive(1,14,0,1), (0.0,[0,0]))
        self.assertEqual(operations._predictive(1,14,0,0), (1.0,[0,0]))
        probability, interval = operations._predictive(1500, 56, 56, 1500)
        self.assertTrue(.45 < probability < .55)  # initial PMF underflows; distribution still recovered
        self.assertTrue(interval[0] < 1500 < interval[1])

    def test_forecast_excludes_future_data_and_reports_display_limit(self):
        study = {'id':'X','start':(self.today-timedelta(days=100)).isoformat(),
                 'end':(self.today+timedelta(days=30)).isoformat(),'target':10000}
        future = [{'study_id':'X','enrolled_at':(self.today+timedelta(days=1)).isoformat()}]
        forecast = operations._forecast(study, future, self.today)
        self.assertEqual(forecast['enrolled'], 0)
        self.assertEqual(forecast['observed_days'], 56)
        self.assertIsNone(forecast['projected_completion'])
        self.assertTrue(math.isfinite(forecast['target_probability_raw']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
