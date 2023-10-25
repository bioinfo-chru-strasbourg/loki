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

from tools import bcftools, bedtools, bgzip, tabix


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

    vcf_comparison(loki_config, module_config)


def happy(workdir, container_name, truth, query, output_prefix, loki_config):
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name,
            "-t",
            "-w",
            workdir,
            "-v",
            f"{workdir}:{workdir}",
            "-v",
            f"{os.path.dirname(loki_config['general']['genome'])}:{os.path.dirname(loki_config['general']['genome'])}",
            "hap.py:0.3.15",
            "/opt/hap.py/bin/hap.py",
            truth,
            query,
            "-r",
            loki_config["general"]["genome"],
            "-o",
            output_prefix,
            "--no-roc",
            "--no-json",
        ]
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
    d = datetime.datetime.now()
    date = f"{d.strftime('%Y%m%d')}-{d.strftime('%H%M%S')}"

    application = loki_config["input"]["application"]
    technology = loki_config["input"]["technology"]
    dataset = loki_config["input"]["dataset"]
    run_name = f"{application}_{technology}_{dataset}"

    if (len(module_config[application][technology][dataset]["samples"]) != 1) or (
        len(module_config[application][technology][dataset]["samples"]) == 1
        and module_config[application][technology][dataset]["run_ref"] == ""
    ):
        new_run_vcf = glob.glob(
            osj(
                loki_config["input"]["results"],
                "STARK.*.variants.Design.vcf.gz",
            )
        )[0]
        run_bed = osj(
            loki_config["input"]["results"],
            f"{module_config[application][technology][dataset]['samples'][0]}/{module_config[application][technology][dataset]['samples'][0]}.bed",
        )
        if os.path.isfile(run_bed):
            if os.stat(run_bed).st_size == 0:
                run_bed = osj(
                    loki_config["input"]["results"],
                    f"{module_config[application][technology][dataset]['samples'][0]}/{module_config[application][technology][dataset]['samples'][0]}.bwamem.design.bed",
                )
        old_run_vcf = glob.glob(
            osj(
                loki_config["input"]["old_run"],
                "STARK.*.variants.Design.vcf.gz",
            )
        )[0]

        if not os.path.isfile(run_bed):
            run_bed = osj(
                loki_config["input"]["results"],
                f"{module_config[application][technology][dataset]['samples'][0]}/STARK/{module_config[application][technology][dataset]['samples'][0]}.bed",
            )
            if os.stat(run_bed).st_size == 0:
                run_bed = osj(
                    loki_config["input"]["results"],
                    f"{module_config[application][technology][dataset]['samples'][0]}/STARK/{module_config[application][technology][dataset]['samples'][0]}.bwamem.design.bed",
                )

        loki_results = osj(loki_config["general"]["output"], f"LOKI_{date}_{run_name}")
        old_run_vcf_used = f"old_run_{os.path.basename(old_run_vcf)}"
        new_run_vcf_used = f"new_run_{os.path.basename(new_run_vcf)}"
        run_bed_used = f"{run_name}.bed"

        if not os.path.isdir(loki_results):
            os.mkdir(osj(loki_results))

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
        shutil.copy(run_bed, osj(loki_results, run_bed_used))

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

        run_bed_used = osj(loki_results, run_bed_used)

        bedtools_intersect(old_run_vcf, run_bed_used, old_run_vcf_filtered)
        bedtools_intersect(new_run_vcf, run_bed_used, new_run_vcf_filtered)

        bcftools_annotate(old_run_vcf_filtered, old_run_vcf_filtered_bcf)
        bcftools_annotate(new_run_vcf_filtered, new_run_vcf_filtered_bcf)

        subprocess.run([bgzip, old_run_vcf_filtered_bcf])
        subprocess.run([tabix, old_run_vcf_filtered_bcf_zipped])
        subprocess.run([bgzip, new_run_vcf_filtered_bcf])
        subprocess.run([tabix, new_run_vcf_filtered_bcf_zipped])

        happy(
            loki_results,
            f"loki_happy_{run_name}_new_run_against_old_run",
            old_run_vcf_filtered_bcf_zipped,
            new_run_vcf_filtered_bcf_zipped,
            "new_run_against_old_run",
            loki_config,
        )

        os.remove(old_run_vcf_filtered)
        os.remove(new_run_vcf_filtered)

    if module_config[application][technology][dataset]["run_ref"] != "":
        ref = module_config[application][technology][dataset]["ref"]
        run_ref = module_config[application][technology][dataset]["run_ref"]
        ref_file = osj(
            module_config["general"]["outer_dataset_folder"], "references", ref
        )
        old_run_ref_vcf = osj(
            loki_config["input"]["old_run"], run_ref, f"{run_ref}.final.vcf.gz"
        )
        new_run_ref_vcf = osj(
            loki_config["input"]["results"], run_ref, f"{run_ref}.final.vcf.gz"
        )
        old_run_ref_vcf_used = f"old_run_{os.path.basename(old_run_ref_vcf)}"
        new_run_ref_vcf_used = f"new_run_{os.path.basename(new_run_ref_vcf)}"
        ref_file_used = f"ref_file_{os.path.basename(ref_file)}"

        shutil.copy(
            new_run_ref_vcf,
            osj(
                loki_results,
                new_run_ref_vcf_used,
            ),
        )
        shutil.copy(
            old_run_ref_vcf,
            osj(
                loki_results,
                old_run_ref_vcf_used,
            ),
        )
        shutil.copy(ref_file, osj(loki_results, ref_file_used))

        old_run_ref_vcf = osj(loki_results, old_run_ref_vcf_used)
        old_run_ref_vcf_filtered = osj(
            loki_results, f"filtered_{old_run_ref_vcf_used}"[:-3]
        )
        old_run_ref_vcf_filtered_bcf_zipped = osj(
            loki_results, f"filtered_bcf_{old_run_ref_vcf_used}"
        )
        old_run_ref_vcf_filtered_bcf = old_run_ref_vcf_filtered_bcf_zipped[:-3]

        new_run_ref_vcf = osj(loki_results, new_run_ref_vcf_used)
        new_run_ref_vcf_filtered = osj(
            loki_results, f"filtered_{new_run_ref_vcf_used}"[:-3]
        )
        new_run_ref_vcf_filtered_bcf_zipped = osj(
            loki_results, f"filtered_bcf_{new_run_ref_vcf_used}"
        )
        new_run_ref_vcf_filtered_bcf = new_run_ref_vcf_filtered_bcf_zipped[:-3]

        ref_file = osj(loki_results, ref_file_used)
        ref_file_filtered = osj(loki_results, f"filtered_{ref_file_used}"[:-3])
        ref_file_filtered_zipped = osj(loki_results, f"filtered_{ref_file_used}")

        bedtools_intersect(old_run_ref_vcf, run_bed_used, old_run_ref_vcf_filtered)
        bedtools_intersect(new_run_ref_vcf, run_bed_used, new_run_ref_vcf_filtered)
        bedtools_intersect(ref_file, run_bed_used, ref_file_filtered)

        bcftools_annotate(old_run_ref_vcf_filtered, old_run_ref_vcf_filtered_bcf)
        bcftools_annotate(new_run_ref_vcf_filtered, new_run_ref_vcf_filtered_bcf)

        subprocess.run([bgzip, old_run_ref_vcf_filtered_bcf])
        subprocess.run([tabix, old_run_ref_vcf_filtered_bcf_zipped])
        subprocess.run([bgzip, new_run_ref_vcf_filtered_bcf])
        subprocess.run([tabix, new_run_ref_vcf_filtered_bcf_zipped])
        subprocess.run([bgzip, ref_file_filtered])
        subprocess.run([tabix, ref_file_filtered_zipped])

        happy(
            loki_results,
            f"loki_happy_{run_name}_new_ref_against_old_ref",
            old_run_ref_vcf_filtered_bcf_zipped,
            new_run_ref_vcf_filtered_bcf_zipped,
            "new_ref_against_old_ref",
            loki_config,
        )
        happy(
            loki_results,
            f"loki_happy_{run_name}_old_ref_against_ref",
            ref_file_filtered_zipped,
            old_run_ref_vcf_filtered_bcf_zipped,
            "old_ref_against_ref",
            loki_config,
        )
        happy(
            loki_results,
            f"loki_happy_{run_name}_new_ref_against_ref",
            ref_file_filtered_zipped,
            new_run_ref_vcf_filtered_bcf_zipped,
            "new_run_against_ref",
            loki_config,
        )

    def test_regression(loki_config, module_config):
        print(loki_config, module_config)
