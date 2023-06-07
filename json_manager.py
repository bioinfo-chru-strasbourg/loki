# -*- coding: utf-8 -*-
import os
from os.path import join as osj
import json


def read(args):
    input_json = args.json

    for parse_json in input_json:
        with open(parse_json, "r") as j:
            data = json.loads(j.read())
        return data
