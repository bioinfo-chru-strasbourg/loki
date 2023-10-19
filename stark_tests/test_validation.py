# -*- coding: utf-8 -*-
import os
import pytest
from os.path import join as osj
import logging as log


def test_module(loki_config):
    assert loki_config["general"]["module"] == "stark"


def test_module2(module_config):
    print(module_config)


# test validation va servir à valider les metrics globales:
# le run est terminé
# les bams sont présents
# les fastq sont non vide et présents, vérifier le header
# il y a un nombre classique de variants dans le run
# vérifier que le rapport stark existe, le nombre de variants, le Q30, le % de duplication, le % on target
# vérifier que le cram est ok
