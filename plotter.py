"""
Check the queue time for jobs submitted on ANVIL

I would think it works for other clusters, too
    Tested it on four other clusters (NERSC, CHPC, UAHPC, and ours)

----------------
June-August 2026
----------------
"""

import numpy as np
import warnings
import shlex
import subprocess
from typing import List, Tuple, Optional, Union
import datetime
import pandas as pd
import seaborn as sns
from slurm_waitmap.conf import *
import argparse
from os.path import splitext
import matplotlib.pyplot as plt


######################################## CONSTANTS ########################################
EXPECTED_FORMAT = [
    "ReqCPUS",
    "ReqNodes",
    "ReqMem",
    "Timelimit",
    "Submit",
    "Start",
]
GB_TO_MB = 1024
# QOS=None

######################################## FOR PLOTTING, IN ADVANCE ########################################
if len(CPU_BINS) < 3:
    raise ValueError(f"There must be at least 3 bins for requested cpus")
if len(TIME_BINS) < 3:
    raise ValueError(f"There must be at least 3 bins for timelimits")

CPU_LABELS = [
    (
        str(cpu_bin)
        if index == 0
        else (
            f"{cpu_bin}+"
            if index == len(CPU_BINS) - 1
            else f"{cpu_bin}-{CPU_BINS[index+1]-1}"
        )
    )
    for index, cpu_bin in enumerate(CPU_BINS)
]
TIME_LABELS = [
    (
        f"<{TIME_BINS[index+1]}"
        if index == 0
        else (
            f"{time_bin}+"
            if index == len(TIME_BINS) - 1
            else f"{time_bin}-{TIME_BINS[index+1]}"
        )
    )
    for index, time_bin in enumerate(TIME_BINS)
]

CPU_BIN_EDGES = CPU_BINS + [np.inf]
TIME_BIN_EDGES = TIME_BINS + [np.inf]


######################################## GATHER STATS ########################################
def decide_on_timings(
    start_time: Optional[str] = START_TIME,
    end_time: Optional[str] = END_TIME,
    verbose: Optional[bool] = VERBOSE,
) -> Tuple[str, str]:
    """
    Given the user's start and end times, return
        start and end times formatted as I need them
    start_time and end_time (if given) should be in the format YYYY-MM-DDTHH:MM
    """
    ##basic sanity checks
    if end_time and len(end_time) != len(EXPECTED_DATE_FORMAT):
        raise ValueError(
            f"End time ({end_time}) not in expected format ({EXPECTED_DATE_FORMAT})"
        )
    if start_time and len(start_time) != len(EXPECTED_DATE_FORMAT):
        raise ValueError(
            f"Start time ({start_time}) not in expected format ({EXPECTED_DATE_FORMAT})"
        )

    this_moment = datetime.datetime.now()
    reconvert = False
    if start_time is None:
        reconvert = True
        if end_time is None:
            if verbose:
                warnings.warn(
                    f"""
                Neither start nor end time given. Will collect data from the
                past {DEFAULT_DAYS} days"""
                )
            end_time = this_moment
        else:
            if verbose:
                warnings.warn(
                    f"""
                Start time not given, but end time given.
                Will collect data from {DEFAULT_DAYS} days before end time"""
                )
            end_time = datetime.datetime.fromisoformat(end_time)
        start_time = end_time - datetime.timedelta(days=DEFAULT_DAYS)
        start_time = (
            f"{start_time.year}-{str(start_time.month).zfill(2)}"
            f"-{str(start_time.day).zfill(2)}"
            f"T{str(start_time.hour).zfill(2)}:{str(start_time.minute).zfill(2)}"
        )
    else:
        if end_time is None:
            if verbose:
                warnings.warn(
                    f"""
                Start time given, but end time not given.
                Will set end time to current moment"""
                )
            end_time = this_moment
            reconvert = True

    if reconvert:
        end_time = (
            f"{end_time.year}-{str(end_time.month).zfill(2)}"
            f"-{str(end_time.day).zfill(2)}"
            f"T{str(end_time.hour).zfill(2)}:{str(end_time.minute).zfill(2)}"
        )

    return start_time, end_time


def run_sacct(
    *,
    start_time: Optional[str] = START_TIME,
    end_time: Optional[str] = END_TIME,
    partitions: Optional[Union[str, List[str]]] = PARTITION,
    #    qos: Optional[Union[str, List[str]]] = QOS,
    usernames: Optional[Union[str, List[str]]] = USERNAME,
    verbose: Optional[bool] = VERBOSE,
) -> int:
    """
    Run sacct

    Given:
        start_time (None | str):                earliest possible start time, format: YYYY-MM-DDTHH:MM
        end_time (None | str):                  latest possible start time, format: YYYY-MM-DDTHH:MM.
        partitions (None | str | List[str]):    partition(s). Default will include all partitions
        usernames (None | str | List[str]):     username(s). Default will include all users.

    Collects:
        ReqCPUS                     requested CPUs
        ReqNodes                    requested nodes
        ReqMem                      requested memory in MB
        TimeLimit                   requested time limit
        Submit                      submit times
        Start                       start times

    Returns:
        0                           if succeeded
        1                           else
    """
    start_time, end_time = decide_on_timings(
        start_time=start_time, end_time=end_time, verbose=verbose
    )
    exitcode = 0
    user_string = f"--user {','.join(usernames)}" if usernames else "--allusers"
    partition_string = f"--partition {','.join(partitions)}" if partitions else " "
    #    qos_string = f"--qos '{qos}'" if qos else " "
    accounting_command = (
        f"sacct {user_string} {partition_string} "  # {qos_string} "
        f"--starttime='{start_time}' --endtime='{end_time}' "
        f"--format='ReqCPUS,ReqNodes,ReqMem,TimeLimit,Submit,Start' "
        f"--parsable2 -X --delimiter ',' --noconvert"
    )
    #    print(accounting_command)
    accounting_command_ = shlex.split(accounting_command)
    with open(LOGFILE, "w", newline="", encoding="utf-8") as stdout, open(
        ERRFILE, "w"
    ) as stderr:
        try:
            run = subprocess.run(
                accounting_command_, stdout=stdout, stderr=stderr, check=True
            )
        except subprocess.CalledProcessError as cpe:
            print(f"Could not run command ({accounting_command})\n Error:\t{cpe}")
            exitcode = 1

    return exitcode


def get_statistics(
    start_time: Optional[str] = START_TIME,
    end_time: Optional[str] = END_TIME,
    partitions: Optional[Union[str, List[str]]] = PARTITION,
    #    qos: Optional[Union[str, List[str]]] = QOS,
    usernames: Optional[Union[str, List[str]]] = USERNAME,
    verbose: Optional[bool] = VERBOSE,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Given:
        start_time (None | str):                earliest possible start time, format: YYYY-MM-DDTHH:MM
        end_time (None | str):                  latest possible start time, format: YYYY-MM-DDTHH:MM.
        partitions (None | str | List[str]):    partition(s). Default will include all partitions
        usernames (None | str | List[str]):     username(s). Default will include all users.
    For start_time and end_time, see decide_on_timings above for their defaults

    Returns:
        ReqCPUS                     requested CPUs
        NumNodes                    requested nodes
        ReqMem_gb                   requested memory in GB
        TimeLimit                   requested time limit in hrs
        QueueWait                   wait time in hrs

    TimeLimit, ReqMem_gb, and NumNodes aren't needed at the moment
    but collected in case I choose to plot them in a future version. Who knows?
    """
    failure_ = run_sacct(
        start_time=start_time,
        end_time=end_time,
        partitions=partitions,
        #            qos=qos,
        usernames=usernames,
        verbose=verbose,
    )
    if failure_:
        raise ValueError(
            f"Could not run sacct successfully. Check {ERRFILE} for details"
        )

    on_bad_lines = "warn"  #such instances that multiple partitions are specified,
    #for example. The user can inspect the line for themselves.
    #Maybe I could fix less handwavingly later, but never you mind that
    df = pd.read_csv(LOGFILE, delimiter=",", on_bad_lines=on_bad_lines)
    title = df.columns.to_list()
    if title != EXPECTED_FORMAT:
        raise ValueError(f"{title} is not in the expected format: {EXPECTED_FORMAT}")

    reqcpus, numnodes, reqmem_mb, timelimit, submit, start = [
        df[i].to_numpy() for i in EXPECTED_FORMAT
    ]

    if len(reqcpus) == 0:
        raise ValueError("No sacct records found for the specified filters.")

    #remove invalid records like start="Unknown"
    start_ = pd.to_datetime(start, errors="coerce", format="%Y-%m-%dT%H:%M:%S",)
    mask = ~pd.isna(start_)
    reqcpus, numnodes, reqmem_mb, timelimit, submit, start = (
        reqcpus[mask].astype(np.int16),
        numnodes[mask].astype(np.int16),
        reqmem_mb[mask],
        timelimit[mask].astype(str),
        submit[mask].astype(str),
        start[mask].astype(str),
    )
    #convert submit and start into queue wait time in hours
    submit = np.array([datetime.datetime.fromisoformat(i) for i in submit])
    start = np.array([datetime.datetime.fromisoformat(i) for i in start])
    queue_wait_time = start - submit
    queue_wait_hrs = np.array([i.total_seconds() / 3_600 for i in queue_wait_time])
    #convert timelimit into hours
    timelimit = np.where(
        np.char.count(timelimit, "-") == 1,
        np.char.replace(timelimit, "-", " days ", count=1),
        timelimit,
    )  #replace "15-" with "15 days", for example
    timelimit_hrs = pd.to_timedelta(timelimit).total_seconds() / 3_600

    reqmem_gb = np.array([int(i.removesuffix("M")) / GB_TO_MB for i in reqmem_mb])

    return (reqcpus, numnodes, reqmem_gb, timelimit_hrs, queue_wait_hrs)


######################################## PLOTTING ########################################
def plot_wait_time(
    start_time: Optional[str] = START_TIME,
    end_time: Optional[str] = END_TIME,
    partitions: Optional[Union[str, List[str]]] = PARTITION,
    #    qos: Optional[Union[str, List[str]]] = QOS,
    usernames: Optional[Union[str, List[str]]] = USERNAME,
    output_heatmap: str = OUTPUT_HEATMAP,
    output_counts: str = OUTPUT_COUNTS,
    verbose: bool = VERBOSE,
    show: bool = SHOW,
):
    """
    1. Plot average wait times vs CPUs requested
    2. Then plot counts within each bin of the plot in (1),
       so we know how statistically reliable the plot is
    """
    output_heatmap=splitext(output_heatmap)[0] + ".png"
    output_counts=splitext(output_counts)[0] + ".png"
    reqcpus, *_, timelimit_hrs, queue_wait_hrs = get_statistics(
        start_time=start_time,
        end_time=end_time,
        partitions=partitions,
        #            qos=qos,
        usernames=usernames,
        verbose=verbose,
    )
    df = pd.DataFrame(
        {
            "ReqCPUS": np.array(reqcpus),
            "Timelimit_hrs": np.array(timelimit_hrs),
            "Wait_hrs": np.array(queue_wait_hrs),
        }
    )
    df["CPU_bin"] = pd.cut(
        df["ReqCPUS"],
        bins=CPU_BIN_EDGES,
        labels=CPU_LABELS,
        include_lowest=True,
        right=False,
    )
    df["Timelimit_bin"] = pd.cut(
        df["Timelimit_hrs"],
        bins=TIME_BIN_EDGES,
        labels=TIME_LABELS,
        include_lowest=True,
        right=False, #exclude the upper limit, of course
    )
    heatmap = df.pivot_table(
        index="CPU_bin",
        columns="Timelimit_bin",
        values="Wait_hrs",
        aggfunc="mean",
        dropna=False,
    )
    counts = df.pivot_table(
        index="CPU_bin",
        columns="Timelimit_bin",
        values="Wait_hrs",
        aggfunc="size",
        dropna=False,
    )
    if heatmap.shape != counts.shape:
        raise ValueError("unexpected shape mismatch between heatmap and counts objects")

    fig, axes = plt.subplots(figsize=FIGSIZE)
    sns.heatmap(
        heatmap,
        annot=ANNOTATE_PLOT,
        fmt=".2f",
        cmap=CMAP,
        linewidths=LW,
        cbar_kws={"label": "Average Queue Wait Time (hrs)"},
        ax=axes,
    )
    axes.set_xlabel("Timelimit (hours)")
    axes.set_ylabel("Number of Cores Requested")
    axes.set_title("Average Queue Wait Time (hours)")
    try:
        plt.savefig(output_heatmap, dpi=DPI)
    except PermissionError: #are we in some root directory, I wonder?
        print(f"could not save {output_heatmap}")
    if show:
        plt.show(block=BLOCK)

    fig, axes = plt.subplots(figsize=FIGSIZE)
    sns.heatmap(
        counts,
        annot=ANNOTATE_PLOT,
        fmt=".0f",#"d",
        cmap=CMAP,
        linewidths=LW,
        cbar_kws={"label": "Number of Jobs"},
        ax=axes,
    )
    axes.set_xlabel("Timelimit (hours)")
    axes.set_ylabel("Number of Cores Requested")
    axes.set_title("Total Number of Jobs")
    try:
        plt.savefig(output_counts, dpi=DPI)
    except PermissionError:
        print(f"could not save {output_counts}")
    if show:
        plt.show()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plots the average queue wait time for jobs. Queue wait time may be artificially high if job sbatch had --dependency or --begin."
    )

    parser.add_argument(
        "--start-time",
        "-s",
        type=str,
        default=START_TIME,
        help=f"Earliest possible job start time, format: YYYY-MM-DDTHH:MM. Default = {START_TIME}",
    )

    parser.add_argument(
        "--end-time",
        "-e",
        type=str,
        default=END_TIME,
        help=f"Latest possible job start time, format: YYYY-MM-DDTHH:MM. Default = {END_TIME}",
    )

    parser.add_argument(
        "--partitions",
        "-p",
        nargs="+",
        default=PARTITION,
        help=f"Partition(s) to include. Default = {PARTITION}",
    )

    parser.add_argument(
        "--usernames",
        "-u",
        nargs="+",
        default=USERNAME,
        help=f"Username(s) to include. Default = {USERNAME}",
    )

    parser.add_argument(
        "--output-heatmap",
        "-oh",
        type=str,
        default=OUTPUT_HEATMAP,
        help=f"Output file for the heatmap of queue wait times. Default = {OUTPUT_HEATMAP}",
    )

    parser.add_argument(
        "--output-counts",
        "-oc",
        type=str,
        default=OUTPUT_COUNTS,
        help=f"Output file for the heatmap of counts for each entry in the queue wait times heatmap. Default = {OUTPUT_COUNTS}",
    )

    parser.add_argument(
        "--show",
        action="store_true",
        default=SHOW,
        help=f"Display plots. Default = {SHOW}",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        default=VERBOSE,
        help=f"Print extra information. Default = {VERBOSE}",
    )

    args = parser.parse_args()

    start_time, end_time, partitions, usernames, verbose, show, output_heatmap, output_counts = (
        args.start_time,
        args.end_time,
        args.partitions,
        args.usernames,
        args.verbose,
        args.show,
        args.output_heatmap,
        args.output_counts
    )
    if verbose:
        if not partitions:
            warnings.warn("Partition(s) not specified. Will analyze jobs submitted to all partitions")
        if not usernames:
            warnings.warn("Username(s) not specified. Will analyze jobs for all users")

    plot_wait_time(
        start_time=start_time,
        end_time=end_time,
        partitions=partitions,
        #            qos=qos,
        usernames=usernames,
        output_heatmap=output_heatmap,
        output_counts=output_counts,
        verbose=verbose,
        show=show,
    )


if __name__ == "__main__":
    main()

