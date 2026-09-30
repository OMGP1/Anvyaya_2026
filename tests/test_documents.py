"""Transaction-level evidence and amendment tests using isolated synthetic data."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as core
import documents


def principal(user_id, role='admin', scope=None):
    permissions = {
        'admin': ['document', 'review', 'amend', 'enrol'],
        'pi': ['document', 'amend', 'enrol'],
        'ethics': ['review'],
        'coordinator': ['document', 'enrol'],
        'leadership': [],
    }
    return {'user_id': user_id, 'name': user_id or 'Shared demonstration', 'role': role,
            'permissions': permissions[role], 'scope': scope}


class DocumentWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_db = core.DB
        core.DB = Path(self.temp.name) / 'documents.sqlite'
        core.initialize()
        with core.connect() as conn:
            for table in ('documents', 'amendments'):
                conn.execute(f'CREATE TABLE IF NOT EXISTS {table}(id TEXT PRIMARY KEY, data TEXT NOT NULL)')
        self.author = principal('USER-AUTHOR', 'pi', ['AIIA-001'])
        self.reviewer = principal('USER-REVIEWER', 'ethics', ['AIIA-001'])
        self.admin = principal('USER-ADMIN')

    def tearDown(self):
        core.DB = self.original_db
        self.temp.cleanup()

    def mutate(self, who, path, data):
        with core.connect() as conn:
            return documents.mutate(core, conn, who, path, data)

    def upload(self, kind='Protocol', version='3.0', **extra):
        data = {'study_id': 'AIIA-001', 'kind': kind, 'version': version,
                'filename': kind.lower() + '.txt',
                'content_base64': base64.b64encode(b'Synthetic evidence for workflow testing.').decode()}
        data.update(extra)
        return self.mutate(self.author, '/api/documents', data)['record']

    def approve_document(self, document):
        return self.mutate(self.reviewer, '/api/documents/' + document['id'] + '/review',
                           {'decision': 'Approved', 'reason': 'Checked the synthetic test evidence.'})['record']

    def amendment_data(self, version='3.0'):
        result = {'study_id': 'AIIA-001', 'iec_reference': 'DEMO-IEC-AMENDMENT',
                  'iec_approved_at': core.utcnow().date().isoformat(),
                  'iec_expiry': (core.utcnow() + timedelta(days=180)).date().isoformat(),
                  'target': 65, 'reason': 'Synthetic protocol and consent update.'}
        for kind in documents.KINDS:
            document = self.approve_document(self.upload(kind, version))
            result[kind.lower() + '_document_id'] = document['id']
        return result

    def expect_error(self, status, who, path, data):
        with self.assertRaises(core.ApiError) as raised:
            self.mutate(who, path, data)
        self.assertEqual(status, raised.exception.status)

    def test_document_metadata_integrity_independent_review_and_persistence(self):
        document = self.upload()
        self.assertNotIn('content_base64', document)
        self.assertEqual(hashlib.sha256(b'Synthetic evidence for workflow testing.').hexdigest(), document['sha256'])
        with core.connect() as conn:
            stored = documents.get_document(core, conn, self.author, document['id'])
            self.assertIn('content_base64', stored)
            self.assertNotIn('content_base64', json.dumps(documents.list_documents(core, conn, self.author)))
        review = {'decision': 'Approved', 'reason': 'Independent review.'}
        self.expect_error(403, self.author, '/api/documents/' + document['id'] + '/review', review)
        # An administrator who uploaded evidence cannot approve their own version.
        self_author_admin = {**self.admin, 'user_id': self.author['user_id']}
        self.expect_error(403, self_author_admin, '/api/documents/' + document['id'] + '/review', review)
        approved = self.approve_document(document)
        self.assertEqual('Approved', approved['status'])
        self.assertEqual(self.reviewer['user_id'], approved['reviewed_by'])
        self.expect_error(409, self.reviewer, '/api/documents/' + document['id'] + '/review', review)
        with core.connect() as conn:
            self.assertEqual('Approved', core.get(conn, 'documents', document['id'])['status'])
            self.assertNotIn('content_base64', '\n'.join(row['payload'] for row in conn.execute('SELECT payload FROM audit')))
            self.assertTrue(core.verify_audit(conn)['valid'])

    def test_named_account_scope_and_immutable_versions(self):
        payload = {'study_id': 'AIIA-001', 'kind': 'Protocol', 'version': '3.0',
                   'filename': 'protocol.txt', 'content_base64': base64.b64encode(b'Test').decode()}
        self.expect_error(403, principal(None), '/api/documents', payload)
        self.expect_error(403, principal('OUTSIDE', 'pi', ['AIIA-002']), '/api/documents', payload)
        document = self.upload()
        self.expect_error(409, self.author, '/api/documents', payload)
        with core.connect() as conn:
            self.assertEqual([], documents.list_documents(core, conn, principal('OUTSIDE', 'pi', ['AIIA-002'])))
            self.assertEqual([], documents.list_documents(core, conn, principal('LEADER', 'leadership')))
            for who in (principal('OUTSIDE', 'pi', ['AIIA-002']), principal('LEADER', 'leadership')):
                with self.assertRaises(core.ApiError) as raised:
                    documents.get_document(core, conn, who, document['id'])
                self.assertEqual(403, raised.exception.status)

    def test_file_signatures_paths_size_encoding_and_rejection(self):
        invalid = [
            ('../protocol.txt', base64.b64encode(b'Test').decode()),
            ('protocol.exe', base64.b64encode(b'Test').decode()),
            ('protocol.pdf', base64.b64encode(b'This is not a PDF').decode()),
            ('protocol.pdf', base64.b64encode(b'%PDF-1.7\nunterminated').decode()),
            ('protocol.txt', base64.b64encode(b'%PDF-1.7\n%%EOF').decode()),
            ('protocol.txt', base64.b64encode(b'bad\x00text').decode()),
            ('protocol.txt', base64.b64encode(b'\xff\xfe').decode()),
            ('protocol.txt', '*invalid*'),
            ('protocol.txt', ''),
            ('protocol.txt', base64.b64encode(b'x' * (documents.MAX_FILE_BYTES + 1)).decode()),
        ]
        for filename, content in invalid:
            with self.subTest(filename=filename, length=len(content)):
                self.expect_error(400, self.author, '/api/documents', {
                    'study_id': 'AIIA-001', 'kind': 'Protocol', 'version': '3.0',
                    'filename': filename, 'content_base64': content})
        document = self.upload(filename='protocol.pdf', content_base64=base64.b64encode(b'%PDF-1.7\nSynthetic test signature\n%%EOF\n').decode())
        self.assertEqual('application/pdf', document['media_type'])
        rejected = self.mutate(self.reviewer, '/api/documents/' + document['id'] + '/review',
                               {'decision': 'Rejected', 'reason': 'Signature check is insufficient for approval.'})['record']
        self.assertEqual('Rejected', rejected['status'])
        self.expect_error(409, self.reviewer, '/api/documents/' + document['id'] + '/review', {'decision': 'Approved', 'reason': 'Retry'})

    def test_amendment_reconsent_preserves_history_and_audit(self):
        data = self.amendment_data()
        proposal = self.mutate(self.author, '/api/amendments', data)['record']
        with core.connect() as conn:
            before = core.get(conn, 'participants', 'SYN-01-001')
            self.assertEqual('2.1', core.get(conn, 'studies', 'AIIA-001')['consent_version'])
            withdrawn = core.get(conn, 'participants', 'SYN-01-002')
            withdrawn.update(status='Withdrawn', consent=False)
            core.save(conn, 'participants', withdrawn)
        result = self.mutate(self.reviewer, '/api/amendments/' + proposal['id'] + '/approve', {'reason': 'Independent approval of recorded amendment evidence.'})
        self.assertEqual(37, result['reconsent_count'])
        self.assertEqual(2, result['study']['revision'])
        with core.connect() as conn:
            participant = core.get(conn, 'participants', 'SYN-01-001')
            self.assertTrue(participant['reconsent_required'])
            self.assertEqual(before['consent_version'], participant['consent_version'])
            self.assertEqual(before['consent_at'], participant['consent_at'])
            self.assertFalse(core.get(conn, 'participants', 'SYN-01-002').get('reconsent_required', False))
        updated = self.mutate(self.author, '/api/participants/SYN-01-001/reconsent', {
            'consent': True, 'consent_version': '3.0', 'consent_language': 'Hindi',
            'reason': 'Recorded consent after discussing the approved revised information.'})['record']
        self.assertFalse(updated['reconsent_required'])
        self.assertEqual('3.0', updated['consent_version'])
        self.assertEqual(before['consent_at'], updated['consent_history'][0]['consent_at'])
        self.assertEqual('2.1', updated['consent_history'][0]['consent_version'])
        self.assertEqual(self.author['user_id'], updated['consent_recorder'])
        with core.connect() as conn:
            self.assertTrue(core.verify_audit(conn)['valid'])
            actions = [json.loads(row['payload'])['action'] for row in conn.execute('SELECT payload FROM audit')]
            self.assertIn('STUDY_AMENDED', actions)
            self.assertIn('PARTICIPANT_RECONSENTED', actions)
        self.expect_error(409, self.author, '/api/participants/SYN-01-001/reconsent', {'consent': True, 'consent_version': '3.0', 'consent_language': 'Hindi', 'reason': 'Retry'})

    def test_amendment_authorization_revision_and_duplicate_approval(self):
        data = self.amendment_data()
        self.expect_error(403, principal(None), '/api/amendments', data)
        self.expect_error(403, self.reviewer, '/api/amendments', data)
        proposal = self.mutate(self.author, '/api/amendments', data)['record']
        path = '/api/amendments/' + proposal['id'] + '/approve'
        self_author_admin = {**self.admin, 'user_id': self.author['user_id']}
        self.expect_error(403, self_author_admin, path, {'reason': 'Self approval'})
        self.expect_error(403, principal(None), path, {'reason': 'Shared approval'})
        with core.connect() as conn:
            study = core.get(conn, 'studies', 'AIIA-001')
            study['revision'] += 1
            core.save(conn, 'studies', study)
        self.expect_error(409, self.reviewer, path, {'reason': 'Stale approval'})
        replacement = self.mutate(self.author, '/api/amendments', data)['record']
        path = '/api/amendments/' + replacement['id'] + '/approve'
        self.mutate(self.reviewer, path, {'reason': 'Current reviewed amendment'})
        self.expect_error(409, self.reviewer, path, {'reason': 'Duplicate approval'})

    def test_amendment_evidence_date_capacity_and_effective_gates(self):
        data = self.amendment_data()
        bad = copy.deepcopy(data)
        bad['protocol_document_id'] = data['consent_document_id']
        self.expect_error(400, self.author, '/api/amendments', bad)
        bad = {**data, 'target': 37}
        self.expect_error(409, self.author, '/api/amendments', bad)
        bad = {**data, 'iec_expiry': '2020-01-01'}
        self.expect_error(400, self.author, '/api/amendments', bad)
        bad = {**data, 'iec_approved_at': '2026-02-30'}
        self.expect_error(400, self.author, '/api/amendments', bad)
        unreviewed = self.upload('Protocol', '4.0')
        self.expect_error(409, self.author, '/api/amendments', {**data, 'protocol_document_id': unreviewed['id']})
        future = {**data, 'iec_approved_at': (core.utcnow() + timedelta(days=7)).date().isoformat()}
        proposal = self.mutate(self.author, '/api/amendments', future)['record']
        with core.connect() as conn:
            audit_count = core.verify_audit(conn)['entries']
        self.expect_error(409, self.reviewer, '/api/amendments/' + proposal['id'] + '/approve', {'reason': 'Too early'})
        with core.connect() as conn:
            self.assertEqual(audit_count, core.verify_audit(conn)['entries'])
            self.assertEqual('2.1', core.get(conn, 'studies', 'AIIA-001')['protocol'])
            self.assertFalse(core.get(conn, 'participants', 'SYN-01-001').get('reconsent_required', False))

    def test_reconsent_requires_current_version_confirmation_and_active_participant(self):
        data = self.amendment_data()
        proposal = self.mutate(self.author, '/api/amendments', data)['record']
        self.mutate(self.reviewer, '/api/amendments/' + proposal['id'] + '/approve', {'reason': 'Independent amendment review'})
        path = '/api/participants/SYN-01-001/reconsent'
        valid = {'consent': True, 'consent_version': '3.0', 'consent_language': 'English', 'reason': 'Recorded discussion'}
        self.expect_error(409, self.author, path, {**valid, 'consent_version': '2.1'})
        self.expect_error(400, self.author, path, {**valid, 'consent': 'true'})
        self.expect_error(400, self.author, path, {**valid, 'consent_language': 'Unknown'})
        self.expect_error(403, self.reviewer, path, valid)
        self.expect_error(403, principal('OUTSIDE', 'pi', ['AIIA-002']), path, valid)
        with core.connect() as conn:
            participant = core.get(conn, 'participants', 'SYN-01-001')
            participant.update(status='Withdrawn', consent=False)
            core.save(conn, 'participants', participant)
        self.expect_error(409, self.author, path, valid)


if __name__ == '__main__':
    unittest.main(verbosity=2)
