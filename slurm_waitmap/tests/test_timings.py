import pytest
from slurm_waitmap.plotter import decide_on_timings


def test_decide_on_timings():
    ##test invalid time formats
    #only one bad date
    with pytest.raises(ValueError):
        decide_on_timings("2026-05-10T12:00", "2026-05-12T16:00:10", True)
    #both dates bad
    with pytest.raises(ValueError):
        decide_on_timings("2026-05-12T", "2026-05-12T16:00:10", True)
    ##omit date(s)
    with pytest.warns(UserWarning):
        decide_on_timings("2026-05-12T08:21", None, True)
    with pytest.warns(UserWarning):
        decide_on_timings(None, "2026-05-12T08:21", True)
    with pytest.warns(UserWarning):
        decide_on_timings(None, None, True)
    ##test valid values
    start_time, end_time = decide_on_timings("2024-08-06T12:12", "2025-08-06T12:12", False)
    expected = ["2024-08-06T12:12", "2025-08-06T12:12"]
    assert expected[0] == start_time
    assert expected[1] == end_time

