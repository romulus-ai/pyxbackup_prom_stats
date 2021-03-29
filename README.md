
# pyxbackup_prom_stats

Collects some metrics from pyxbackup (https://github.com/dotmanila/pyxbackup) jobs and pushes them to a Prometheus Push Gateway.

This Project is heavily inspired by the greate rsnapshot metrics collector (https://github.com/kormat/rsnap_prom_stats)

## NOT YET READY!!!

Currently I am still collecting the possible output secenarios produced by pyxbackup, as long as I do not have the correct ones, I cannot create matching regular expressions.

## Compiling a binary

pyinstaller --onefile pyxbackup_prom_stats.py
Binary is stored in: dist/pyxbackup_prom_stats

## Collected Metrics:

    # HELP pyxbackup_start_time Timestamp pyxbackup started at
    # TYPE pyxbackup_start_time gauge
    pyxbackup_start_time{instance="{'instance': 'localhost'}"} 1.616751205e+09
    # HELP pyxbackup_end_time Timestamp pyxbackup finished at
    # TYPE pyxbackup_end_time gauge
    pyxbackup_end_time{instance="{'instance': 'localhost'}"} 1.616751325e+09
    # HELP pyxbackup_duration_seconds How long pyxbackup ran for
    # TYPE pyxbackup_duration_seconds gauge
    pyxbackup_duration_seconds{instance="{'instance': 'localhost'}"} 120.0
    # HELP pyxbackup_success Was the last run successful 0 ok 1 notok
    # TYPE pyxbackup_success gauge
    pyxbackup_success{instance="{'instance': 'localhost'}"} 0.0