import pytest


def pytest_addoption(parser):
    parser.addoption("--jsonvalue", action="store", default="default_value")


@pytest.fixture(scope="session")
def json(pytestconfig):
    json_value = pytestconfig.getoption("--jsonvalue")
    return json_value
