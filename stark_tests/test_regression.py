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


def launch_module(loki_config, module_config):
    container = loki_config["general"]["container"]
    dataset_folder = module_config["general"]["inner_dataset_folder"]
    application = loki_config["input"]["application"]
    technology = loki_config["input"]["technology"]
    dataset = loki_config["input"]["dataset"]
    stark_application = module_config[application][technology][dataset]["application"]
    output = loki_config["general"]["output"]

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
    return osj(
        loki_config["general"]["output"], stark_application[:-4], "UNKNOWN", run_name
    )


def test_module(loki_config, module_config):
    if loki_config["input"]["analyse"] == "yes" and not loki_config["input"]["results"]:
        loki_config["input"]["results"] = launch_module(loki_config, module_config)
        stark_log_files = glob.glob(
            osj(loki_config["input"]["results"], "STARK.*.analysis.log")
        )

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

    vcf_comparison(loki_config)


def vcf_comparison(loki_config):
    d = datetime.datetime.now()
    date = f"{d.strftime('%Y%m%d')}-{d.strftime('%H%M%S')}"

    application = loki_config["input"]["application"]
    technology = loki_config["input"]["technology"]
    dataset = loki_config["input"]["dataset"]
    run_name = f"{application}_{technology}_{dataset}"

    results = glob.glob(osj(loki_config["input"]["results"], "*", ""))
    sample_list = []

    for sample in results:
        sample_list.append(os.path.basename(os.path.dirname(sample)))

    for sample in sample_list:
        run_sample_vcf = osj(
            loki_config["input"]["results"],
            f"{sample}/{sample}.reports/{sample}.final.vcf.gz",
        )
        run_sample_bed = osj(
            loki_config["input"]["results"],
            f"{sample}/{sample}.bed",
        )
        if os.path.isfile(run_sample_bed):
            if os.stat(run_sample_bed).st_size == 0:
                run_sample_bed = osj(
                    loki_config["input"]["results"],
                    f"{sample}/{sample}.bwamem.design.bed",
                )
        reference_sample_vcf = osj(
            loki_config["input"]["reference"],
            f"{sample}/{sample}.reports/{sample}.final.vcf.gz",
        )

        if not os.path.isfile(run_sample_vcf):
            run_sample_vcf = osj(
                loki_config["input"]["results"],
                f"{sample}/STARK/{sample}.reports/{sample}.final.vcf.gz",
            )
            run_sample_bed = osj(
                loki_config["input"]["results"],
                f"{sample}/STARK/{sample}.bed",
            )
            if os.stat(run_sample_bed).st_size == 0:
                run_sample_bed = osj(
                    loki_config["input"]["results"],
                    f"{sample}/STARK/{sample}.bwamem.design.bed",
                )
        if not os.path.isfile(reference_sample_vcf):
            reference_sample_vcf = osj(
                loki_config["input"]["reference"],
                f"{sample}/STARK/{sample}.reports/{sample}.final.vcf.gz",
            )

    loki_results = osj(loki_config["general"]["output"], f"LOKI_{date}_{run_name}")
    reference_vcf = f"ref_{os.path.basename(reference_sample_vcf)}"
    run_vcf = f"run_{os.path.basename(run_sample_vcf)}"

    if not os.path.isdir(loki_results):
        os.mkdir(osj(loki_results))

    shutil.copy(
        reference_sample_vcf,
        osj(
            loki_results,
            reference_vcf,
        ),
    )
    shutil.copy(
        run_sample_vcf,
        osj(
            loki_results,
            run_vcf,
        ),
    )
    shutil.copy(run_sample_bed, loki_results)

    reference_sample_vcf = osj(loki_results, reference_vcf)
    reference_sample_vcf_filtered = osj(loki_results, f"filtered_{reference_vcf}"[:-3])
    reference_sample_vcf_filtered_zipped = osj(
        loki_results, f"filtered_{reference_vcf}"
    )
    run_sample_vcf = osj(loki_results, run_vcf)
    run_sample_vcf_filtered = osj(loki_results, f"filtered_{run_vcf}"[:-3])
    run_sample_vcf_filtered_zipped = osj(loki_results, f"filtered_{run_vcf}")
    run_sample_bed = osj(loki_results, os.path.basename(run_sample_bed))

    subprocess.run(
        f"bedtools intersect -header -a {reference_sample_vcf} -b {run_sample_bed} > {reference_sample_vcf_filtered}",
        shell=True,
    )
    subprocess.run(
        f"bedtools intersect -header -a {run_sample_vcf} -b {run_sample_bed} > {run_sample_vcf_filtered}",
        shell=True,
    )

    subprocess.run(["bgzip", reference_sample_vcf_filtered])
    subprocess.run(["bgzip", run_sample_vcf_filtered])
    subprocess.run(["tabix", reference_sample_vcf_filtered_zipped])
    subprocess.run(["tabix", run_sample_vcf_filtered_zipped])

    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--name",
            f"loki_hap_py_{run_name}",
            "-t",
            "-w",
            loki_results,
            "-v",
            f"{loki_results}:{loki_results}",
            "-v",
            f"{os.path.dirname(loki_config['general']['genome'])}:{os.path.dirname(loki_config['general']['genome'])}",
            "pkrusche/hap.py",
            "/opt/hap.py/bin/hap.py",
            reference_sample_vcf_filtered_zipped,
            run_sample_vcf_filtered_zipped,
            "-r",
            loki_config["general"]["genome"],
            "-o",
            run_name,
        ]
    )

    def test_regression(loki_config, module_config):
        print(loki_config, module_config)
        # Cas1:Il n'y a pas de référence, on compare alors uniquement les statistiques entre les deux runs sur les samples existants.
        # Cas1:Il y a une référence, on compare alors les deux runs entre eux ainsi que CONTRE la référence pour chacun puis on compare les stats.
        # Attention, adapter le script de comparaison dans chacune des situations ainsi qu'en prenant en compte la présence de plusieurs vcf.
