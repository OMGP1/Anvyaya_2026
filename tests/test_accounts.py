"""Named-account HTTP integration checks; each test uses its own temporary database."""
import json
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_api import Client
import server


TEMP_PASSWORD = 'Temporary#26046'
NEW_PASSWORD = 'Changed#26046Now'
RESET_PASSWORD = 'ResetTemporary#26046'
FINAL_PASSWORD = 'FinalChanged#26046'


class AccountTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='anvaya-accounts-')
        cls.addClassCleanup(cls.temp.cleanup)
        for adjustment in [
            patch.object(server, 'DB', Path(cls.temp.name) / 'unused.sqlite'),
            patch.object(server, 'DEMO_LOGIN', True),
            patch.object(server, 'SECURE_COOKIE', False),
            patch.object(server, 'SESSIONS', {}),
            patch.object(server, 'ATTEMPTS', {}),
            patch.dict(os.environ, {'CTMS_ADMIN_PASSWORD': ''}),
        ]:
            adjustment.start()
            cls.addClassCleanup(adjustment.stop)
        cls.httpd = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.addClassCleanup(cls.httpd.server_close)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.addClassCleanup(cls.httpd.shutdown)
        cls.base = f'http://127.0.0.1:{cls.httpd.server_port}'

    def setUp(self):
        with server.LOCK:
            server.DB = Path(self.temp.name) / (self._testMethodName + '.sqlite')
            server.SESSIONS.clear()
            server.ATTEMPTS.clear()
            server.initialize()
        self.admin = Client(self.base).login('admin')
        self.created = 0

    def tearDown(self):
        # Every scenario checks account-list and full-audit output for secret leakage.
        for path in ['/api/users', '/api/audit']:
            status, payload = self.admin.call(path)
            self.assertEqual(status, 200, payload)
            self.assert_redacted(payload)

    def assert_redacted(self, payload):
        encoded = json.dumps(payload)
        self.assertNotIn('password_hash', encoded)
        self.assertNotIn('pbkdf2_sha256$', encoded)
        for secret in [TEMP_PASSWORD, NEW_PASSWORD, RESET_PASSWORD, FINAL_PASSWORD]:
            self.assertNotIn(secret, encoded)

    def create(self, role='pi', scope=None, username=None, actor=None):
        self.created += 1
        payload = {
            'username': username or f'account.{self.created}',
            'name': f'Synthetic account {self.created}',
            'role': role,
            'scope': None if role == 'admin' else (scope if scope is not None else ['AIIA-003']),
            'password': TEMP_PASSWORD,
        }
        status, result = (actor or self.admin).call('/api/users', payload)
        self.assertEqual(status, 200, result)
        self.assert_redacted(result)
        return result['record']

    def latest(self, user):
        status, payload = self.admin.call('/api/users')
        self.assertEqual(status, 200, payload)
        return next(record for record in payload['users'] if record['id'] == user['id'])

    def sign_in(self, user, password=TEMP_PASSWORD):
        client = Client(self.base)
        status, result = client.call('/api/login', {'username': user['username'], 'password': password})
        self.assertEqual(status, 200, result)
        self.assert_redacted(result)
        status, profile = client.call('/api/me')
        self.assertEqual(status, 200, profile)
        self.assertEqual(profile['user_id'], user['id'])
        self.assertFalse(profile['demo'])
        self.assert_redacted(profile)
        client.csrf = profile['csrf']
        return client

    def change_password(self, client, current=TEMP_PASSWORD, replacement=NEW_PASSWORD):
        status, result = client.call('/api/account/password', {
            'current_password': current, 'password': replacement,
        })
        self.assertEqual(status, 200, result)
        self.assert_redacted(result)

    def active_client(self, user):
        client = self.sign_in(user)
        self.change_password(client)
        return client

    def management(self, user, action, **fields):
        current = self.latest(user)
        status, result = self.admin.call(f'/api/users/{user["id"]}/{action}', {
            'revision': current['revision'], 'reason': 'Synthetic access review', **fields,
        })
        self.assertEqual(status, 200, result)
        self.assertEqual(result['record']['revision'], current['revision'] + 1)
        self.assertGreater(result['record']['auth_version'], current['auth_version'])
        self.assert_redacted(result)
        return result['record']

    @staticmethod
    def enrolment(study='AIIA-003'):
        return {
            'study_id': study, 'age': 35, 'sex': 'F', 'prakriti': 'Not assessed',
            'consent': True, 'consent_version': '2.1', 'consent_language': 'English',
        }

    def test_scope_read_and_revocation_are_serialized(self):
        user = self.create()
        client = self.active_client(user)
        user = self.latest(user)
        checked, release, revocation_finished = threading.Event(), threading.Event(), threading.Event()
        original = server.Handler.session
        def pause_after_validation(handler):
            session = original(handler)
            if handler.path == '/api/data' and session.get('user_id') == user['id']:
                checked.set()
                release.wait(3)
            return session
        def revoke():
            result = self.admin.call('/api/users/' + user['id'] + '/revoke', {'revision': user['revision'], 'reason': 'Concurrent revocation test'})
            revocation_finished.set()
            return result
        with patch.object(server.Handler, 'session', pause_after_validation), ThreadPoolExecutor(max_workers=2) as pool:
            read = pool.submit(client.call, '/api/data')
            self.assertTrue(checked.wait(2))
            change = pool.submit(revoke)
            try:
                self.assertFalse(revocation_finished.wait(0.2), 'Revocation must not commit between authorization and the scoped read.')
            finally:
                release.set()
            self.assertEqual(read.result(timeout=3)[0], 200)
            self.assertEqual(change.result(timeout=3)[0], 200)
        self.assertEqual(client.call('/api/data')[0], 401)

    def test_valid_login_does_not_reset_failed_guess_budget(self):
        attacker = Client(self.base)
        for _ in range(10):
            self.assertEqual(attacker.call('/api/login', {'username': 'missing.target', 'password': 'incorrect'})[0], 401)
        Client(self.base).login('admin')
        for _ in range(5):
            self.assertEqual(attacker.call('/api/login', {'username': 'missing.target', 'password': 'incorrect'})[0], 401)
        self.assertEqual(attacker.call('/api/login', {'username': 'missing.target', 'password': 'incorrect'})[0], 429)

    def test_01_creation_uniqueness_and_password_redaction(self):
        user = self.create(username='Case.Name')
        self.assertEqual(user['username'], 'case.name')
        self.assertTrue(user['active'])
        self.assertTrue(user['must_change_password'])
        self.assertEqual(user['revision'], 1)
        status, duplicate = self.admin.call('/api/users', {
            'username': '  CASE.NAME  ', 'name': 'Duplicate', 'role': 'pi',
            'scope': ['AIIA-003'], 'password': TEMP_PASSWORD,
        })
        self.assertEqual(status, 409, duplicate)
        self.assertEqual(len(self.admin.call('/api/users')[1]['users']), 1)
        with server.connect() as conn:
            stored = server.get(conn, 'users', user['id'])
        self.assertNotEqual(stored['password_hash'], TEMP_PASSWORD)
        self.assertTrue(server.accounts.password_matches(TEMP_PASSWORD, stored['password_hash']))
        self.assertNotIn(TEMP_PASSWORD, json.dumps(stored))
        ledger = self.admin.call('/api/audit')[1]
        creations = [entry for entry in ledger['entries'] if entry['action'] == 'ACCOUNT_CREATED']
        self.assertEqual(len(creations), 1)
        self.assertEqual(creations[0]['actor'], 'demo:admin')
        self.assertEqual(creations[0]['entity'], user['id'])
        self.assertTrue(ledger['verification']['valid'])

    def test_02_temporary_password_gate_and_change_revokes_other_sessions(self):
        user = self.create()
        first, second = self.sign_in(user), self.sign_in(user)
        self.assertTrue(first.call('/api/me')[1]['must_change_password'])
        for path in ['/api/data', '/api/audit', '/api/export/fhir', '/api/users']:
            with self.subTest(path=path):
                self.assertEqual(first.call(path)[0], 403)
        self.assertEqual(first.call('/api/enrolments', self.enrolment())[0], 403)
        for current, replacement in [
            ('wrong-current-password', NEW_PASSWORD),
            (TEMP_PASSWORD, TEMP_PASSWORD),
            (TEMP_PASSWORD, 'too-short'),
        ]:
            with self.subTest(current=current, replacement=replacement):
                self.assertEqual(first.call('/api/account/password', {
                    'current_password': current, 'password': replacement,
                })[0], 400)
        self.assertEqual(first.call('/api/account/password', {
            'current_password': TEMP_PASSWORD, 'password': NEW_PASSWORD,
        }, {'X-CSRF-Token': 'invalid'})[0], 403)
        self.change_password(first)
        self.assertFalse(first.call('/api/me')[1]['must_change_password'])
        self.assertEqual(first.call('/api/data')[0], 200)
        self.assertEqual(second.call('/api/data')[0], 401)
        self.assertEqual(Client(self.base).call('/api/login', {
            'username': user['username'], 'password': TEMP_PASSWORD,
        })[0], 401)
        self.assertEqual(self.sign_in(user, NEW_PASSWORD).call('/api/data')[0], 200)

    def test_03_individual_scope_overrides_role_defaults_and_audits_user_id(self):
        user = self.create(role='pi', scope=['AIIA-003'])
        client = self.active_client(user)
        profile = client.call('/api/me')[1]
        self.assertEqual(profile['scope'], ['AIIA-003'])
        self.assertNotIn('AIIA-003', server.ROLES['pi']['scope'])
        status, data = client.call('/api/data')
        self.assertEqual(status, 200)
        self.assertEqual([study['id'] for study in data['studies']], ['AIIA-003'])
        for table in ['participants', 'events', 'visits', 'queries']:
            self.assertTrue(all(record['study_id'] == 'AIIA-003' for record in data[table]))
        self.assertEqual(client.call('/api/enrolments', self.enrolment('AIIA-001'))[0], 403)
        self.assertEqual(client.call('/api/export/fhir?study=AIIA-001')[0], 403)
        status, enrolment = client.call('/api/enrolments', self.enrolment())
        self.assertEqual(status, 200, enrolment)
        status, bundle = client.call('/api/export/fhir?study=AIIA-003')
        self.assertEqual(status, 200, bundle)
        study_ids = [entry['resource']['id'] for entry in bundle['entry'] if entry['resource']['resourceType'] == 'ResearchStudy']
        self.assertEqual(study_ids, ['AIIA-003'])
        ledger = self.admin.call('/api/audit')[1]
        entries = [entry for entry in ledger['entries'] if entry['actor'] == user['id']]
        self.assertTrue({'SESSION_STARTED', 'PASSWORD_CHANGED', 'PARTICIPANT_ENROLLED', 'DATA_EXPORTED'} <= {entry['action'] for entry in entries})
        self.assertTrue(all(entry['actor_name'] == user['name'] and entry['actor_role'] == 'pi' for entry in entries))
        event = next(entry for entry in entries if entry['action'] == 'PARTICIPANT_ENROLLED')
        self.assertEqual(event['entity'], enrolment['record']['id'])
        self.assertEqual(event['study_id'], 'AIIA-003')
        self.assertTrue(ledger['verification']['valid'])

    def test_04_revoke_invalidates_all_existing_sessions(self):
        user = self.create()
        first = self.active_client(user)
        second = self.sign_in(user, NEW_PASSWORD)
        self.management(user, 'revoke')
        self.assertEqual(first.call('/api/data')[0], 401)
        self.assertEqual(second.call('/api/me')[0], 401)
        fresh = self.sign_in(user, NEW_PASSWORD)
        self.assertFalse(fresh.call('/api/me')[1]['must_change_password'])
        self.assertEqual(fresh.call('/api/data')[0], 200)

    def test_05_reset_revokes_sessions_and_requires_a_new_password(self):
        user = self.create()
        first = self.active_client(user)
        second = self.sign_in(user, NEW_PASSWORD)
        reset = self.management(user, 'reset', password=RESET_PASSWORD)
        self.assertTrue(reset['must_change_password'])
        self.assertEqual(first.call('/api/data')[0], 401)
        self.assertEqual(second.call('/api/me')[0], 401)
        self.assertEqual(Client(self.base).call('/api/login', {
            'username': user['username'], 'password': NEW_PASSWORD,
        })[0], 401)
        replacement = self.sign_in(user, RESET_PASSWORD)
        self.assertEqual(replacement.call('/api/data')[0], 403)
        self.change_password(replacement, RESET_PASSWORD, FINAL_PASSWORD)
        self.assertEqual(replacement.call('/api/data')[0], 200)
        self.assertEqual(Client(self.base).call('/api/login', {
            'username': user['username'], 'password': RESET_PASSWORD,
        })[0], 401)

    def test_06_disable_role_change_and_scope_change_revoke_sessions(self):
        user = self.create()
        first = self.active_client(user)
        second = self.sign_in(user, NEW_PASSWORD)
        disabled = self.management(user, 'access', role='pi', active=False, scope=['AIIA-003'])
        self.assertFalse(disabled['active'])
        for client in [first, second]:
            self.assertEqual(client.call('/api/data')[0], 401)
        self.assertEqual(Client(self.base).call('/api/login', {
            'username': user['username'], 'password': NEW_PASSWORD,
        })[0], 401)
        self.management(user, 'access', role='pi', active=True, scope=['AIIA-003'])
        restored = self.sign_in(user, NEW_PASSWORD)
        self.assertEqual(restored.call('/api/data')[0], 200)
        self.management(user, 'access', role='monitor', active=True, scope=['AIIA-005'])
        self.assertEqual(restored.call('/api/data')[0], 401)
        monitor = self.sign_in(user, NEW_PASSWORD)
        self.assertEqual(monitor.call('/api/me')[1]['role'], 'monitor')
        self.assertEqual([study['id'] for study in monitor.call('/api/data')[1]['studies']], ['AIIA-005'])
        self.assertEqual(monitor.call('/api/enrolments', self.enrolment('AIIA-005'))[0], 403)
        self.management(user, 'access', role='monitor', active=True, scope=['AIIA-001'])
        self.assertEqual(monitor.call('/api/me')[0], 401)
        reassigned = self.sign_in(user, NEW_PASSWORD)
        self.assertEqual([study['id'] for study in reassigned.call('/api/data')[1]['studies']], ['AIIA-001'])
        self.assertEqual(reassigned.call('/api/export/fhir?study=AIIA-005')[0], 403)

    def test_07_last_named_admin_and_self_access_are_protected(self):
        first = self.create(role='admin')
        for changes in [
            {'role': 'admin', 'scope': None, 'active': False},
            {'role': 'pi', 'scope': ['AIIA-001'], 'active': True},
        ]:
            with self.subTest(changes=changes):
                status, result = self.admin.call(f'/api/users/{first["id"]}/access', {
                    'revision': first['revision'], 'reason': 'Attempt to remove last admin', **changes,
                })
                self.assertEqual(status, 409, result)
        self.assertTrue(self.latest(first)['active'])
        named_admin = self.active_client(first)
        second = self.create(role='admin', actor=named_admin)
        current = self.latest(first)
        for changes in [
            {'role': 'admin', 'scope': None, 'active': False},
            {'role': 'pi', 'scope': ['AIIA-001'], 'active': True},
        ]:
            self.assertEqual(named_admin.call(f'/api/users/{first["id"]}/access', {
                'revision': current['revision'], 'reason': 'Self access removal', **changes,
            })[0], 409)
        self.management(first, 'access', role='admin', active=False, scope=None)
        self.assertEqual(named_admin.call('/api/users')[0], 401)
        self.assertEqual(self.admin.call(f'/api/users/{second["id"]}/access', {
            'revision': second['revision'], 'reason': 'Remove remaining admin',
            'role': 'admin', 'scope': None, 'active': False,
        })[0], 409)
        ledger = self.admin.call('/api/audit')[1]
        creation = next(entry for entry in ledger['entries'] if entry['entity'] == second['id'] and entry['action'] == 'ACCOUNT_CREATED')
        self.assertEqual(creation['actor'], first['id'])
        self.assertEqual(creation['actor_role'], 'admin')

    def test_08_management_permissions_field_validation_and_stale_revision(self):
        user = self.create()
        client = self.active_client(user)
        self.assertEqual(Client(self.base).call('/api/users')[0], 401)
        self.assertEqual(client.call('/api/users')[0], 403)
        base = {'username': 'validation.user', 'name': 'Synthetic validation', 'role': 'pi', 'scope': ['AIIA-003'], 'password': TEMP_PASSWORD}
        self.assertEqual(client.call('/api/users', base)[0], 403)
        current = self.latest(user)
        for action in ['access', 'reset', 'revoke']:
            self.assertEqual(client.call(f'/api/users/{user["id"]}/{action}', {
                'revision': current['revision'], 'reason': 'Unauthorised request',
                'role': 'pi', 'scope': ['AIIA-003'], 'active': True, 'password': RESET_PASSWORD,
            })[0], 403)
        before = self.admin.call('/api/audit')[1]['verification']['entries']
        for changes in [
            {'username': ''}, {'username': 'ab'}, {'username': 'not a username'},
            {'name': ''}, {'role': 'owner'}, {'role': []}, {'scope': None},
            {'scope': ['AIIA-003', 'AIIA-003']}, {'scope': ['UNKNOWN']}, {'scope': [3]},
            {'role': 'admin', 'scope': []}, {'password': 'short'}, {'password': ' ' * 12},
            {'password': True}, {'password': 'x' * 129},
        ]:
            with self.subTest(changes=changes):
                status, result = self.admin.call('/api/users', {**base, **changes})
                self.assertEqual(status, 400, result)
        valid_access = {'revision': current['revision'], 'reason': 'Access review', 'role': 'pi', 'scope': ['AIIA-003'], 'active': True}
        for changes in [
            {'revision': True}, {'reason': ''}, {'active': 'false'}, {'role': 'unknown'},
            {'scope': ['UNKNOWN']}, {'scope': ['AIIA-003', 'AIIA-003']},
        ]:
            with self.subTest(access=changes):
                self.assertEqual(self.admin.call(f'/api/users/{user["id"]}/access', {**valid_access, **changes})[0], 400)
        self.assertEqual(self.admin.call('/api/audit')[1]['verification']['entries'], before)
        self.assertEqual(self.latest(user)['revision'], current['revision'])
        self.assertEqual(client.call('/api/data')[0], 200)
        updated = self.management(user, 'revoke')
        for action, additions in [('revoke', {}), ('reset', {'password': RESET_PASSWORD}), ('access', {'role': 'pi', 'scope': [], 'active': True})]:
            status, result = self.admin.call(f'/api/users/{user["id"]}/{action}', {
                'revision': current['revision'], 'reason': 'Stale update', **additions,
            })
            self.assertEqual(status, 409, result)
        self.assertEqual(self.latest(user)['revision'], updated['revision'])
        self.assertEqual(self.admin.call('/api/account/password', {
            'current_password': server.PASSWORD, 'password': NEW_PASSWORD,
        })[0], 403)

    def test_09_empty_assignment_does_not_inherit_role_scope(self):
        user = self.create(role='pi', scope=[])
        client = self.active_client(user)
        status, data = client.call('/api/data')
        self.assertEqual(status, 200, data)
        self.assertEqual(client.call('/api/me')[1]['scope'], [])
        for table in ['studies', 'participants', 'events', 'visits', 'queries']:
            self.assertEqual(data[table], [])
        self.assertEqual(data['kpis']['studies'], 0)
        self.assertEqual(data['kpis']['enrolled'], 0)
        self.assertEqual(client.call('/api/enrolments', self.enrolment('AIIA-001'))[0], 403)
        self.assertEqual(client.call('/api/export/fhir?study=AIIA-001')[0], 403)


if __name__ == '__main__':
    unittest.main(verbosity=2)
