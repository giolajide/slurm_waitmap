import subprocess
from unittest.mock import patch
from slurm_waitmap.plotter import run_sacct
import pytest
import numpy as np
import memory_to_gb


def test_run_sacct_success(tmp_path):
    logfile = tmp_path / "stats.csv"
    errfile = tmp_path / "stats.err"

    with patch("slurm_waitmap.plotter.LOGFILE", str(logfile)), \
         patch("slurm_waitmap.plotter.ERRFILE", str(errfile)), \
         patch(
             "slurm_waitmap.plotter.decide_on_timings",
             return_value=("2026-08-01T12:00", "2026-08-02T12:00"),
         ), \
         patch("slurm_waitmap.plotter.subprocess.run") as mock_run:

        exitcode = run_sacct(
            usernames=["stories", "true"],
            partitions=["gpu", "cpu"],
        )

    assert exitcode == 0

    command = mock_run.call_args.args[0]

    assert "sacct" in command
    assert "--user" in command
    assert "stories,true" in command
    assert "--partition" in command
    assert "gpu,cpu" in command
    assert "--starttime=2026-08-01T12:00" in command
    assert "--endtime=2026-08-02T12:00" in command


def test_run_sacct_no_filters(tmp_path):
    logfile = tmp_path / "stats.csv"
    errfile = tmp_path / "stats.err"

    with patch("slurm_waitmap.plotter.LOGFILE", str(logfile)), \
         patch("slurm_waitmap.plotter.ERRFILE", str(errfile)), \
         patch(
             "slurm_waitmap.plotter.decide_on_timings",
             return_value=("2026-08-01T12:00", "2026-08-02T12:00"),
         ), \
         patch("slurm_waitmap.plotter.subprocess.run") as mock_run:

        exitcode = run_sacct(
            usernames=None,
            partitions=None,
        )

    assert exitcode == 0

    command = mock_run.call_args.args[0]

    assert "--allusers" in command
    assert "--user" not in command
    assert "--partition" not in command


def test_run_sacct_failure(tmp_path):
    logfile = tmp_path / "stats.csv"
    errfile = tmp_path / "stats.err"

    with patch("slurm_waitmap.plotter.LOGFILE", str(logfile)), \
         patch("slurm_waitmap.plotter.ERRFILE", str(errfile)), \
         patch(
             "slurm_waitmap.plotter.decide_on_timings",
             return_value=("2026-08-01T12:00", "2026-08-02T12:00"),
         ), \
         patch(
             "slurm_waitmap.plotter.subprocess.run",
             side_effect=subprocess.CalledProcessError(
                 returncode=1,
                 cmd="sacct",
             ),
         ):

        exitcode = run_sacct(
            usernames=["giolajide"],
            partitions=["gpu"],
        )

    assert exitcode == 1


def test_memory_to_gb():
    ##invalid unit
    with pytest.warns(UserWarning):
        memory_to_gb("753U")
    ##valid unit in TB
    number=746
    result = memory_to_gb(f"{number}T")
    assert result == pytest.approx(number * 1024, abs=1e-5)
    ##valid unit in MB
    result = memory_to_gb(f"{number}M")
    assert result == pytest.approx(number / 1024, abs=1e-4)
    ##unsupported memory units
    assert np.isnan(memory_to_gb("753Mc"))
    assert np.isnan(memory_to_gb("753Mn"))
