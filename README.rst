==============
Slurm Waitmap
==============

`slurm-waitmap` uses Slurm accounting data from `sacct` to visualize how requested CPU count and job time limit affect queue wait times. It generates heatmaps of the average queue wait time and the number of jobs in each resource-request bin, helping users choose job parameters that may reduce time spent waiting in the queue.


Requirements
=============

* numpy>=1.26.4
* seaborn>=0.12.0
* pandas>=2.1
* matplotlib>=3.8.0


Installation
=============

First create and activate a new environment::

    mamba create --name env_name "python>=3.9,<3.14"
    mamba activate env_name

Then install::

    pip install slurm_waitmap
 

Usage
======

`slurm_waitmap` reads job-accounting data from Slurm using `sacct` and generates two heatmaps::

* average queue wait time as a function of requested CPU count and job time limit;
* number of jobs in each CPU-count and time-limit bin.

A basic run is::

```
slurm-waitmap
```

By default, the program analyzes jobs from the configured recent time window and writes two PNG files:

* `wait_times.png`
* `counts.png`

Example output::

Average queue wait time::

.. image:: https://example.com/images/queue_wait_times.png
   :width: 700
   :alt: Heatmap of average Slurm queue wait times

Number of jobs in each bin::

.. image:: https://example.com/images/queue_wait_counts.png
   :width: 700
   :alt: Heatmap showing the number of Slurm jobs in each bin

To configure the choices of time and cores binning, edit the conf.py file, but be careful!!!!

Options
--------

Restrict to a time range
^^^^^^^^^^^^^^^^^^^^^^^^^^

Start and end times must use the format `YYYY-MM-DDTHH:MM`::

```
slurm-waitmap \
    --start-time 2026-06-01T00:00 \
    --end-time 2026-07-01T00:00
```

Filter by partition
^^^^^^^^^^^^^^^^^^^^

Analyze one partition::

    slurm-waitmap --partitions gpu

Analyze multiple partitions::

    slurm-waitmap --partitions gpu shared

Filter by user
^^^^^^^^^^^^^^^^

Analyze jobs submitted by one user::

    slurm-waitmap --usernames username1

Analyze jobs submitted by multiple users::

    slurm-waitmap --usernames username1 username2

Choose output filenames
^^^^^^^^^^^^^^^^^^^^^^^^

Use `--output-heatmap` and `--output-counts` to choose the output filenames::

```
slurm-waitmap \
    --output-heatmap average_wait.png \
    --output-counts job_counts.png
```


Display the plots interactively
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``--show`` to display the plots in addition to saving them::

    slurm-waitmap --show

Verbose output
^^^^^^^^^^^^^^^^

Use ``--verbose`` to print additional information and warnings::

    slurm-waitmap --verbose

Complete example
^^^^^^^^^^^^^^^^^^
::

    slurm-waitmap \
        --start-time 2026-06-01T00:00 \
        --end-time 2026-07-01T00:00 \
        --partitions gpu shared \
        --usernames username1 username2 \
        --output-heatmap average_wait.png \
        --output-counts job_counts.png \
        --verbose

Command-line help
^^^^^^^^^^^^^^^^^^^

To see all available options::

    slurm-waitmap --help


Contact
========

Any suggestions or issues?

* Email me at giolajide@crimson.ua.edu
* Or raise an issue right here_



.. _here: https://github.com/giolajide/slurm_waitmap/issues
