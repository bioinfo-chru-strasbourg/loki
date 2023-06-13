# -*- coding: utf-8 -*-
import os
import pytest
from os.path import join as osj
import logging as log


def test_module(loki_config):
    assert loki_config["general"]["module"] == "stark"


def test_module2(module_config):
    print(module_config)
