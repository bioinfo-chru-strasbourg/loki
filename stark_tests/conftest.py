import pytest


def pytest_addoption(parser):
    parser.addoption("--json", action="store", default="default_value")


@pytest.fixture(scope="session")
def json(pytestconfig):
    json_value = pytestconfig.getoption("--json")
    return json_value
