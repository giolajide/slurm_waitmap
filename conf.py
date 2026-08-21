##EDIT AS YOU PLEASE
CPU_BINS = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024] #make sure to be at least 3 elements
TIME_BINS = [0, 1, 4, 8, 12, 24, 48, 64, 100, 150] #make sure to be at least 3 elements
VERBOSE = False
DEFAULT_DAYS = 7
ERRFILE = "stats.err"
LOGFILE = "stats.csv"
SHOW=False
FIGSIZE = (11, 8)
ANNOTATE_PLOT = True
LW = 0.5
CMAP = "RdYlGn_r"  #similar to https://www.nersc.gov/users/status/queue-wait-times
BLOCK = False
DPI=150
OUTPUT_HEATMAP="wait_times.png"
OUTPUT_COUNTS="counts.png"


##do not edit unless you know what you're doing!
END_TIME = None #or some date in the format YYYY-MM-DDTHH:MM
START_TIME = None #or some date in the format YYYY-MM-DDTHH:MM
PARTITION = None
USERNAME = None
EXPECTED_DATE_FORMAT = "YYYY-MM-DDTHH:MM"


#__all__=[
#        "CPU_BINS",
#        "TIME_BINS",
#        "VERBOSE",
#        "DEFAULT_DAYS",
#        "END_TIME",
#        "START_TIME",
#        "PARTITION",
#        "USERNAME",
#        "ERRFILE",
#        "LOGFILE",
#        "SHOW",
#        "FIGSIZE",
#        "ANNOTATE_PLOT",
#        "LW",
#        "CMAP",
#        "BLOCK",
#        "DPI",
#        "OUTPUT_HEATMAP",
#        "OUTPUT_COUNTS",
#        "EXPECTED_DATE_FORMAT",
#        ]



