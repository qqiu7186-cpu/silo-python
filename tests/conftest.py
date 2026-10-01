import os
import pytest


def pytest_addoption(parser):
    parser.addoption('--run-integration', action='store_true',
                     help='Run against SILO_ENDPOINT using SILO_ACCESS_KEY/SECRET_KEY')


def pytest_collection_modifyitems(config, items):
    if config.getoption('--run-integration'):
        missing = [key for key in ('SILO_ENDPOINT', 'SILO_ACCESS_KEY', 'SILO_SECRET_KEY')
                   if not os.environ.get(key)]
        if missing:
            raise pytest.UsageError('Integration requires: ' + ', '.join(missing))
    else:
        for item in items:
            if 'integration' in item.keywords:
                item.add_marker(pytest.mark.skip(reason='Use --run-integration with SILO_*'))
