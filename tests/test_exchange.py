"""HTTP exchange regression tests; each test owns a fresh temporary database."""
import copy
import csv
import hashlib
import io
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from datetime import timedelta
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import exchange
import server
from test_api import Client


class QuietHandler(server.Handler):
    def log_message(self, *_args):
        pass


class ExchangeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        for key, value in [('DB', Path(temporary.name) / 'exchange.sqlite'), ('DEMO_LOGIN', True), ('SECURE_COOKIE', False)]:
            change = patch.object(server, key, value)
            change.start()
            self.addCleanup(change.stop)
        server.SESSIONS.clear()
        server.ATTEMPTS.clear()
        with patch.dict(os.environ, {'CTMS_ADMIN_PASSWORD': ''}):
            server.initialize()
        self.httpd = server.ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
        thread = threading.Thread(target=lambda: self.httpd.serve_forever(poll_interval=0.01), daemon=True)
        thread.start()

        def stop():
            self.httpd.shutdown()
            self.httpd.server_close()
            thread.join(timeout=5)

        self.addCleanup(stop)
        self.base = f'http://127.0.0.1:{self.httpd.server_port}'
        self.admin = Client(self.base).login('admin')

    def row(self, ident='EXT-001', **changes):
        return {'external_id': ident, 'age': '35', 'sex': 'F', 'prakriti': 'Not assessed',
                'consent_version': '2.1', 'consent_language': 'English', 'consent_confirmed': 'true', **changes}

    def csv_text(self, *records, fields=None):
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=fields or exchange.FIELDS)
        writer.writeheader()
        writer.writerows(records or [self.row()])
        return stream.getvalue()

    def preview(self, client=None, records=None, **changes):
        payload = {'study_id': 'AIIA-001', 'source_name': 'Synthetic EDC',
                   'csv_text': self.csv_text(*(records or [self.row()])), 'synthetic': True, **changes}
        return (client or self.admin).call('/api/imports/preview', payload)

    def job(self, **changes):
        status, result = self.preview(**changes)
        self.assertEqual(status, 200, result)
        return result['record']

    def commit(self, job, client=None, **changes):
        return (client or self.admin).call(f'/api/imports/{job["id"]}/commit',
                                          {'reviewed': True, 'reason': 'Synthetic source reviewed', **changes})

    def counts(self):
        with server.connect() as conn:
            return {table: conn.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
                    for table in ['participants', 'visits', 'audit']}

    def participant(self, ident):
        with server.connect() as conn:
            return server.get(conn, 'participants', ident)

    def edit_study(self, **changes):
        with server.connect() as conn:
            study = server.get(conn, 'studies', 'AIIA-001')
            original = copy.deepcopy(study)
            study.update(changes)
            server.save(conn, 'studies', study)
            return original

    def test_valid_import_persists_visits_audit_exact_source_hash_and_lineage(self):
        text = self.csv_text(self.row())
        started = server.stamp()
        before = self.counts()
        job = self.job(csv_text=text)
        self.assertEqual((job['ready'], job['rejected'], job['duplicates']), (1, 0, 0))
        self.assertEqual(self.counts()['participants'], before['participants'])
        self.assertEqual(job['source_sha256'], hashlib.sha256(text.encode()).hexdigest())
        status, result = self.commit(job)
        self.assertEqual(status, 200, result)
        committed = result['record']
        self.assertEqual((committed['status'], committed['inserted']), ('Committed', 1))
        self.assertFalse(result['idempotent'])
        pid = committed['rows'][0]['participant_id']
        participant = self.participant(pid)
        provenance = participant['provenance']
        self.assertEqual(provenance['import_id'], job['id'])
        self.assertEqual(provenance['external_id'], 'EXT-001')
        self.assertEqual(provenance['source_sha256'], hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(provenance['row_sha256'], hashlib.sha256(server.canonical(self.row()).encode()).hexdigest())
        self.assertTrue(provenance['synthetic'])
        self.assertLessEqual(started, participant['enrolled_at'])
        self.assertLessEqual(participant['enrolled_at'], server.stamp())
        self.assertLessEqual(started, participant['consent_at'])
        self.assertLessEqual(participant['consent_at'], participant['enrolled_at'])
        counts = self.counts()
        self.assertEqual(counts['participants'], before['participants'] + 1)
        self.assertEqual(counts['visits'], before['visits'] + 2)
        self.assertEqual(counts['audit'], before['audit'] + 4)
        with server.connect() as conn:
            self.assertEqual(len([v for v in server.rows(conn, 'visits') if v['participant_id'] == pid]), 2)
            self.assertTrue(server.verify_audit(conn)['valid'])
        ledger = self.admin.call('/api/audit')[1]['entries']
        self.assertTrue({'IMPORT_PREVIEWED', 'PARTICIPANT_ENROLLED', 'SOURCE_RECONCILED', 'IMPORT_COMMITTED'}
                        <= {e['action'] for e in ledger if e['entity'] in [pid, job['id']]})
        status, detail = self.admin.call(f'/api/imports/{job["id"]}')
        self.assertEqual(status, 200)
        self.assertEqual(detail['record'], committed)
        listing = self.admin.call('/api/data')[1]['imports']
        self.assertEqual(len(listing), 1)
        self.assertNotIn('rows', listing[0])
        self.assertNotIn('EXT-001', str(listing))

    def test_repeat_commit_and_repeat_source_are_idempotent(self):
        job = self.job()
        status, first = self.commit(job)
        self.assertEqual(status, 200)
        before = self.counts()
        status, repeat = self.commit(job)
        self.assertEqual(status, 200)
        self.assertTrue(repeat['idempotent'])
        self.assertEqual(repeat['record'], first['record'])
        self.assertEqual(before, self.counts())
        duplicate = self.job(source_name='SYNTHETIC EDC')
        self.assertEqual((duplicate['ready'], duplicate['duplicates']), (0, 1))
        status, result = self.commit(duplicate)
        self.assertEqual(status, 200)
        self.assertEqual(result['record']['inserted'], 0)
        self.assertEqual(result['record']['rows'][0]['participant_id'], first['record']['rows'][0]['participant_id'])
        self.assertEqual(self.counts()['participants'], before['participants'])
        self.assertEqual(self.counts()['visits'], before['visits'])

    def test_changed_source_payload_is_rejected_at_preview_and_commit(self):
        original = self.job()
        raced = self.job(records=[self.row(age='36')])
        self.assertEqual(self.commit(original)[0], 200)
        before = self.counts()
        self.assertEqual(self.commit(raced)[0], 409)
        self.assertEqual(before, self.counts())
        stale = self.admin.call(f'/api/imports/{raced["id"]}')[1]['record']
        self.assertEqual(stale['status'], 'Preview')
        changed = self.job(records=[self.row(age='37')])
        self.assertEqual(changed['rejected'], 1)
        self.assertIn('different values', changed['rows'][0]['error'])
        before = self.counts()
        self.assertEqual(self.commit(changed)[0], 409)
        self.assertEqual(before, self.counts())

    def test_parser_and_mapping_reject_malformed_requests_without_writes(self):
        invalid_mappings = [{}, [], False, '', {'external_id': 'external_id'},
                            {key: 'same' for key in exchange.FIELDS},
                            {**{key: key for key in exchange.FIELDS}, 'age': 7}]
        cases = [{'mapping': mapping} for mapping in invalid_mappings]
        cases += [{'synthetic': value} for value in [False, 'true', None]]
        cases += [{'csv_text': ','.join([*exchange.FIELDS, 'age']) + '\n' + ','.join([*self.row().values(), '35'])},
                  {'csv_text': 'external_id,age\nEXT-1,35'},
                  {'csv_text': ','.join(exchange.FIELDS)},
                  {'csv_text': ','.join(exchange.FIELDS) + '\n"unterminated'},
                  {'csv_text': self.csv_text(*[self.row(f'ID-{i}') for i in range(101)])}]
        for changes in cases:
            with self.subTest(changes=changes):
                before = self.counts()
                status, result = self.preview(**changes)
                self.assertEqual(status, 400, result)
                self.assertEqual(before, self.counts())
        mapping = {key: 'source_' + key for key in exchange.FIELDS}
        row = {mapping[key]: value for key, value in self.row().items()}
        job = self.job(mapping=mapping, csv_text=self.csv_text(row, fields=list(mapping.values())))
        self.assertEqual(job['ready'], 1)
        self.assertEqual(self.commit(job)[0], 200)

    def test_rejected_rows_prevent_entire_batch_commit(self):
        for changes in [{'external_id': '=bad'}, {'age': '17'}, {'age': '1.5'}, {'sex': 'invalid'},
                        {'prakriti': 'Invented'}, {'consent_language': 'Unknown'},
                        {'consent_confirmed': 'false'}, {'consent_version': 'old'}, {'consent_version': ''}]:
            with self.subTest(changes=changes):
                job = self.job(records=[self.row('GOOD'), self.row('BAD', **changes)])
                self.assertGreater(job['rejected'], 0)
                before = self.counts()
                self.assertEqual(self.commit(job)[0], 409)
                self.assertEqual(before, self.counts())
        job = self.job(records=[self.row(), self.row()])
        self.assertEqual(job['rejected'], 1)
        self.assertIn('Duplicate', job['rows'][1]['error'])
        self.assertEqual(self.commit(job)[0], 409)
        for text in [self.csv_text() + 'ID-2,35\n', self.csv_text().rstrip() + ',EXTRA\n']:
            job = self.job(csv_text=text)
            self.assertGreater(job['rejected'], 0)
            self.assertEqual(self.commit(job)[0], 409)

    def test_commit_requires_review_and_rechecks_changed_study_evidence(self):
        job = self.job()
        for payload in [{'reviewed': False}, {'reviewed': 'true'}, {'reason': ''}]:
            before = self.counts()
            self.assertEqual(self.commit(job, **payload)[0], 400)
            self.assertEqual(before, self.counts())
        expiry = (server.utcnow() - timedelta(days=1)).date().isoformat()
        for changes in [{'ctri': ''}, {'iec_expiry': expiry}, {'status': 'Follow-up'}, {'consent_version': '3.0'}]:
            with self.subTest(changes=changes):
                original = self.edit_study(**changes)
                before = self.counts()
                self.assertEqual(self.commit(job)[0], 409)
                self.assertEqual(before, self.counts())
                self.assertEqual(self.admin.call(f'/api/imports/{job["id"]}')[1]['record']['status'], 'Preview')
                with server.connect() as conn:
                    server.save(conn, 'studies', original)

    def test_capacity_failure_rolls_back_prior_rows_visits_audit_and_lineage(self):
        job = self.job(records=[self.row('FIRST'), self.row('SECOND')])
        with server.connect() as conn:
            enrolled = sum(p['study_id'] == 'AIIA-001' for p in server.rows(conn, 'participants'))
        self.edit_study(target=enrolled + 1)
        before = self.counts()
        status, result = self.commit(job)
        self.assertEqual(status, 409, result)
        self.assertIn('target reached', result['error'])
        self.assertEqual(before, self.counts())
        detail = self.admin.call(f'/api/imports/{job["id"]}')[1]['record']
        self.assertEqual(detail['status'], 'Preview')
        self.assertTrue(all(row['status'] == 'Ready' and 'participant_id' not in row for row in detail['rows']))
        with server.connect() as conn:
            self.assertFalse(any(p.get('provenance') for p in server.rows(conn, 'participants')))
            self.assertTrue(server.verify_audit(conn)['valid'])

    def test_reimport_cannot_reactivate_a_withdrawn_participant(self):
        job = self.job()
        pid = self.commit(job)[1]['record']['rows'][0]['participant_id']
        self.assertEqual(self.admin.call(f'/api/participants/{pid}/withdraw', {'reason': 'Synthetic withdrawal'})[0], 200)
        before = self.counts()
        duplicate = self.job()
        self.assertEqual(duplicate['duplicates'], 1)
        self.assertEqual(self.commit(duplicate)[1]['record']['inserted'], 0)
        participant = self.participant(pid)
        self.assertEqual(participant['status'], 'Withdrawn')
        self.assertFalse(participant['consent'])
        self.assertEqual(self.counts()['participants'], before['participants'])
        self.assertEqual(self.counts()['visits'], before['visits'])
        self.assertEqual(self.admin.call(f'/api/visits/{pid}-V1/complete', {'reason': 'Blocked after withdrawal'})[0], 409)

    def test_auth_permissions_scope_and_metadata_redaction(self):
        anonymous = Client(self.base)
        self.assertEqual(self.preview(client=anonymous)[0], 401)
        job = self.job()
        self.assertEqual(self.commit(job)[0], 200)
        outside = self.job(study_id='AIIA-003', records=[self.row('OUTSIDE-SECRET')])
        self.assertEqual(self.commit(outside)[0], 200)
        pi = Client(self.base).login('pi')
        self.assertEqual(self.preview(client=pi, study_id='AIIA-003')[0], 403)
        self.assertEqual(pi.call(f'/api/imports/{outside["id"]}')[0], 403)
        self.assertEqual(self.commit(outside, client=pi)[0], 403)
        listing = pi.call('/api/data')[1]['imports']
        self.assertEqual({j['id'] for j in listing}, {job['id']})
        self.assertTrue(all('rows' not in j for j in listing))
        status, exported = pi.call('/api/export/provenance')
        self.assertEqual(status, 200)
        self.assertNotIn(b'OUTSIDE-SECRET', exported)
        self.assertNotIn(b'AIIA-003', exported)
        for role in ['monitor', 'regulator', 'leadership', 'ethics', 'pv']:
            with self.subTest(role=role):
                client = Client(self.base).login(role)
                self.assertEqual(self.preview(client=client)[0], 403)
                self.assertEqual(self.commit(job, client=client)[0], 403)
                self.assertEqual(client.call(f'/api/imports/{job["id"]}')[0], 403)
                self.assertEqual(client.call('/api/data')[1]['imports'], [])
        coordinator = Client(self.base).login('coordinator')
        self.assertEqual(coordinator.call('/api/export/provenance')[0], 403)
        self.assertEqual(coordinator.call('/api/exchange/check')[0], 403)
        self.assertEqual(anonymous.call('/api/exchange/check')[0], 401)
        before = self.counts()
        self.assertEqual(self.admin.call('/api/imports/preview', {
            'study_id': 'AIIA-001', 'source_name': 'CSRF', 'csv_text': self.csv_text(), 'synthetic': True,
        }, {'X-CSRF-Token': 'wrong'})[0], 403)
        self.assertEqual(before, self.counts())

    def test_provenance_csv_escapes_formula_source_and_exports_exact_hash(self):
        text = self.csv_text(self.row())
        job = self.job(source_name='=SUM(1,2)', csv_text=text)
        committed = self.commit(job)[1]['record']
        status, raw = self.admin.call('/api/export/provenance')
        self.assertEqual(status, 200)
        records = list(csv.DictReader(io.StringIO(raw.decode())))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['source_name'], "'=SUM(1,2)")
        self.assertEqual(records[0]['source_sha256'], hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(records[0]['participant_id'], committed['rows'][0]['participant_id'])
        self.assertEqual(records[0]['import_id'], job['id'])

    def test_local_fhir_checks_detect_missing_reference_without_claiming_conformance(self):
        status, result = self.admin.call('/api/exchange/check')
        self.assertEqual(status, 200)
        self.assertTrue(result['passed'])
        self.assertIn('Local', result['scope'])
        self.assertIn('Official FHIR profile validation', result['scope'])
        self.assertGreater(result['resources'], 0)
        self.assertGreater(result['references'], 0)
        valid_bundle = self.admin.call('/api/export/fhir?study=AIIA-001')[1]
        invalid_bundle = copy.deepcopy(valid_bundle)
        subject = next(e['resource'] for e in invalid_bundle['entry'] if e['resource']['resourceType'] == 'ResearchSubject')
        subject['individual']['reference'] = 'https://invalid.example/Patient/missing'
        with patch.object(server, 'bundle', return_value=invalid_bundle):
            status, result = self.admin.call('/api/exchange/check')
        self.assertEqual(status, 200)
        self.assertFalse(result['passed'])
        checks = {check['name']: check['passed'] for check in result['checks']}
        self.assertFalse(checks['All local references resolve'])
        self.assertTrue(checks['Unique resource URLs'])


if __name__ == '__main__':
    unittest.main()
