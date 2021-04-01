#!/usr/local/bin/python3

import argparse
import logging
import re
import socket
import sys
import time

from datetime import datetime

from prometheus_client import (
    CollectorRegistry,
    Gauge,
    generate_latest,
    push_to_gateway,
)

DEFAULT_PUSH_GATEWAY = "localhost:9091"
DEFAULT_JOB_NAME = "pyxbackup"

localhost = socket.getfqdn()
gauges = {}

def main():
    parser = argparse.ArgumentParser(
        prog="pyxbackup-prom-stats",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--pushgw", default=DEFAULT_PUSH_GATEWAY,
                        help="Address of the pushgateway to publish to. If "
                        "set to '-' it will print the metrics to stdout instead.")
    parser.add_argument("--job", default=DEFAULT_JOB_NAME,
                        help="Pushgateway job name.")
    parser.add_argument("-v", action="store_true",
                        help="Print some information to stdout.")
    args = parser.parse_args()
    level = logging.WARNING
    if args.v:
        level = logging.INFO
    logging.basicConfig(
        format='[%(asctime)s] %(message)s',
        level=level)

    registry = setup_metrics()
    logging.info("Started")
    def_labels = {'instance': localhost}
    process_input(def_labels)
    logging.info("Finished reading output")
    if args.pushgw == "-":
        print(generate_latest(registry).decode("utf-8"))
    else:
        logging.info("publishing to pushgateway @ %s", args.pushgw)
        push_to_gateway(args.pushgw, job=args.job, registry=registry)


# Here we setup the registry for the metrics we want to collect
def setup_metrics():
    registry = CollectorRegistry()
    basic_labels = ['instance']
    gauges["pyxbackup_start_time"] = Gauge(
        "pyxbackup_start_time", "Timestamp pyxbackup started at", basic_labels,
        registry=registry)
    gauges["pyxbackup_end_time"] = Gauge(
        "pyxbackup_end_time", "Timestamp pyxbackup finished at", basic_labels,
        registry=registry)
    gauges["pyxbackup_duration_seconds"] = Gauge(
        "pyxbackup_duration_seconds", "How long pyxbackup ran until starting the pruning", basic_labels,
        registry=registry)
    gauges["pyxbackup_duration_preparing_seconds"] = Gauge(
        "pyxbackup_duration_preparing_seconds", "How long pyxbackup needed for preparing the backup", basic_labels,
        registry=registry)
    gauges["pyxbackup_duration_pruning_seconds"] = Gauge(
        "pyxbackup_duration_pruning_seconds", "How long pyxbackup needed for pruning the old backups", basic_labels,
        registry=registry)
    gauges["pyxbackup_duration_overall_seconds"] = Gauge(
        "pyxbackup_duration_overall_seconds", "How long pyxbackup needed for the complete backup process", basic_labels,
        registry=registry)
    gauges["pyxbackup_success"] = Gauge(
        "pyxbackup_success", "Was the last run successful 0 ok 1 notok", basic_labels,
        registry=registry)
    return registry

# Here we analyse the Lines from STDIN
def process_input(def_labels):
    starttimestamp_rx = re.compile(r'.*(\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2}).* (INFO: Running FULL backup, started at).*')

    preparingtimestamp_rx = re.compile(r'.*(\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2}).* (INFO: Preparing full backup:).*')

    endtimestamp_rx = re.compile(r'.*(\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2}).* (INFO: Cleaning up).*')

    pruningtimestamp_rx = re.compile(r'.*(\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2}).* (INFO: Pruning).*')

    runtime_error_rx = re.compile(r'.*(\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2}).* (ERROR:) .*')

    start_date_time_obj = None
    error = False

    starttimestamp = 0
    preparingtimestamp = 0
    endtimestamp = 0
    pruningtimestamp = 0
    backup_success = 0
    for line in read_lines():
        if not line:  # Skip blank lines
            continue
        # If we found an error line, we take the timestamp of that line as endtime!
        if runtime_error_rx.match(line):
            result = runtime_error_rx.search(line)
            end_date_time_obj = datetime.strptime(result.group(1), '%m/%d/%Y %H:%M:%S')

            backup_success = 1
            endtimestamp = end_date_time_obj.timestamp()
            pruningtimestamp = end_date_time_obj.timestamp()
            error = True
            continue
        if starttimestamp_rx.match(line):
            result = starttimestamp_rx.search(line)

            start_date_time_obj = datetime.strptime(result.group(1), '%m/%d/%Y %H:%M:%S')
            starttimestamp = start_date_time_obj.timestamp()
            continue
        if endtimestamp_rx.match(line):
            result = endtimestamp_rx.search(line)

            end_date_time_obj = datetime.strptime(result.group(1), '%m/%d/%Y %H:%M:%S')
            endtimestamp = end_date_time_obj.timestamp()
            continue
        if preparingtimestamp_rx.match(line):
            result = preparingtimestamp_rx.search(line)

            preparing_date_time_obj = datetime.strptime(result.group(1), '%m/%d/%Y %H:%M:%S')
            preparingtimestamp = preparing_date_time_obj.timestamp()
            continue
        if pruningtimestamp_rx.match(line):
            result = pruningtimestamp_rx.search(line)

            pruning_date_time_obj = datetime.strptime(result.group(1), '%m/%d/%Y %H:%M:%S')
            pruningtimestamp = pruning_date_time_obj.timestamp()
            continue

    gauges["pyxbackup_success"].labels(def_labels).set(backup_success)

    gauges["pyxbackup_start_time"].labels(def_labels).set(starttimestamp)
    gauges["pyxbackup_end_time"].labels(def_labels).set(endtimestamp)

    gauges["pyxbackup_duration_seconds"].labels(def_labels).set(endtimestamp - starttimestamp)
    gauges["pyxbackup_duration_preparing_seconds"].labels(def_labels).set(endtimestamp - preparingtimestamp)
    gauges["pyxbackup_duration_pruning_seconds"].labels(def_labels).set(pruningtimestamp - endtimestamp)
    gauges["pyxbackup_duration_overall_seconds"].labels(def_labels).set(pruningtimestamp - starttimestamp)

def read_lines():
    line = ""
    for l in sys.stdin:
        line += l.strip()
        if line.endswith("\\"):
            line = line.rstrip("\\")
            continue
        yield line
        line = ""


main()