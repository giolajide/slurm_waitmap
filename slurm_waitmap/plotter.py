"""
Check the queue time for jobs submitted
mid-2026
"""

import numpy as np
import warnings
import shlex
import subprocess
from typing import List, Tuple, Optional, Union, Literal
import datetime
import pandas as pd
import seaborn as sns
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

CPU_BINS = [2, 4, 8, 16, 32]  # make sure to be at least 2 elements
TIME_BINS = [1, 8, 24]  # make sure to be at least 2 elements
VERBOSE = False
DEFAULT_DAYS = 14
ERRFILE = "slurm_waitmap_sacct.err"
LOGFILE = "slurm_waitmap_sacct.csv"
SHOW = False
FIGSIZE = (11, 8)
ANNOTATE_PLOT = True
LW = 0.5
CMAP = "RdYlGn_r"  # similar to https://www.nersc.gov/users/status/queue-wait-times, I think
BLOCK = False
DPI = 100
OUTPUT_HEATMAP = "wait_times.png"
OUTPUT_COUNTS = "counts.png"

END_TIME = None  # or some date in the format YYYY-MM-DDTHH:MM
START_TIME = None  # or some date in the format YYYY-MM-DDTHH:MM
PARTITION = None
USERNAME = None
EXPECTED_DATE_FORMAT = "YYYY-MM-DDTHH:MM"


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

    TODO: validate that start_time < end_time
    """
    ##basic sanity checks
    #proper formatting
    if end_time:
        try:
            datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M")
        except ValueError:
            raise ValueError(f"End time ({end_time}) not in expected format ({EXPECTED_DATE_FORMAT})")
    if start_time:
        try:
            datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
        except ValueError:
            raise ValueError(f"Start time ({start_time}) not in expected format ({EXPECTED_DATE_FORMAT})")
            
    ##check that start-time is before end-time
    if end_time and start_time:
        end_time_=datetime.datetime.strptime(end_time, "%Y-%m-%dT%H:%M")
        start_time_=datetime.datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
        dt=start_time_ - end_time_
        if dt.total_seconds() <= 0:
            raise ValueError(f"Supplied Start time ({start_time}) <= End time ({end_time})")
    
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
#    print(start_time, end_time)
#    print(type(start_time), type(end_time))
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
    if isinstance(usernames, str):
        usernames = [usernames]
    if isinstance(partitions, str):
        partitions = [partitions]

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
#    exit()
    accounting_command_ = shlex.split(accounting_command)
    with open(LOGFILE, "w", newline="", encoding="utf-8") as stdout, open(
        ERRFILE, "w"
    ) as stderr:
        try:
            subprocess.run(
                accounting_command_, stdout=stdout, stderr=stderr, check=True
            )
        except subprocess.CalledProcessError as cpe:
            print(f"Could not run command ({accounting_command})\n Error:\t{cpe}")
            exitcode = 1

    return exitcode


def memory_to_gb(value: str, verbose: Optional[bool] = VERBOSE) -> float:
    """
    Handle whatever units --noconvert in the sacct command returns
    Expects K, M, G, or T (for kb, mb, gb, or tb)
    Returns mem in GB as a float
    """
    value = str(value).strip()
    unit = value[-1].upper()
    if unit == "K":
        return float(value[:-1]) / (GB_TO_MB**2)
    elif unit == "M":
        return float(value[:-1]) / GB_TO_MB
    elif unit == "G":
        return float(value[:-1])
    elif unit == "T":
        return float(value[:-1]) * GB_TO_MB
    else:
        #raise ValueError(f"Unrecognized memory format: {value}")

        ##8-19-26
        ##looks like some clusters report Mn (mb per node), Mc (mb per core)
        ##https://lists.schedmd.com/pipermail/slurm-users/2018-July/001655.html
        ##Since we aren't tracking memory -- at least in the first version --
        ##let's not bother introducing extra complexity dealing with that
        ##but also not raise an error; instead, just giving some placeholder value
        if verbose:
            warnings.warn(f"Unrecognized memory format: {value}, but never mind that")
        return np.nan


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

    on_bad_lines = "warn"  # such instances that multiple partitions are specified,
    # for example. The user can inspect the line for themselves.
    # Maybe I could fix less handwavingly later, but never you mind, Mrs Brown
    try:
        df = pd.read_csv(LOGFILE, delimiter=",", on_bad_lines=on_bad_lines)
    except FileNotFoundError:
        raise FileNotFoundError(f"{LOGFILE} not found. Do you have write permissions?")
    title = df.columns.to_list()
    if title != EXPECTED_FORMAT:
        raise ValueError(f"{title} is not in the expected format: {EXPECTED_FORMAT}")

    reqcpus, numnodes, reqmem_mb, timelimit, submit, start = [
        df[i].to_numpy() for i in EXPECTED_FORMAT
    ]

    if len(reqcpus) == 0:
        raise ValueError("No sacct records found for the specified filters.")

    # remove invalid records like start="Unknown"
    start_ = pd.to_datetime(
        start,
        errors="coerce",
        format="%Y-%m-%dT%H:%M:%S",
    )
    mask = ~pd.isna(start_)
    reqcpus, numnodes, reqmem_mb, timelimit, submit, start = (
        reqcpus[mask].astype(np.int32),
        numnodes[mask].astype(np.int32),
        reqmem_mb[mask],
        timelimit[mask].astype(str),
        submit[mask].astype(str),
        start[mask].astype(str),
    )
    # convert submit and start into queue wait time in hours
    submit = np.array([datetime.datetime.fromisoformat(i) for i in submit])
    start = np.array([datetime.datetime.fromisoformat(i) for i in start])
    queue_wait_time = start - submit
    queue_wait_hrs = np.array([i.total_seconds() / 3_600 for i in queue_wait_time])
    # convert timelimit into hours
    timelimit = np.where(
        np.char.count(timelimit, "-") == 1,
        np.char.replace(timelimit, "-", " days ", count=1),
        timelimit,
    )  # replace "15-" with "15 days", for example
    timelimit_hrs = pd.to_timedelta(timelimit).total_seconds() / 3_600

    #    reqmem_gb = np.array([int(i.removesuffix("M")) / GB_TO_MB for i in reqmem_mb])
    reqmem_gb = np.array([memory_to_gb(i, verbose=verbose) for i in reqmem_mb])

    return (reqcpus, numnodes, reqmem_gb, timelimit_hrs, queue_wait_hrs)


######################################## PLOTTING ########################################
def bins_sanity(
    bins: List[int],
    bin_type: str = Literal["cpus", "timelimit"]
) -> Tuple[bool, str]:
    """
    sanity checks for cpu and time bins
    """
    message = str()
    message_and_checks = {
        f"There must be at least 2 bins for requested {bin_type}": len(bins) < 2,
        f"There should be no negative values for {bin_type}": any(x <= 0 for x in bins),
        f"Values should be strictly ascending for {bin_type}": any(a >= b for a, b in zip(cpu_bins, cpu_bins[1:])),
    }
    for message, check in message_and_checks.items():
        if check:
            return not check, message



def define_labels(
    cpu_bins: List[int] = CPU_BINS,
    time_bins: List[int] = TIME_BINS,
) -> Tuple[List[str], List[int], List[str], List[int]]:
    """
    Given the bins for cpu requirement and time pending,
    define the x and y-axis labels
    """
    ##sanity checks
    sane_cpu_bins, cpu_message = bins_sanity(cpu_bins, "cpus")
    sane_time_bins, time_message = bins_sanity(time_bins, "timelimit")
    if sane_cpu_bins is False:
        raise ValueError(cpu_message)
    if sane_time_bins is False:
        raise ValueError(time_message)
    
    cpu_labels = [
        f"<{cpu_bins[0]}",
        *[f"{cpu_bins[i]}-{cpu_bins[i+1]-1}" for i in range(len(cpu_bins) - 1)],
        f"{cpu_bins[-1]}+",
    ]
    time_labels = [
        f"<{time_bins[0]}",
        *[f"{time_bins[i]}-{time_bins[i+1]-1}" for i in range(len(time_bins) - 1)],
        f"{time_bins[-1]}+",
    ]

    cpu_bin_edges = [-np.inf] + cpu_bins + [np.inf]
    time_bin_edges = [-np.inf] + time_bins + [np.inf]

    return (cpu_labels, cpu_bin_edges, time_labels, time_bin_edges)


def plot_wait_time(
    cpu_bin_edges: List[int],
    cpu_labels: List[str],
    time_bin_edges: List[int],
    time_labels: List[str],
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
    output_heatmap = splitext(output_heatmap)[0] + ".png"
    output_counts = splitext(output_counts)[0] + ".png"
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
        bins=cpu_bin_edges,
        labels=cpu_labels,
        include_lowest=True,
        right=False,
    )
    df["Timelimit_bin"] = pd.cut(
        df["Timelimit_hrs"],
        bins=time_bin_edges,
        labels=time_labels,
        include_lowest=True,
        right=False,  # exclude the upper limit, of course
    )
    lw, outside_lw = 0.2, 0.8
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
    axes.invert_yaxis()
    axes.set_xticks(np.arange(len(time_labels) + 1), minor=True)
    axes.set_yticks(np.arange(len(cpu_labels) + 1), minor=True)
    axes.grid(which="minor", color="black", linestyle="-", linewidth=lw)
    axes.tick_params(which="minor", bottom=False, left=False)
    for spine in axes.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
        spine.set_linewidth(outside_lw)
    axes.set_xlabel("Timelimit (hours)")
    axes.set_ylabel("Number of Cores Requested")
    axes.set_title("Average Queue Wait Time (hours)")
    try:
        plt.savefig(output_heatmap, dpi=DPI)
    except PermissionError:  # are we in some root directory, I wonder?
        print(f"could not save {output_heatmap}")
    plt.show(block=BLOCK) if show else plt.close(fig)

    fig, axes = plt.subplots(figsize=FIGSIZE)
    sns.heatmap(
        counts,
        annot=ANNOTATE_PLOT,
        fmt=".0f",  # "d",
        cmap=CMAP,
        linewidths=LW,
        cbar_kws={"label": "Number of Jobs"},
        ax=axes,
    )
    axes.set_xlabel("Timelimit (hours)")
    axes.set_ylabel("Number of Cores Requested")
    axes.set_title("Total Number of Jobs")
    axes.invert_yaxis()
    axes.set_xticks(np.arange(len(time_labels) + 1), minor=True)
    axes.set_yticks(np.arange(len(cpu_labels) + 1), minor=True)
    axes.grid(which="minor", color="black", linestyle="-", linewidth=lw)
    axes.tick_params(which="minor", bottom=False, left=False)

    for spine in axes.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
        spine.set_linewidth(outside_lw)
    try:
        plt.savefig(output_counts, dpi=DPI)
    except PermissionError:
        print(f"could not save {output_counts}")
    plt.show() if show else plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plots the average queue wait time for jobs. Queue wait time may be artificially high if job sbatch had --dependency or --begin."
    )

    parser.add_argument(
        "--start-time",
        "-s",
        type=str,
        default=START_TIME,
        help=f"Earliest possible job start time, format: YYYY-MM-DDTHH:MM. Optional. Default = {START_TIME}",
    )

    parser.add_argument(
        "--end-time",
        "-e",
        type=str,
        default=END_TIME,
        help=f"Latest possible job start time, format: YYYY-MM-DDTHH:MM. Optional. Default = {END_TIME}",
    )

    parser.add_argument(
        "--partitions",
        "-p",
        nargs="+",
        default=PARTITION,
        help=f"Partition(s) to include. Optional. Default = {PARTITION}",
    )

    parser.add_argument(
        "--usernames",
        "-u",
        nargs="+",
        default=USERNAME,
        help=f"Username(s) to include. Optional. Default = {USERNAME}",
    )

    parser.add_argument(
        "--cpu-bins",
        "-cb",
        nargs="+",
        type=int,
        default=CPU_BINS,
        help=f"Define bins for cpu counts. Optional. Provide as a space-separated list of at least 2 elements. Default = {CPU_BINS}",
    )
    parser.add_argument(
        "--time-bins",
        "-tb",
        nargs="+",
        type=int,
        default=TIME_BINS,
        help=f"Define bins for requested job time limits. Optional. Provide as a space-separated list of at least 2 elements. Default = {TIME_BINS}",
    )
    parser.add_argument(
        "--output-heatmap",
        "-oh",
        type=str,
        default=OUTPUT_HEATMAP,
        help=f"Output file for the heatmap of queue wait times. Optional. Default = {OUTPUT_HEATMAP}",
    )

    parser.add_argument(
        "--output-counts",
        "-oc",
        type=str,
        default=OUTPUT_COUNTS,
        help=f"Output file for the heatmap of counts for each entry in the queue wait times heatmap. Optional. Default = {OUTPUT_COUNTS}",
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

    (
        start_time,
        end_time,
        partitions,
        usernames,
        verbose,
        show,
        output_heatmap,
        output_counts,
        cpu_bins,
        time_bins,
    ) = (
        args.start_time,
        args.end_time,
        args.partitions,
        args.usernames,
        args.verbose,
        args.show,
        args.output_heatmap,
        args.output_counts,
        args.cpu_bins,
        args.time_bins,
    )
    if verbose:
        if not partitions:
            warnings.warn(
                "Partition(s) not specified. Will analyze jobs submitted to all partitions"
            )
        if not usernames:
            warnings.warn("Username(s) not specified. Will analyze jobs for all users")

    cpu_labels, cpu_bin_edges, time_labels, time_bin_edges = define_labels(
        cpu_bins=cpu_bins,
        time_bins=time_bins,
    )

    plot_wait_time(
        cpu_bin_edges=cpu_bin_edges,
        cpu_labels=cpu_labels,
        time_bin_edges=time_bin_edges,
        time_labels=time_labels,
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
