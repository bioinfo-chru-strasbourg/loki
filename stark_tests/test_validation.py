# -*- coding: utf-8 -*-
import os
import pytest
from os.path import join as osj
import logging as log


def test_print_json(json):
    log.info(json)


def test_add():
    assert 2 + 2 == 5
