import glob
import os
import numpy as np


def read_atmprof_header(path):
    head = []
    with open(path, "rt") as f:
        a = f.read()
        for line in str.splitlines(a):
            if str.startswith(line, "#"):
                head.append(line)
    return head


def gather_atmprof_headers(run_dir):
    atmprofs = {}
    for path in glob.glob(os.path.join(run_dir, "atmprof*.dat")):
        basename = os.path.basename(path)
        fname = os.path.splitext(basename)[0]
        atmprof_id_str = fname[len("atmprof") :]
        atmprof_id = int(atmprof_id_str)
        atmprofs[atmprof_id] = read_atmprof_header(path)
    return atmprofs


def print_atmprof_keys(run_dir):
    a = gather_atmprof_headers(run_dir)
    # only first line
    b = {}
    for key in a:
        b[key] = a[key][0]
    keys = np.sort(list(a.keys()))
    for key in keys:
        print(key, str.strip(b[key]))
    """
    1 # Atmospheric Model 1 (tropical)
    2 # Atmospheric Model 2 (midlatitude summer)
    3 # Atmospheric Model 3 (midlatitude winter)
    4 # Atmospheric Model 4 (subarctic summer)
    5 # Atmospheric Model 5 (subarctic winter)
    6 # Atmospheric Model 6 (U.S. Standard)
    7 # Atmospheric Model  7 (MAGIC summer)
    8 # Atmospheric Model  8 (MAGIC winter)
    9 # Atmospheric Model 9 (antarctic winter, south pole plus extension to sea level)
    10 # Atmospheric Model 10 (Windhoek, Namibia, all year average) as fitted to radiosonde data
    11 # Atmospheric Model 11 (Windhoek, Namibia, February) as fitted to radiosonde data
    12 # Atmospheric Model 12 (Windhoek, Namibia, June) as fitted to radiosonde data
    20 # Atmospheric Model 20 (South America at long=292, lat=-23) as loosely adapted to MSIS-E 90 model
    22 # This is a model profile derived for El Leoncito CTA site candidate, using the measured
    24 # This is a model profile derived for the Aar CTA site candidate, using the measured
    26 # This is a model profile derived for the Armazone CTA site candidate in Chile, using the measured
    28 # This is a model profile derived for the San Antonio de los Cobres (SAC) CTA site candidate, using the measured
    32 # This is a model profile derived for the San Antonio de los Cobres (SAC) CTA site candidate, using the measured
    34 # This is a model profile derived for the Yavapai Ranch CTA site candidate, using the measured
    36 # This is a model profile derived for the Tenerife CTA site candidate, using the measured
    """

    # Strip front
    """
    1  tropical)
    2  midlatitude summer)
    3  midlatitude winter)
    4  subarctic summer)
    5  subarctic winter)
    6  U.S. Standard)
    7  MAGIC summer)
    8  MAGIC winter)
    9  antarctic winter, south pole plus extension to sea level)
    10 Windhoek, Namibia, all year average) as fitted to radiosonde data
    11 Windhoek, Namibia, February) as fitted to radiosonde data
    12 Windhoek, Namibia, June) as fitted to radiosonde data
    20 South America at long=292, lat=-23) as loosely adapted to MSIS-E 90 model
    22 El Leoncito CTA site candidate, using the measured
    24 Aar CTA site candidate, using the measured
    26 Armazone CTA site candidate in Chile, using the measured
    28 San Antonio de los Cobres (SAC) CTA site candidate, using the measured
    32 San Antonio de los Cobres (SAC) CTA site candidate, using the measured
    34 Yavapai Ranch CTA site candidate, using the measured
    36 Tenerife CTA site candidate, using the measured
    """

    # Strip back
    """
    1  tropical
    2  midlatitude summer
    3  midlatitude winter
    4  subarctic summer
    5  subarctic winter
    6  U.S. Standard
    7  MAGIC summer
    8  MAGIC winter
    9  antarctic winter, south pole plus extension to sea level
    10 Windhoek, Namibia, all year average
    11 Windhoek, Namibia, February
    12 Windhoek, Namibia, June
    20 South America at long=292, lat=-23
    22 El Leoncito
    24 Aar
    26 Armazone, Chile
    28 San Antonio de los Cobres
    32 San Antonio de los Cobres
    34 Yavapai Ranch
    36 Tenerife
    """

    # add info manually
    """
    1  tropical
    2  midlatitude summer
    3  midlatitude winter
    4  subarctic summer
    5  subarctic winter
    6  U.S. Standard
    7  MAGIC summer
    8  MAGIC winter
    9  antarctic winter, south pole plus extension to sea level
    10 Windhoek, Namibia, all year average
    11 Windhoek, Namibia, February
    12 Windhoek, Namibia, June
    20 South America at long=292, lat=-23
    22 El Leoncito
    24 Aar, Indonesia
    26 Armazone, Chile
    28 San Antonio de los Cobres [BUG]
    32 San Antonio de los Cobres [BUG]
    34 Yavapai Ranch, U.S.
    36 Tenerife
    """


def atmprof(key):
    ATM = {}
    ATM["tropical"] = 1
    ATM["Windhoek, Namibia, all year average"] = 10
    ATM["Windhoek, Namibia, February"] = 11
    ATM["Windhoek, Namibia, June"] = 12

    return ATM[key]


def particles(key):
    pass
