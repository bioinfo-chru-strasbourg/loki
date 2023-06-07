# !/usr/bin/python
# !/bin/sh
# !/usr/tcl/bin
# -*- coding: utf-8 -*-
"""
###############################
##							 ##
##		loki validation		 ##
##	Author : Mateusz RAUCH	 ##
##							 ##
###############################
"""

import argparse
import sys
import os
import logging as log
import textwrap
import commons
import json_manager

# Il faut que le script crée un directory de test pour pytest


def main(args):
    original_umask = os.umask(0o000)
    commons.set_log_level(args)
    commons.set_logger_info(args)
    json_manager.read(args)
    commons.set_logger_info(args)
    os.umask(original_umask)


def parse_args():
    # Main parser
    main_parser = argparse.ArgumentParser(
        prog="loki",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
            ------------------------------------------
                Be the best validator of your team
                            -loki-
            (vaLidation tOol for starK Infrastructure)
            ------------------------------------------"""
        ),
    )
    main_parser.add_argument(
        "-v",
        "--verbosity",
        type=str,
        default="info",
        help="Verbosity level, DEBUG, INFO, WARNING, ERROR, CRITICAL. Default value is INFO",
    )
    main_parser.add_argument(
        "-j",
        "--json",
        required=True,
        type=str,
        help="path to one or many json files containing all informations about the analysis and validation process",
        nargs="*",
    )
    main_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=".",
        help="path to the wanted output, by default current directory",
    )

    args = main_parser.parse_args()
    main(args)


if __name__ == "__main__":
    parse_args()
