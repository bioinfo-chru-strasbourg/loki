# -*- coding: utf-8 -*-
import os
import pytest
from os.path import join as osj
import logging as log


class argjson:
    def __init__(self, name):
        self.name = name

    def module(self):
        print(self)
        return self.module()


def test_add():
    assert 2 + 2 == 5


def test_module(jsonvalue):
    print(jsonvalue)
