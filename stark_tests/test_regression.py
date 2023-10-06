# -*- coding: utf-8 -*-
import os
import pytest
import glob
from os.path import join as osj
import logging as log
import subprocess
import json


def launch_module(loki_config, module_config):
    image = loki_config["general"]["image"]
    dataset_folder = module_config["general"]["inner_dataset_folder"]
    database_folder = module_config["general"]["outer_database_folder"]
    application = loki_config["input"]["application"]
    technology = loki_config["input"]["technology"]
    dataset = loki_config["input"]["dataset"]
    stark_application = module_config[application][technology][dataset]["application"]
    stark_output = loki_config["general"]["output"]
    actual_folder = os.getcwd()

    if stark_output == "":
        stark_output = actual_folder

    run_name = f"{application}_{technology}_{dataset}"
    run_path = osj(dataset_folder, application, technology, dataset)
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--name",
            f"{run_name}",
            "-v",
            f"{database_folder}:/STARK/databases",
            "-v",
            f"{actual_folder}:{actual_folder}",
            f"{image}",
            "STARK",
            f"--run={run_path}",
            f"--analysis_name={run_name}",
            f"--application={stark_application}",
            f"--output={stark_output}",
        ]
    )
    return osj(stark_output, "results", run_name)


def test_module(loki_config, module_config):
    if loki_config["input"]["analyse"] == "yes" and not loki_config["input"]["results"]:
        loki_config["input"]["results"] = launch_module(loki_config, module_config)
        stark_log_files = glob.glob(
            osj(loki_config["input"]["results"], "STARK.*.analysis.log")
        )

        for stark_log_file in stark_log_files:
            error_check = subprocess.check_output(
                [
                    "grep",
                    "\*\*\*",
                    stark_log_file,
                ]
            )
            assert error_check == ""

    vcf_comparison(loki_config, module_config)


def vcf_comparison(loki_config, module_config):
    results = glob.glob(osj(loki_config["input"]["results"], "*", ""))
    sample_list = []

    for sample in results:
        sample_list.append(os.path.basename(os.path.dirname(sample)))

    for sample in sample_list:
        run_sample_vcf = osj(
            loki_config["input"]["results"],
            f"{sample}/{sample}.reports/{sample}.final.vcf",
        )
        reference_sample_vcf = osj(
            loki_config["input"]["reference"],
            f"{sample}/{sample}.reports/{sample}.final.vcf",
        )

        if not os.path.isfile(run_sample_vcf):
            run_sample_vcf = osj(
                loki_config["input"]["results"],
                f"{sample}/STARK/{sample}.reports/{sample}.final.vcf",
            )
        if not os.path.isfile(reference_sample_vcf):
            reference_sample_vcf = osj(
                loki_config["input"]["reference"],
                f"{sample}/STARK/{sample}.reports/{sample}.final.vcf",
            )

        subprocess.run(
            [
                "vcftoolz",
                "compare",
                "--truth",
                reference_sample_vcf,
                run_sample_vcf,
            ]
        )


# Un score avec le CQI
# un score de non régression sur les autres samples
