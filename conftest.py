import pytest
import json
import logging as log
import os


def pytest_addoption(parser):
    parser.addoption("--jsonvalue", action="store", default="default_value")


@pytest.fixture(scope="session")
def json_value(pytestconfig):
    value = pytestconfig.getoption("--jsonvalue")
    return value


@pytest.fixture(scope="session")
def loki_config(json_value):
    with open(json_value, "r") as j:
        data = json.loads(j.read())
    return data


@pytest.fixture(scope="session")
def module_config(loki_config):
    module_config = (
        loki_config["general"]["config"] + loki_config["general"]["module"] + ".json"
    )
    with open(module_config, "r") as j:
        data = json.loads(j.read())
    return data
