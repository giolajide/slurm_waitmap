import pytest
from slurm_waitmap.plotter import define_labels
from math import inf

def test_define_labels():
    ##invalid length of cpu and-or time bins
    with pytest.raises(ValueError):
        define_labels([1], [1, 2])
    with pytest.raises(ValueError):
        define_labels([1, 4], [1])
    with pytest.raises(ValueError):
        define_labels([1], [1])
    #valid cpu and time bins
    cpu_labels, cpu_bin_edges, time_labels, time_bin_edges = define_labels(
            [1, 2, 7, 14, 21, 28],
            [1, 2, 24, 48],
            )
    assert cpu_labels == ["<1", "1-1", "2-6", "7-13", "14-20", "21-27", "28+"]
    assert cpu_bin_edges  == [-inf, 1, 2, 7, 14, 21, 28, inf]
    assert time_labels  == ["<1", "1-1", "2-23", "24-47", "48+"]
    assert time_bin_edges  == [-inf, 1, 2, 24, 48, inf]
    ##no need to test invalid types, as these are already
    ##screened out by the main() function, by setting type=int in argparse

