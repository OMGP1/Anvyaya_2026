#!/usr/bin/env python3
"""Validate a fresh synthetic export with the pinned official HL7 R4 validator.

Never opens the configured application database. Downloads of definition packages
are allowed unless --offline is selected; terminology service use is always off.
The validator JAR is supplied separately and its SHA-256 must match the pin below.
"""

import argparse
from collections import Counter
import hashlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
VERSION = '6.10.4'
JAR_SHA256 = '1106b9d58f9e363e47bea7c4fc065841e5fc91fe9d062775c3bfdd212bd653cc'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jar', type=Path, required=True, help='Official validator_cli.jar version 6.10.4')
    parser.add_argument('--cache-dir', type=Path,
                        default=Path(tempfile.gettempdir()) / 'anvaya-fhir-validation-home',
                        help='Isolated Java user.home and FHIR package cache')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/validation/fhir-output.json',
                        help='Destination for the unmodified OperationOutcome JSON')
    parser.add_argument('--offline', action='store_true', help='Disable HTTP(S); requires cached definition packages')
    args = parser.parse_args()
    if sha256(args.jar) != JAR_SHA256:
        parser.error('Validator JAR SHA-256 differs from the pinned official 6.10.4 artifact.')
    cache = args.cache_dir.resolve()
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='anvaya-fhir-validation-') as directory:
        workspace = Path(directory)
        # Set isolation before importing the app: no connection can use its live DB.
        os.environ['CTMS_DB'] = str(workspace / 'synthetic.sqlite')
        os.environ['CTMS_DEMO_LOGIN'] = 'true'
        os.environ.pop('CTMS_ADMIN_PASSWORD', None)
        sys.path.insert(0, str(ROOT))
        import server

        bundle_function_sha256 = hashlib.sha256(inspect.getsource(server.bundle).encode()).hexdigest()
        server.initialize()
        with server.connect() as conn:
            exported = server.bundle(conn, 'admin')
        source = workspace / 'bundle.json'
        source.write_text(json.dumps(exported, indent=2) + '\n', encoding='utf-8')
        outcome = workspace / 'outcome.json'
        command = ['java', f'-Duser.home={cache}', '-Xmx2g', '-jar', str(args.jar.resolve()),
                   str(source), '-version', '4.0.1', '-tx', 'n/a',
                   '-txCache', str(cache / 'tx-cache'), '-output', str(outcome)]
        if args.offline:
            command.append('-no-http-access')
        print('Validating a fresh synthetic bundle; terminology service disabled.', flush=True)
        completed = subprocess.run(command, capture_output=True, text=True, timeout=300)
        if not outcome.exists():
            print(completed.stdout[-4000:] + completed.stderr[-4000:], file=sys.stderr)
            raise RuntimeError(f'Validator produced no OperationOutcome (exit {completed.returncode}); no result saved.')
        result = json.loads(outcome.read_text(encoding='utf-8'))
        if result.get('resourceType') != 'OperationOutcome':
            raise RuntimeError('Unexpected validator output; no result saved.')
        counts = Counter(issue['severity'] for issue in result.get('issue', []))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(outcome.read_bytes())
        print(json.dumps({
            'validator_version': VERSION, 'validator_sha256': JAR_SHA256,
            'fhir_version': '4.0.1', 'terminology_service': 'disabled',
            'http_disabled': args.offline, 'exit_code': completed.returncode,
            'resources': len(exported['entry']), 'issues': dict(counts),
            'input_sha256': sha256(source), 'outcome_sha256': sha256(outcome),
            'bundle_function_sha256': bundle_function_sha256,
            'output': str(args.output.resolve()),
            'definition_packages': sorted(p.name for p in (cache / '.fhir/packages').iterdir()
                                          if p.is_dir() and '#' in p.name),
        }, indent=2))
        return 1 if completed.returncode or counts['error'] or counts['fatal'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
