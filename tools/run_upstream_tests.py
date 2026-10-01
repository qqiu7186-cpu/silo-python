"""Run the unmodified minio 7.2.20 unit suite against Minio or Silo.

Clone upstream separately, then:
python tools/run_upstream_tests.py /path/to/minio-py --client silo --result result.json
The SDK must be installed first. No credentials or server are required.
"""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

import minio
from silo import Silo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', type=Path)
    parser.add_argument('--client', choices=['minio', 'silo'], default='silo')
    parser.add_argument('--result', type=Path)
    args = parser.parse_args()
    checkout = args.checkout.resolve()
    result_path = args.result.resolve() if args.result else None
    if importlib.metadata.version('minio') != '7.2.20':
        parser.error('Install minio==7.2.20 first')
    revision = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != 'f671ca948b35978c39a3100e4ae0e9b93416b911':
        parser.error('Upstream checkout must be tag 7.2.20 (f671ca948b35978c39a3100e4ae0e9b93416b911)')
    if subprocess.run(['git', '-C', str(checkout), 'diff', '--quiet', 'HEAD', '--']).returncode:
        parser.error('Upstream tracked files must be unmodified')
    # Import installed minio first; changing this binding only selects the class
    # imported by upstream tests. Actual SDK implementation is never modified.
    original = minio.Minio
    selected = Silo if args.client == 'silo' else original
    sys.path.insert(0, str(checkout))
    os.chdir(checkout)
    minio.Minio = selected
    try:
        suite = unittest.defaultTestLoader.discover(
            str(checkout / 'tests/unit'), pattern='*_test.py', top_level_dir=str(checkout))
    finally:
        minio.Minio = original
    client_modules = [module for name, module in sys.modules.items()
                      if name.startswith('tests.unit.') and hasattr(module, 'Minio')]
    if not client_modules or any(module.Minio is not selected for module in client_modules):
        raise RuntimeError('Upstream tests did not load the selected client')
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    summary = {'client': args.client, 'upstream_version': '7.2.20',
               'upstream_commit': revision, 'tests': result.testsRun,
               'client_test_modules': len(client_modules),
               'failures': len(result.failures), 'errors': len(result.errors),
               'skipped': len(result.skipped)}
    if result_path:
        result_path.write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
