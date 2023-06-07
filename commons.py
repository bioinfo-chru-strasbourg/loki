# -*- coding: utf-8 -*-
import os
import logging as log
from os.path import join as osj
from threading import local
import sys
import time


def set_logger_info(args):
    mylog = log.getLogger()
    log_file = mylog.handlers[0].baseFilename
    info_file = log_file.replace(".log", ".info")

    if not os.path.isfile(info_file):
        python_command = " ".join(sys.argv)
        python_version = f"{sys.version.split(' ')[0].split('.')[0]}.{sys.version.split(' ')[0].split('.')[1]}"
        command = f"python{python_version} {python_command}"
        global time_seconds_start
        time_seconds_start = time.time() + 7200
        local_time = time.localtime(time_seconds_start)
        actual_time = time.strftime("%a %b %d %H:%M:%S %Y", local_time)
        start = actual_time

        logging = f"""Command: {command}
Start time: {start}\n"""

        with open(info_file, "a") as write_file:
            write_file.write(logging)

    else:
        time_seconds_end = time.time() + 7200
        local_time = time.localtime(time_seconds_end)
        actual_time = time.strftime("%a %b %d %H:%M:%S %Y", local_time)
        end = actual_time
        delta = time_seconds_end - time_seconds_start

        logging = f"""End time: {end}
Time run: {delta}"""

        with open(info_file, "a") as write_file:
            write_file.write(logging)


def logger_header(log_file):
    logging = f"""#########################
#         -loki-        #
# Author: Mateusz Rauch #
#########################

####################
#   Release: 1.0   #
####################

"""
    with open(log_file, "a") as write_file:
        write_file.write(logging)


def set_log_level(args):
    verbosity = args.verbosity
    json = args.json
    output = args.output
    json_names = ""

    for json_file in json:
        json_name = json_file.split("/")[-1].split(".")[0]
        json_names = f"{json_names}_{json_name}"

    time_seconds = time.time() + 7200
    local_time = time.localtime(time_seconds)
    actual_time = time.strftime("%Y%m%d_%H%M%S", local_time)

    log_file = f"{actual_time}{json_names}.log"

    log_file = osj(
        output,
        "logs",
        log_file,
    )

    if not os.path.isdir(osj(output, "logs")):
        os.mkdir(osj(output, "logs"))

    logger_header(log_file)

    configs = {
        "debug": log.DEBUG,
        "info": log.INFO,
        "warning": log.WARNING,
        "error": log.ERROR,
        "critical": log.CRITICAL,
    }
    if verbosity not in configs.keys():
        raise ValueError(
            "Unknown verbosity level:"
            + verbosity
            + "\nPlease use any in:"
            + configs.keys()
        )

    log.basicConfig(
        filename=log_file,
        force=True,
        filemode="a",
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=configs[verbosity],
    )


if __name__ == "__main__":
    pass
