# -*- coding: utf-8 -*-
import os
from os.path import join as osj
import json
import pytest
import logging as log


def check_loki_json(parsed_json):
    with open(parsed_json, "r") as j:
        data = json.loads(j.read())
    if data["general"]["type"] == "regression":
        if not data["input"]["reference"]:
            log.error(
                "Cannot launch regression process in case you don't have a reference result"
            )
            raise ValueError()
        elif not data["input"]["results"] and data["input"]["analyse"] == "no":
            log.error(
                "Cannot launch regression process in case you don't have results and you don't want any analysis"
            )
            raise ValueError()


def launch(parsed_json, output):
    mylog = log.getLogger()
    log_file = mylog.handlers[0].baseFilename
    date = (
        os.path.basename(log_file).split("_")[0]
        + "_"
        + os.path.basename(log_file).split("_")[1]
    )

    with open(parsed_json, "r") as j:
        data = json.loads(j.read())
    module = data["general"]["module"]
    config_folder = data["general"]["config"]
    validation_type = data["general"]["type"]
    tests_folder = module + "_tests"
    config_file = config_folder + module + ".json"
    if not os.path.isfile(config_file):
        log.error(
            f"specified {module} config file does not exist, you need first to create your configfile"
        )
        raise ValueError(config_file)
    if os.path.isdir(tests_folder):
        pytest.main(
            [
                tests_folder,
                "-vrA",
                "--jsonvalue",
                parsed_json,
                "-k",
                validation_type,
                "--capture",
                "fd",
                "--html",
                f"{output}/logs/{date}_{os.path.splitext(os.path.basename(parsed_json))[0]}.html",
                "--self-contained-html",
            ]
        )
    else:
        log.error(f"{tests_folder} does not exist, you need first to create your tests")
        raise ValueError(tests_folder)
