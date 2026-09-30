"""Synthetic fixtures test terminology review and recipient reporting records."""
from datetime import timedelta
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as core
import safety_workflow as workflow


def principal(user_id='USR-ADMIN', role='admin', scope=None):
    return {**core.ROLES[role], 'user_id': user_id, 'name': user_id or 'Shared demonstration',
            'role': role, 'scope': scope}


class SafetyWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_db = core.DB
        core.DB = Path(self.temp.name) / 'safety.sqlite'
        core.initialize()
        self.admin = principal()
        self.reviewer = principal('USR-PV', 'pv', ['AIIA-001'])
        self.coordinator = principal('USR-COORD', 'coordinator', ['AIIA-001'])
        with core.connect() as conn:
            for table in ('dictionaries', 'obligations'):
                conn.execute(f'CREATE TABLE IF NOT EXISTS {table}(id TEXT PRIMARY KEY, data TEXT NOT NULL)')
            for who in (self.admin, self.reviewer, self.coordinator):
                core.save(conn, 'users', {'id': who['user_id'], 'name': who['name'], 'role': who['role'],
                                         'scope': who['scope'], 'active': True})
            self.event = core.get(conn, 'events', 'AE-0001')

    def tearDown(self):
        core.DB = self.old_db
        self.temp.cleanup()

    def mutate(self, who, path, data):
        with core.connect() as conn:
            return workflow.mutate(core, conn, who, path, data)

    def expect_error(self, status, who, path, data):
        with self.assertRaises(core.ApiError) as raised:
            self.mutate(who, path, data)
        self.assertEqual(status, raised.exception.status)

    def dictionary_data(self, **updates):
        data = {'name': 'Synthetic safety training vocabulary', 'version': '1.0', 'kind': 'Synthetic',
                'terms': [{'code': 'SYN-001', 'label': 'Dizziness'}, {'code': 'SYN-002', 'label': 'Reported nausea'},
                          {'code': 'SYN-003', 'label': 'Skin irritation'}]}
        data.update(updates)
        return data

    def dictionary(self, **updates):
        return self.mutate(self.admin, '/api/dictionaries', self.dictionary_data(**updates))['record']

    def obligation_data(self, **updates):
        data = {'recipient': 'Synthetic IEC recipient', 'phase': 'initial', 'assignee_id': self.reviewer['user_id'],
                'due_at': core.stamp(core.utcnow() - timedelta(hours=1)),
                'reason': 'Study SOP demo: recorded recipient target, applicability reviewed separately.'}
        data.update(updates)
        return data

    def obligation(self, **updates):
        return self.mutate(self.reviewer, '/api/safety/AE-0001/obligations', self.obligation_data(**updates))['record']

    def test_dictionary_immutable_metadata_licence_and_term_validation(self):
        dictionary = self.dictionary()
        self.assertEqual(3, dictionary['term_count'])
        self.assertNotIn('terms', dictionary)
        self.assertFalse(dictionary['licence_confirmed'])
        self.assertEqual(64, len(dictionary['sha256']))
        self.expect_error(409, self.admin, '/api/dictionaries', self.dictionary_data())
        self.expect_error(400, self.admin, '/api/dictionaries', self.dictionary_data(kind='MedDRA'))
        self.expect_error(400, self.admin, '/api/dictionaries', self.dictionary_data(kind='WHODrug', licence_confirmed='true'))
        for terms in ([], [{'code': 'X', 'label': 'One'}, {'code': 'X', 'label': 'Two'}], ['not an object'],
                      [{'code': '../x', 'label': 'Invalid code'}], [{'code': 'X', 'label': 'Invalid\nlabel'}],
                      [{'code': str(i), 'label': 'Synthetic'} for i in range(2001)]):
            self.expect_error(400, self.admin, '/api/dictionaries', self.dictionary_data(version='invalid', terms=terms))
        declared = self.dictionary(kind='MedDRA', licence_confirmed=True, name='User declaration test',
                                   terms=[{'code': 'FIXTURE-ONLY', 'label': 'Synthetic test term; not a licensed term'}])
        self.assertTrue(declared['licence_confirmed'])
        self.assertIn('not independently verified', declared['licence_verification'])
        with core.connect() as conn:
            metadata = workflow.list_dictionary_metadata(core, conn, self.reviewer)
            self.assertEqual(2, len(metadata))
            self.assertTrue(all('terms' not in entry for entry in metadata))
            imported = [json.loads(row['payload']) for row in conn.execute('SELECT payload FROM audit')
                        if json.loads(row['payload'])['action'] == 'DICTIONARY_IMPORTED']
            self.assertTrue(all('terms' not in entry['after'] for entry in imported))
            self.assertTrue(core.verify_audit(conn)['valid'])

    def test_dictionary_and_coding_named_role_and_scope_access(self):
        self.expect_error(403, principal(None), '/api/dictionaries', self.dictionary_data())
        self.expect_error(403, self.reviewer, '/api/dictionaries', self.dictionary_data())
        dictionary = self.dictionary()
        payload = {'dictionary_id': dictionary['id'], 'code': 'SYN-001', 'reason': 'Human reviewed term selection.'}
        path = '/api/safety/AE-0001/coding'
        self.expect_error(403, principal(None), path, payload)
        self.expect_error(403, self.coordinator, path, payload)
        outside = principal('USR-OUTSIDE', 'pv', ['AIIA-002'])
        self.expect_error(403, outside, path, payload)
        with core.connect() as conn:
            for who in (outside, principal('USR-REG', 'regulator'), principal('USR-LEAD', 'leadership')):
                with self.assertRaises(core.ApiError) as raised:
                    workflow.suggest(core, conn, who, 'AE-0001', dictionary['id'])
                self.assertEqual(403, raised.exception.status)
            with self.assertRaises(core.ApiError) as raised:
                workflow.list_dictionary_metadata(core, conn, principal('USR-REG', 'regulator'))
            self.assertEqual(403, raised.exception.status)

    def test_suggestions_deterministic_scored_abstention_and_verbatim_preservation(self):
        dictionary = self.dictionary()
        with core.connect() as conn:
            before = core.get(conn, 'events', 'AE-0001')
            first = workflow.suggest(core, conn, self.coordinator, 'AE-0001', dictionary['id'])
            second = workflow.suggest(core, conn, self.coordinator, 'AE-0001', dictionary['id'])
            self.assertEqual(first, second)
            self.assertEqual('SYN-001', first['candidates'][0]['code'])
            self.assertTrue(first['requires_human_review'])
            self.assertTrue(all(0.2 <= entry['lexical_similarity'] <= 1 for entry in first['candidates']))
            self.assertEqual(before, core.get(conn, 'events', 'AE-0001'))
            exact = workflow.suggest(core, conn, self.reviewer, 'AE-0003', dictionary['id'])
            self.assertEqual(1.0, exact['candidates'][0]['lexical_similarity'])
        unrelated = self.dictionary(version='2.0', terms=[{'code': 'SYN-NOMATCH', 'label': 'zzzzzzzzzzzzzzzzzzzz'}])
        with core.connect() as conn:
            answer = workflow.suggest(core, conn, self.reviewer, 'AE-0001', unrelated['id'])
            self.assertTrue(answer['abstained'])
            self.assertEqual([], answer['candidates'])
            with self.assertRaises(core.ApiError) as raised:
                workflow.suggest(core, conn, self.reviewer, 'AE-0001', 'DICT-MISSING')
            self.assertEqual(404, raised.exception.status)

    def test_reviewed_coding_release_history_and_no_causality_change(self):
        dictionary = self.dictionary()
        path = '/api/safety/AE-0001/coding'
        data = {'dictionary_id': dictionary['id'], 'code': 'SYN-001', 'reason': 'Reviewer selected synthetic term.'}
        self.expect_error(400, self.reviewer, path, {**data, 'code': 'NOT-IN-DICTIONARY'})
        coded = self.mutate(self.reviewer, path, data)['record']
        self.assertEqual('Synthetic', coded['coded_term']['kind'])
        self.assertEqual(self.reviewer['user_id'], coded['coded_term']['reviewer'])
        self.assertEqual(self.event['term'], coded['term'])
        self.assertEqual(self.event['narrative'], coded['narrative'])
        self.assertNotIn('MedDRA', coded['coding'])
        release = self.dictionary(version='2.0')
        updated = self.mutate(self.reviewer, path, {**data, 'dictionary_id': release['id']})['record']
        self.assertEqual('2.0', updated['coded_term']['version'])
        self.assertEqual('1.0', updated['coding_history'][0]['version'])
        self.assertEqual(self.event['serious'], updated['serious'])
        self.assertEqual(self.event['status'], updated['status'])
        medication = self.dictionary(kind='WHODrug', licence_confirmed=True,
                                     terms=[{'code': 'FIXTURE', 'label': 'Synthetic medication test fixture'}])
        self.expect_error(400, self.reviewer, path, {**data, 'dictionary_id': medication['id'], 'code': 'FIXTURE'})
        with core.connect() as conn:
            with self.assertRaises(core.ApiError) as raised:
                workflow.suggest(core, conn, self.reviewer, 'AE-0001', medication['id'])
            self.assertEqual(400, raised.exception.status)
            self.assertTrue(core.verify_audit(conn)['valid'])

    def test_obligation_assignees_role_scope_deadlines_and_uniqueness(self):
        path = '/api/safety/AE-0001/obligations'
        self.expect_error(403, self.coordinator, path, self.obligation_data())
        self.expect_error(403, principal('OUTSIDE', 'pv', ['AIIA-002']), path, self.obligation_data())
        self.expect_error(400, self.reviewer, path, self.obligation_data(assignee_id=self.coordinator['user_id']))
        self.expect_error(400, self.reviewer, path, self.obligation_data(due_at='2026-09-30T10:00:00'))
        self.expect_error(400, self.reviewer, path, self.obligation_data(due_at='not a timestamp'))
        self.expect_error(400, self.reviewer, path, self.obligation_data(due_at=core.stamp(core.utcnow() - timedelta(days=30))))
        with core.connect() as conn:
            user = core.get(conn, 'users', self.reviewer['user_id'])
            user['active'] = False
            core.save(conn, 'users', user)
        self.expect_error(400, self.admin, path, self.obligation_data())
        with core.connect() as conn:
            user['active'] = True
            user['scope'] = ['AIIA-002']
            core.save(conn, 'users', user)
        self.expect_error(400, self.admin, path, self.obligation_data())
        with core.connect() as conn:
            user['scope'] = ['AIIA-001']
            core.save(conn, 'users', user)
            assignees = workflow.list_assignees(core, conn, self.reviewer, 'AIIA-001')
            self.assertEqual({self.admin['user_id'], self.reviewer['user_id']}, {entry['id'] for entry in assignees})
            self.assertTrue(all(set(entry) == {'id', 'name', 'role'} for entry in assignees))
        obligation = self.obligation()
        self.assertEqual('Awaiting dispatch', obligation['status'])
        self.expect_error(409, self.reviewer, path, self.obligation_data(recipient='SYNTHETIC IEC RECIPIENT'))
        self.expect_error(409, self.reviewer, path, self.obligation_data(recipient='Synthetic  IEC\t recipient'))
        followup = self.obligation(phase='analysis', due_at=core.stamp(core.utcnow() + timedelta(days=10)))
        self.assertEqual('analysis', followup['phase'])
        with core.connect() as conn:
            self.assertEqual(2, len(workflow.list_obligations(core, conn, self.reviewer)))
            self.assertEqual([], workflow.list_obligations(core, conn, principal('OUTSIDE', 'pv', ['AIIA-002'])))
            self.assertEqual([], workflow.list_obligations(core, conn, principal('LEAD', 'leadership')))

    def test_dispatch_receipt_escalation_order_and_entry_times(self):
        obligation = self.obligation()
        path = '/api/obligations/' + obligation['id']
        sent_at = core.stamp(core.utcnow() - timedelta(hours=2))
        received_at = core.stamp(core.utcnow() - timedelta(hours=1))
        dispatch = {'sent_at': sent_at, 'reference': 'SYN-SENT-001', 'reason': 'Recorded evidence of external dispatch.'}
        receipt = {'received_at': received_at, 'reference': 'SYN-ACK-001', 'reason': 'Recorded external acknowledgment.'}
        self.expect_error(409, self.reviewer, path + '/receipt', receipt)
        self.expect_error(400, self.reviewer, path + '/dispatch', {**dispatch, 'sent_at': core.stamp(core.utcnow() + timedelta(hours=1))})
        self.expect_error(400, self.reviewer, path + '/dispatch', {**dispatch, 'sent_at': core.stamp(core.utcnow() - timedelta(days=30))})
        self.expect_error(400, self.reviewer, path + '/dispatch', {**dispatch, 'sent_at': '2026-09-30T10:00:00'})
        escalated = self.mutate(self.reviewer, path + '/escalate', {'reason': 'Asked assigned reviewer to follow up.'})['record']
        self.assertEqual('Awaiting dispatch', escalated['status'])
        self.assertEqual(1, len(escalated['escalations']))
        with core.connect() as conn:
            self.assertTrue(workflow.list_obligations(core, conn, self.reviewer)[0]['overdue'])
        dispatched = self.mutate(self.reviewer, path + '/dispatch', dispatch)['record']
        self.assertEqual('Awaiting receipt', dispatched['status'])
        self.assertEqual(sent_at, dispatched['sent_at'])
        self.assertNotEqual(sent_at, dispatched['dispatch_entered_at'])
        self.expect_error(409, self.reviewer, path + '/dispatch', dispatch)
        self.expect_error(400, self.reviewer, path + '/receipt', {**receipt, 'received_at': core.stamp(core.utcnow() - timedelta(hours=3))})
        self.expect_error(400, self.reviewer, path + '/receipt', {**receipt, 'received_at': core.stamp(core.utcnow() + timedelta(days=1))})
        acknowledged = self.mutate(self.reviewer, path + '/receipt', receipt)['record']
        self.assertEqual('Acknowledged', acknowledged['status'])
        self.assertEqual(received_at, acknowledged['received_at'])
        self.assertNotEqual(received_at, acknowledged['receipt_entered_at'])
        self.expect_error(409, self.reviewer, path + '/receipt', receipt)
        self.expect_error(409, self.reviewer, path + '/escalate', {'reason': 'Unneeded escalation'})
        with core.connect() as conn:
            self.assertFalse(workflow.list_obligations(core, conn, self.reviewer)[0]['overdue'])
            self.assertEqual(self.event, core.get(conn, 'events', self.event['id']))
            self.assertTrue(core.verify_audit(conn)['valid'])

    def test_failed_dispatch_is_atomic_and_actions_are_scoped(self):
        obligation = self.obligation()
        path = '/api/obligations/' + obligation['id'] + '/dispatch'
        payload = {'sent_at': core.stamp(core.utcnow() - timedelta(hours=2)), 'reference': '', 'reason': 'Missing reference'}
        with core.connect() as conn:
            original = core.get(conn, 'obligations', obligation['id'])
            original_count = core.verify_audit(conn)['entries']
        self.expect_error(400, self.reviewer, path, payload)
        payload['reference'] = 'SYN-REF'
        self.expect_error(403, self.coordinator, path, payload)
        self.expect_error(403, principal('OUTSIDE', 'pv', ['AIIA-002']), path, payload)
        with core.connect() as conn:
            self.assertEqual(original, core.get(conn, 'obligations', obligation['id']))
            self.assertEqual(original_count, core.verify_audit(conn)['entries'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
