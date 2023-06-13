# -*- coding: utf-8 -*-
import os
from os.path import join as osj
import json
import pytest
import logging as log
import subprocess


def json_checker(parsed_json):
    with open(parsed_json, "r") as j:
        data = json.loads(j.read())
    config_folder = data["general"]["config"]
    results = data["input"]["results"]
    analyse = data["input"]["analyse"]

    if not os.path.isdir(config_folder):
        log.error(
            f"specified {config_folder} config folder does not exist, please verify it"
        )
        raise ValueError(config_folder)

    if analyse != "no" and analyse != "yes":
        log.error(f"{analyse} value must be yes or no, please verify it")
        raise ValueError(analyse)

    if analyse == "no" and not os.path.isdir(results):
        log.error(f"specified {results} run folder does not exist, please verify it")
        raise ValueError(results)


def read(parsed_json, output):
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
    tests_folder = module + "_tests"
    config_file = config_folder + module + "_config.json"
    if not os.path.isfile(config_file):
        log.error(
            f"specified {module} config file does not exist, you need first to create your configfile"
        )
        raise ValueError(config_file)
    if os.path.isdir(tests_folder):
        pytest.main(
            [
                tests_folder,
                "-vsrA",
                "--jsonvalue",
                parsed_json,
                "--capture",
                "sys",
                "--html",
                f"{output}/logs/{date}_{os.path.splitext(os.path.basename(parsed_json))[0]}.html",
                "--self-contained-html",
            ]
        )
    else:
        log.error(f"{tests_folder} does not exist, you need first to create your tests")
        raise ValueError(tests_folder)
