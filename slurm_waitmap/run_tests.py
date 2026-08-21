"""
Automatically test most functions
Might implement for the others later,
if I get the time and energy
"""
from pathlib import Path
import sys


def main() -> None:
    """
    Run every test, then exit with pytest’s status code.
    """
    try:
        import pytest
        from ascii_colors import ASCIIColors
    except ImportError:
        raise SystemExit(
            "Testing dependencies are not installed.\n"
            "Install them with:\n\tpip install 'slurm_waitmap[tests]'"
        )

    repo_root = Path(__file__).resolve().parent
    tests_dir = repo_root / "tests"
    exit_code = pytest.main(["-s", str(tests_dir)])
    text = "All tests passed!" if exit_code == 0 else "Some tests failed!"
    color = ASCIIColors.color_green if exit_code == 0 else ASCIIColors.color_red
    ASCIIColors.print(
        text.upper(),
        color=color,
        style=ASCIIColors.style_bold,
        background=ASCIIColors.color_black,
        end="\n\n",
        flush=True,
        file=sys.stdout,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

