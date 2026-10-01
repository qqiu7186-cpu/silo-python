"""Run upstream 7.2.20 functional tests against a local SILO_* endpoint.

This makes and deletes random minio-py-test-* buckets. It does not configure
KMS, external notifications or TLS. Run from a scratch directory; upstream
creates temporary local files. No credentials are printed in the summary.
"""
import argparse
from contextlib import redirect_stdout
import importlib.util
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys

import minio
from silo import Silo


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', type=Path)
    parser.add_argument('--client', choices=['minio', 'silo'], default='silo')
    parser.add_argument('--result', required=True, type=Path)
    args = parser.parse_args()
    checkout = args.checkout.resolve()
    result_path = args.result.resolve()
    revision = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
    if minio.__version__ != '7.2.20' or revision != 'f671ca948b35978c39a3100e4ae0e9b93416b911':
        parser.error('Install minio 7.2.20 and use the exact upstream 7.2.20 checkout')
    if subprocess.run(['git', '-C', str(checkout), 'diff', '--quiet', 'HEAD', '--']).returncode:
        parser.error('Upstream tracked files must be unmodified')
    for key in ('SILO_ENDPOINT', 'SILO_ACCESS_KEY', 'SILO_SECRET_KEY'):
        if not os.environ.get(key):
            parser.error(key + ' is required')
    secure = os.environ.get('SILO_SECURE', 'true').strip().lower()
    if secure not in ('true', 'false'):
        parser.error('SILO_SECURE must be true/false')
    os.environ.update(SERVER_ENDPOINT=os.environ['SILO_ENDPOINT'],
                      ACCESS_KEY=os.environ['SILO_ACCESS_KEY'],
                      SECRET_KEY=os.environ['SILO_SECRET_KEY'],
                      ENABLE_HTTPS='1' if secure == 'true' else '0',
                      MINT_MODE='full')
    selected = Silo if args.client == 'silo' else minio.Minio
    original = minio.Minio
    spec = importlib.util.spec_from_file_location('upstream_functional', checkout/'tests/functional/tests.py')
    module = importlib.util.module_from_spec(spec)
    minio.Minio = selected
    try:
        spec.loader.exec_module(module)
    finally:
        minio.Minio = original
    if module.Minio is not selected:
        raise RuntimeError('Upstream functional tests did not load selected client')
    output = StringIO()
    failed = False
    with redirect_stdout(output):
        try:
            module.main()
        except module.TestFailed:
            failed = True
    results = []
    for line in output.getvalue().splitlines():
        entry = json.loads(line)
        if entry['name'] == 'minio-py:test_make_bucket_with_region' and '.amazonaws.com' not in os.environ['SILO_ENDPOINT']:
            entry['status'] = 'NOT_APPLICABLE'
        # Publish names/status only; exclude traces, arguments and signed URLs.
        results.append({key:entry[key] for key in ('name','status','duration') if key in entry})
    summary = {'client': args.client, 'upstream_commit': revision,
               'endpoint': os.environ['SILO_ENDPOINT'], 'secure': secure == 'true',
               'pass': sum(r['status']=='PASS' for r in results),
               'fail': sum(r['status']=='FAIL' for r in results),
               'not_applicable': sum(r['status']=='NOT_APPLICABLE' for r in results),
               'not_implemented': sum(r['status']=='NA' for r in results),
               'results': results,
               'limitations': ['HTTP run excludes SSE-C tests',
                               'AWS-only cases short-circuit for a local endpoint',
                               'notification test only checks empty configuration']}
    result_path.write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='results'}))
    if failed:
        for line in output.getvalue().splitlines():
            entry = json.loads(line)
            if entry['status']=='FAIL':
                print('Failed upstream case:', entry['name'], file=sys.stderr)
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
