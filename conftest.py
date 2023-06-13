import pytest
import json


def pytest_addoption(parser):
    parser.addoption("--jsonvalue", action="store", default="default_value")


@pytest.fixture(scope="session")
def jsonvalue(pytestconfig):
    json_value = pytestconfig.getoption("--jsonvalue")
    return json_value


@pytest.fixture(scope="session")
def config(jsonvalue):
    with open(jsonvalue, "r") as j:
        data = json.loads(j.read())
    return data
