# -*- coding: utf-8 -*-
import os
import pytest
from os.path import join as osj
import logging as log
import subprocess


def launch_module(loki_config, module_config):
    image = loki_config["general"]["image"]
    subprocess.run(["docker", "run", "--rm", image, "STARK", "-h"])


def test_module(loki_config, module_config):
    if (
        loki_config["input"]["analyse"] == "yes"
        and loki_config["input"]["noregres2"]
        and not loki_config["input"]["noregres1"]
    ):
        loki_config["input"]["noregres1"] = launch_module(loki_config, module_config)
    elif (
        loki_config["input"]["analyse"] == "yes"
        and loki_config["input"]["noregres1"]
        and not loki_config["input"]["noregres2"]
    ):
        loki_config["input"]["noregres2"] = launch_module(loki_config, module_config)

    noregres1 = osj(
        loki_config["input"]["noregres1"],
        "GC-BOR-MIS-CAP-BRCA-2V57",
        "GC-BOR-MIS-CAP-BRCA-2V57.reports",
        "GC-BOR-MIS-CAP-BRCA-2V57.final.vcf",
    )
    noregres2 = osj(
        loki_config["input"]["noregres2"],
        "GC-BOR-MIS-CAP-BRCA-2V57",
        "GC-BOR-MIS-CAP-BRCA-2V57.reports",
        "GC-BOR-MIS-CAP-BRCA-2V57.final.vcf",
    )
    print(noregres1)
    print(noregres2)


# comparer le vcf contre le témoin puis comparer les résultats
# potentiellement, calculer le temps d'analyse
