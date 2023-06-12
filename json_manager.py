# -*- coding: utf-8 -*-
import os
from os.path import join as osj
import json
import pytest
import logging as log
import subprocess


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
    tests_folder = data["general"]["module"] + "_tests"
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
