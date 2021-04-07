#one-time setup
import os
cwd = os.getcwd()
if cwd.endswith('selenium-support'):
    os.chdir(os.path.join(cwd, 'data'))

import pytest

ismultidispatchfound = False
try:
    # pip install multidispatch==0.2
    #python3 -m pip install .[md]
    from multidispatch import multimethod
    ismultidispatchfound = True
except ImportError:
    pass


#see https://docs.pytest.org/en/latest/example/simple.html#control-skipping-of-tests-according-to-command-line-option
def skip_tests(config=None, items=None, keyword=None, reason=None):
    if items is None:
        TypeError("items can't be None")

    if reason is None:
        TypeError("reason can't be None")

    if keyword is None:
        TypeError("keyword can't be None")

    skip = pytest.mark.skip(reason=reason)
    for item in items:
        if keyword in item.keywords:
            item.add_marker(skip)



#see https://docs.pytest.org/en/latest/example/simple.html#control-skipping-of-tests-according-to-command-line-option
def pytest_collection_modifyitems(config, items):
    if not ismultidispatchfound:
        skip_tests(items=items, keyword="md", reason="multidispatch is not installed..")


#see https://docs.pytest.org/en/latest/mark.html
#see https://docs.pytest.org/en/latest/example/simple.html#control-skipping-of-tests-according-to-command-line-option
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "md: multidispatch is not installed.."
    )