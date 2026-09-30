"""Run: python3 tests/test_ops.py. Every database lives in a temporary directory."""
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import stat
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ops
import server


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.sqlite'
        self.writer = sqlite3.connect(self.source)
        self.addCleanup(self.writer.close)
        self.writer.row_factory = sqlite3.Row
        self.writer.execute('PRAGMA journal_mode=WAL')
        for table in ['studies', 'participants', 'events', 'queries', 'visits', 'settings', 'documents']:
            self.writer.execute(f'CREATE TABLE {table}(id TEXT PRIMARY KEY, data TEXT NOT NULL)')
        self.writer.executescript('''
            CREATE TABLE audit(seq INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL, prev TEXT NOT NULL, hash TEXT NOT NULL);
            CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT, 'Audit records are append-only'); END;
            CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT, 'Audit records are append-only'); END;
        ''')
        server.save(self.writer, 'studies', {'id': 'TEST-001', 'title': 'Synthetic recovery study'})
        server.save(self.writer, 'participants', {'id': 'SYN-001', 'study_id': 'TEST-001', 'private_test_marker': 'never_print_this'})
        server.save(self.writer, 'documents', {'id': 'DOC-001', 'study_id': 'TEST-001', 'version': '2'})
        server.audit(self.writer, 'test:alice', 'PARTICIPANT_CREATED', 'SYN-001', 'TEST-001', after={'consent': True})
        server.audit(self.writer, 'test:bob', 'DOCUMENT_REVIEWED', 'DOC-001', 'TEST-001', reason='Synthetic verification')
        self.writer.commit()

    def source_hashes(self):
        return {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (self.source, Path(str(self.source) + '-wal')) if path.exists()}

    def test_online_backup_and_restore_include_wal_and_leave_source_unchanged(self):
        before = self.source_hashes()
        backup = self.root / 'backup.sqlite'
        result = ops.copy_database(self.source, backup)
        self.assertEqual(result['audit_entries'], 2)
        self.assertEqual(result, ops.verify(backup))
        restored = self.root / 'restored.sqlite'
        self.assertEqual(result, ops.copy_database(backup, restored))
        self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(restored.stat().st_mode), 0o600)
        with sqlite3.connect(restored) as conn:
            conn.row_factory = sqlite3.Row
            self.assertEqual(server.get(conn, 'participants', 'SYN-001')['private_test_marker'], 'never_print_this')
            self.assertEqual(server.get(conn, 'documents', 'DOC-001')['version'], '2')
            self.assertTrue(server.verify_audit(conn)['valid'])
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE audit SET hash='tamper'")
        self.assertEqual(before, self.source_hashes())
        self.assertFalse(Path(str(backup) + '-wal').exists())

    def test_refuses_existing_files_same_source_and_symlinks(self):
        existing = self.root / 'existing.sqlite'
        existing.write_bytes(b'keep exactly')
        alias = self.root / 'alias.sqlite'
        alias.symlink_to(existing)
        before = self.source_hashes()
        for destination in [existing, self.source, alias]:
            with self.assertRaises(FileExistsError):
                ops.copy_database(self.source, destination)
        self.assertEqual(existing.read_bytes(), b'keep exactly')
        self.assertTrue(alias.is_symlink())
        self.assertEqual(before, self.source_hashes())
        recovery_file = self.root / 'new.sqlite-journal'
        recovery_file.write_bytes(b'preserve earlier recovery state')
        with self.assertRaises(FileExistsError):
            ops.copy_database(self.source, self.root / 'new.sqlite')
        self.assertEqual(recovery_file.read_bytes(), b'preserve earlier recovery state')
        self.assertFalse((self.root / 'new.sqlite').exists())

    def test_tampered_audit_rejected_and_partial_output_removed(self):
        self.writer.execute('DROP TRIGGER audit_no_update')
        self.writer.execute("UPDATE audit SET payload='{}' WHERE seq=1")
        self.writer.commit()
        before = self.source_hashes()
        with self.assertRaisesRegex(ops.VerificationError, 'Audit chain'):
            ops.verify(self.source)
        destination = self.root / 'rejected.sqlite'
        with self.assertRaisesRegex(ops.VerificationError, 'Audit chain'):
            ops.copy_database(self.source, destination)
        self.assertEqual(list(self.root.glob('rejected.sqlite*')), [])
        self.assertEqual(before, self.source_hashes())

    def test_corrupt_or_wrong_database_rejected_without_source_changes(self):
        corrupt = self.root / 'corrupt.sqlite'
        corrupt.write_bytes(b'not a sqlite database')
        empty = self.root / 'wrong.sqlite'
        sqlite3.connect(empty).close()
        for source in (corrupt, empty):
            original = source.read_bytes()
            destination = self.root / ('copy-' + source.name)
            with self.assertRaises((sqlite3.DatabaseError, ops.VerificationError)):
                ops.copy_database(source, destination)
            self.assertFalse(destination.exists())
            self.assertEqual(source.read_bytes(), original)

    def test_cli_metadata_and_error_never_dump_record_contents(self):
        output, errors = io.StringIO(), io.StringIO()
        backup = self.root / 'cli-backup.sqlite'
        with redirect_stdout(output), redirect_stderr(errors):
            self.assertEqual(ops.main(['backup', str(backup), '--source', str(self.source)]), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(set(result), {'status', 'operation', 'integrity', 'audit_entries', 'audit_head'})
        self.assertEqual(result['operation'], 'backup')
        self.assertNotIn('never_print_this', output.getvalue() + errors.getvalue())
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            self.assertEqual(ops.main(['restore', str(backup), str(self.source)]), 1)
        self.assertEqual(output.getvalue(), '')
        self.assertEqual(json.loads(errors.getvalue())['status'], 'error')


if __name__ == '__main__':
    unittest.main()
