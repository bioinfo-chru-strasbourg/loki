# -*- coding: utf-8 -*-
import os
from os.path import join as osj
import json
import pytest
import logging as log


def read(args):
    input_json = args.json

    for parse_json in input_json:
        with open(parse_json, "r") as j:
            data = json.loads(j.read())
        tests_folder = data["general"]["module"] + "_tests"
        if os.path.isdir(tests_folder):
            pytest.main([tests_folder])
        else:
            log.error(
                f"{tests_folder} does not exist, you need first to create your tests"
            )
