"""Run isolated checks; pass --browser to include installed-Chrome workflows."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--browser', action='store_true')
args = parser.parse_args()
names = ['api', 'accounts', 'documents', 'exchange', 'safety_workflow', 'ops', 'runtime']
if args.browser:
    names += ['browser', 'browser_extended']
for name in names:
    result = subprocess.run([sys.executable, str(ROOT / 'tests' / f'test_{name}.py')], cwd=ROOT, capture_output=True, text=True)
    output = result.stdout + result.stderr
    print(f'{name}: {"PASS" if result.returncode == 0 else "FAIL"}', flush=True)
    if result.returncode:
        print(output, flush=True)
        sys.exit(result.returncode)
    for line in output.splitlines():
        if line.startswith(('Ran ', 'PASS:')):
            print('  ' + line, flush=True)
print('All requested checks passed. Test databases are isolated from the demonstration database.')
