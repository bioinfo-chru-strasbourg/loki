# -*- coding: utf-8 -*-
import os
import pytest
import glob
import shutil
from os.path import join as osj
import logging as log
import datetime
import subprocess
import re
import pandas as pd

from tools import bcftools, bedtools, bgzip, tabix


def test_module(loki_config, module_config):
    d = datetime.datetime.now()
    global date
    date = f"{d.strftime('%Y%m%d')}-{d.strftime('%H%M%S')}"
    # Checking if user asked for a STARK analysis
    if loki_config["input"]["analyse"] == "yes" and not loki_config["input"]["results"]:
        loki_config["input"]["results"] = launch_module(loki_config, module_config)
        stark_log_files = glob.glob(
            osj(loki_config["input"]["results"], "STARK.*.analysis.log")
        )
        # Checking if the STARK result is healthy (*** missing form the log)
        if len(stark_log_files) == 0:
            log.error(
                "Not found any log in the folder, please check results folder accessibility in your json"
            )
            raise ValueError(stark_log_files)

        for stark_log_file in stark_log_files:
            grep_result = subprocess.run(
                [
                    "grep",
                    "\*\*\*",
                    stark_log_file,
                ],
                capture_output=True,
                text=True,
            )
            error = grep_result.stdout.strip("\n")

            if error != "":
                log.error("Error in STARK analysis")
                raise ValueError(error)

    # vcf_comparison(loki_config, module_config)


def launch_module(loki_config, module_config):
    container = loki_config["general"]["container"]
    dataset_folder = module_config["general"]["inner_dataset_folder"]
    application = loki_config["input"]["application"]
    technology = loki_config["input"]["technology"]
    dataset = loki_config["input"]["dataset"]
    stark_application = module_config[application][technology][dataset]["application"]
    output = loki_config["general"]["output"]

    # Converting server path to STARK cli path
    if not output.startswith("/STARK"):
        output = re.sub(".*/STARK", "/STARK", output)

    run_name = f"{application}_{technology}_{dataset}"
    run_path = osj(dataset_folder, application, technology, dataset)
    subprocess.run(
        [
            "docker",
            "exec",
            f"{container}",
            "STARK",
            f"--run={run_path}",
            f"--analysis_name={run_name}",
            f"--application={stark_application}",
            f"--repository={output}",
        ]
    )
    # Deleting result folder from the CLI
    subprocess.run(
        [
            "docker",
            "exec",
            f"{container}",
            "rm",
            "-rf",
            f"/STARK/output/results/{run_name}",
        ]
    )
    # Selecting the run that just passed the container
    runs = glob.glob(
        osj(
            loki_config["general"]["output"],
            stark_application.split(".")[0],
            "*",
            run_name,
        )
    )

    for run in runs:
        if os.path.basename(run) == run_name:
            project = os.path.basename(os.path.dirname(run))

    return osj(
        loki_config["general"]["output"],
        stark_application.split(".")[0],
        project,
        run_name,
    )


def bedtools_intersect(a, b, output):
    subprocess.run(
        f"{bedtools} intersect -header -a {a} -b {b} > {output}",
        shell=True,
    )


def bcftools_annotate(input, output):
    subprocess.run(
        [
            bcftools,
            "annotate",
            "-x",
            "FMT/FT",
            "-o",
            output,
            input,
        ]
    )


def vcf_comparison(loki_config, module_config):
    application = loki_config["input"]["application"]
    technology = loki_config["input"]["technology"]
    dataset = loki_config["input"]["dataset"]
    run_name = f"{application}_{technology}_{dataset}"
    global loki_results
    loki_results = osj(loki_config["general"]["output"], f"LOKI_{date}_{run_name}")

    # Looking for all sample names
    sample_list = []
    sample_list = glob.glob(osj(loki_config["input"]["results"], "*", ""))
    sample_list_old = glob.glob(osj(loki_config["input"]["old_run"], "*", ""))

    useful_sample = os.path.basename(sample_list[0][:-1])

    # Looking for a bed file for futur comparison
    run_bed = osj(
        loki_config["input"]["results"],
        f"{useful_sample}/{useful_sample}.bed",
    )

    if os.path.isfile(run_bed):
        if os.stat(run_bed).st_size == 0:
            run_bed = osj(
                loki_config["input"]["results"],
                f"{useful_sample}/{useful_sample}.bwamem.design.bed",
            )
    if not os.path.isfile(run_bed):
        run_bed = osj(
            loki_config["input"]["results"],
            f"{useful_sample}/STARK/{useful_sample}.bed",
        )
        if os.stat(run_bed).st_size == 0:
            run_bed = osj(
                loki_config["input"]["results"],
                f"{useful_sample}/STARK/{useful_sample}.bwamem.design.bed",
            )

    run_bed_used = f"{run_name}.bed"

    if not os.path.isdir(loki_results):
        os.mkdir(osj(loki_results))

    shutil.copy(run_bed, osj(loki_results, run_bed_used))
    run_bed_used = osj(loki_results, run_bed_used)

    # Launching the process for each sample
    for sample in sample_list:
        sample = os.path.basename(sample[:-1])
        # Taking the vcf file for the loop sample from results or repository for the new run
        new_run_vcf = osj(
            loki_config["input"]["results"],
            f"{sample}/{sample}.reports/{sample}.final.vcf.gz",
        )
        if not os.path.isfile(new_run_vcf):
            new_run_vcf = osj(
                loki_config["input"]["results"],
                f"{sample}/{sample}.final.vcf.gz",
            )

        # Taking the vcf file for the loop sample from results or repository for the old run acting as reference
        old_run_vcf = osj(
            loki_config["input"]["old_run"],
            f"{sample}/{sample}.reports/{sample}.final.vcf.gz",
        )
        if not os.path.isfile(old_run_vcf):
            old_run_vcf = osj(
                loki_config["input"]["old_run"],
                f"{sample}/{sample}.final.vcf.gz",
            )

        # Defining name to identify vcf
        old_run_vcf_used = f"old_run_{os.path.basename(old_run_vcf)}"
        new_run_vcf_used = f"new_run_{os.path.basename(new_run_vcf)}"

        # Copying vcf and bed for the loop sample inside the results folder
        shutil.copy(
            old_run_vcf,
            osj(
                loki_results,
                old_run_vcf_used,
            ),
        )
        shutil.copy(
            new_run_vcf,
            osj(
                loki_results,
                new_run_vcf_used,
            ),
        )

        # Defining some temporary name for processed files
        old_run_vcf = osj(loki_results, old_run_vcf_used)
        old_run_vcf_filtered = osj(loki_results, f"filtered_{old_run_vcf_used}"[:-3])
        old_run_vcf_filtered_bcf_zipped = osj(
            loki_results, f"filtered_bcf_{old_run_vcf_used}"
        )
        old_run_vcf_filtered_bcf = old_run_vcf_filtered_bcf_zipped[:-3]

        new_run_vcf = osj(loki_results, new_run_vcf_used)
        new_run_vcf_filtered = osj(loki_results, f"filtered_{new_run_vcf_used}"[:-3])
        new_run_vcf_filtered_bcf_zipped = osj(
            loki_results, f"filtered_bcf_{new_run_vcf_used}"
        )
        new_run_vcf_filtered_bcf = new_run_vcf_filtered_bcf_zipped[:-3]

        # Bedtools intersect to only take variants in the run design
        bedtools_intersect(old_run_vcf, run_bed_used, old_run_vcf_filtered)
        bedtools_intersect(new_run_vcf, run_bed_used, new_run_vcf_filtered)

        # Bcftools to delete FT field causing problem for happy
        bcftools_annotate(old_run_vcf_filtered, old_run_vcf_filtered_bcf)
        bcftools_annotate(new_run_vcf_filtered, new_run_vcf_filtered_bcf)

        # Pre-processing for comparison
        subprocess.run([bgzip, old_run_vcf_filtered_bcf])
        subprocess.run([tabix, old_run_vcf_filtered_bcf_zipped])
        subprocess.run([bgzip, new_run_vcf_filtered_bcf])
        subprocess.run([tabix, new_run_vcf_filtered_bcf_zipped])

        if not os.path.isdir(osj(loki_results, sample)):
            os.mkdir(osj(loki_results, sample))

        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--name",
                f"loki_happy_{run_name}_new_run_against_old_run",
                "-t",
                "-w",
                loki_results,
                "-v",
                f"{loki_results}:{loki_results}",
                "-v",
                f"{os.path.dirname(loki_config['general']['genome'])}:{os.path.dirname(loki_config['general']['genome'])}",
                "hap.py:0.3.15",
                "/opt/hap.py/bin/hap.py",
                old_run_vcf_filtered_bcf_zipped,
                new_run_vcf_filtered_bcf_zipped,
                "-r",
                loki_config["general"]["genome"],
                "-o",
                f"{sample}/{sample}",
                "--no-roc",
                "--no-json",
                "--usefiltered-truth",
                "--engine=vcfeval",
                "--engine-vcfeval-template",
                "hg19",
            ]
        )

        os.remove(old_run_vcf_filtered)
        os.remove(new_run_vcf_filtered)
        sample_files = glob.glob(osj(loki_results, f"*{sample}*"))
        for file in sample_files:
            shutil.move(file, osj(loki_results, sample))


def test_metrics(loki_config, module_config):
    loki_results = osj(
        loki_config["general"]["output"],
        "LOKI_20231030-173402_tiny_monosample_dataset1",
    )
    loki_samples = glob.glob(osj(loki_results, "*", ""))
    for result in loki_samples:
        result = os.path.basename(result[:-1])
        log.info(f"Checking metrics for {result}")
        df = pd.read_csv(osj(loki_results, result, f"{result}.summary.csv"))
        all_row = df[df["Filter"] == "ALL"].index.values
        for i in all_row:
            print(i)
        # assert df.loc[all_row, "METRIC.Recall"].item() == 1.0
