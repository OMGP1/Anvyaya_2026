"""Verified SQLite recovery copies; no command replaces an existing database."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import sys
import time

from server import DB, verify_audit


class VerificationError(ValueError):
    pass


def readonly(path):
    conn = sqlite3.connect(Path(path).expanduser().resolve().as_uri() + '?mode=ro', uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA query_only=ON')
    conn.execute('PRAGMA trusted_schema=OFF')
    return conn


def inspect_database(conn):
    """Verify SQLite structure and the same raw-payload chain checked by the app."""
    if [row[0] for row in conn.execute('PRAGMA integrity_check')] != ['ok']:
        raise VerificationError('SQLite integrity verification failed.')
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {'studies', 'participants', 'events', 'queries', 'visits', 'settings', 'audit'} <= tables:
        raise VerificationError('Required application tables are missing.')
    result = verify_audit(conn)
    if not result['valid']:
        raise VerificationError('Audit chain verification failed.')
    return {'integrity': 'ok', 'audit_entries': result['entries'], 'audit_head': result['head']}


def verify(path):
    with closing(readonly(path)) as conn:
        # All checks observe one snapshot, including when the application is live.
        conn.execute('BEGIN')
        return inspect_database(conn)


def copy_database(source, destination):
    """Online backup API includes committed WAL data; output must not exist."""
    destination = Path(destination).expanduser().absolute()
    sidecars = [Path(str(destination) + suffix) for suffix in ('-wal', '-shm', '-journal')]
    with closing(readonly(source)) as source_conn:
        if any(os.path.lexists(path) for path in sidecars):
            raise FileExistsError('Destination recovery sidecars already exist.')
        descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(descriptor)
        try:
            deadline = time.monotonic() + 60

            def progress(_status, _remaining, _total):
                if time.monotonic() > deadline:
                    raise VerificationError('Copy timed out; retry during lower database activity.')

            with closing(sqlite3.connect(destination, timeout=5)) as target:
                target.row_factory = sqlite3.Row
                source_conn.backup(target, pages=256, progress=progress, sleep=0.1)
                # Produce a standalone file without a recovery dependency on WAL.
                target.execute('PRAGMA journal_mode=DELETE')
                target.execute('PRAGMA trusted_schema=OFF')
                result = inspect_database(target)
            with destination.open('rb') as copied:
                os.fsync(copied.fileno())
            return result
        except BaseException:
            for path in [destination, *sidecars]:
                path.unlink(missing_ok=True)
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Back up, verify or restore an Anvaya SQLite database. Existing files are never overwritten.',
        epilog='Copies contain the complete database. Use approved encrypted storage. Restore into a new path, verify it, then stop the application and configure CTMS_DB to that path. Hash verification detects broken chains; it does not authenticate a chain rewritten by a database administrator.',
    )
    commands = parser.add_subparsers(dest='command', required=True)
    backup = commands.add_parser('backup', help='Create a verified online backup, including committed WAL records.')
    backup.add_argument('destination', type=Path, help='New output file; parent directory must already exist.')
    backup.add_argument('--source', type=Path, default=DB, help='Application SQLite database (default: CTMS_DB or data/ctms.sqlite).')
    check = commands.add_parser('verify', help='Read-only SQLite integrity and audit-chain verification.')
    check.add_argument('source', type=Path)
    restore = commands.add_parser('restore', help='Copy a verified backup into a NEW database; does not switch the running app.')
    restore.add_argument('source', type=Path)
    restore.add_argument('destination', type=Path)
    args = parser.parse_args(argv)
    try:
        result = verify(args.source) if args.command == 'verify' else copy_database(args.source, args.destination)
    except (OSError, sqlite3.Error, VerificationError, KeyError, IndexError, TypeError) as error:
        message = str(error) if isinstance(error, VerificationError) else 'Database operation failed; check source format, paths, permissions and destination absence.'
        print(json.dumps({'status': 'error', 'message': message}), file=sys.stderr)
        return 1
    print(json.dumps({'status': 'ok', 'operation': args.command, **result}, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
