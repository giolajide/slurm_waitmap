==============
Slurm Waitmap
==============

``slurm-waitmap`` uses Slurm accounting data from ``sacct`` to visualize how requested CPU count and job time limit affect queue wait times. It generates heatmaps of the average queue wait time and the number of jobs in each resource-request bin, helping users choose job parameters that may reduce time spent waiting in the queue.


Requirements
=============

* Slurm accounting enabled and the ``sacct`` command available.
* numpy>=1.26.4
* seaborn>=0.12.0
* pandas>=2.1
* matplotlib>=3.8.0


Installation
=============

Run the following command to install::

    pip install slurm_waitmap
 

Usage
======

A basic run is::

    slurm-waitmap



Example output::

Average queue wait time:

.. figure:: https://raw.githubusercontent.com/giolajide/slurm_waitmap/main/docs/wait_times.png
   :scale: 140
   :alt: Heatmap of average Slurm queue wait times
   :align: center


Number of jobs in each bin:

.. figure:: https://raw.githubusercontent.com/giolajide/slurm_waitmap/main/docs/counts.png
   :scale: 140
   :align: center
   :alt: Heatmap showing the number of Slurm jobs in each bin


Options
--------

Restrict to a time range
^^^^^^^^^^^^^^^^^^^^^^^^^^

Start and end times must use the format **YYYY-MM-DDTHH:MM** ::

    slurm-waitmap --start-time 2026-06-01T00:00 --end-time 2026-07-01T00:00

Note:

* If *--start-time* is given but *--end-time* is omitted, it sets *--end-time* to the current moment
* If *--end-time* is given but *--start-time* is omitted, it sets *--start-time* to 14 days before *--end-time*
* If neither *--start-time* nor *--end-time* is specified, then it defaults to the last 14 days


Filter by partition
^^^^^^^^^^^^^^^^^^^^

Analyze one partition::

    slurm-waitmap --partitions gpu

Analyze multiple partitions::

    slurm-waitmap --partitions gpu shared

If *--partitions* is not specified, then it defaults to all partitions

Filter by user
^^^^^^^^^^^^^^^^

Analyze jobs submitted by one user::

    slurm-waitmap --usernames dora

Analyze jobs submitted by multiple users::

    slurm-waitmap --usernames dora spenlow

If *--usernames* is not specified, then it defaults to all users

Choose output filenames
^^^^^^^^^^^^^^^^^^^^^^^^

Use `--output-heatmap` and `--output-counts` to specify the output filenames::

    slurm-waitmap --output-heatmap average_wait.png --output-counts job_counts.png


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
        --usernames abel magwitch \
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
