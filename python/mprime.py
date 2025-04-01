#!/usr/bin/env python3

# Daniel Connelly and Teal Dulcet
# Usage: ./mprime.py [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
# ./mprime.py "$USER" "$HOSTNAME" 150 10
# ./mprime.py ANONYMOUS

# /// script
# requires-python = ">=3.5"
# dependencies = [
#   "requests",
# ]
# ///

import os
import platform
import re  # regular expression matching
import shlex
import stat
import subprocess
import sys
import tarfile
from hashlib import sha256

DIR = "mprime"
FILE = "p95v3019b20.linux64.tar.gz"
SUM = "4ce2377e03deb4cf189523136e26401ba08f67857a128e420dd030d00cdca601"


def misc_check(condition, err):
    if condition:
        print(err, file=sys.stderr)
        sys.exit(1)


# Source: https://stackoverflow.com/questions/22058048/hashing-a-file-in-python
# There is no sha256sum in the hashlib library normally
def sha256sum(filename):
    """Completes a checksum of the folder
    Parameters:
    filename (string): directory to be checked
    Returns:
    The hash sum string in hexidecimal digits.
    """
    h = sha256()
    buf = bytearray(h.block_size * 4096)
    view = memoryview(buf)
    with open(filename, "rb") as f:
        for size in iter(lambda: f.readinto(buf), 0):
            h.update(view[:size])
    return h.hexdigest()


# Main script
USERID = sys.argv[1] if len(sys.argv) > 1 else os.environ["USER"]
COMPUTER = sys.argv[2] if len(sys.argv) > 2 else platform.node()
TYPE = sys.argv[3] if len(sys.argv) > 3 else str(150)
TIME = (int(sys.argv[4]) if len(sys.argv) > 4 else 10) * 60


print(f"PrimeNet User ID:\t{USERID}")
print(f"Computer name:\t\t{COMPUTER}")
print(f"Type of work:\t\t{TYPE}")
print(f"Idle time to run:\t{TIME // 60} minutes\n")

# ---Dependencies/Downloads---#
try:
    import requests
except ImportError:
    print(
        f"""Please run the below command to install the Requests library:

	{os.path.basename(sys.executable) if sys.executable else "python3"} -m pip install requests

Then, run the script again."""
    )
    sys.exit(0)
# ----------------------------#
# ---Command Line Checks------#
misc_check(len(sys.argv) > 5, f"Usage: {sys.argv[0]} [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]")
misc_check(not re.match(r"^([024568]|1(0[0124]|5[0123]|6[01])?)$", TYPE), "Usage: [Type of work] is not a valid number")
misc_check(not re.match(r"^([0-9]*\.)?[0-9]+$", TIME), "Usage: [Idle time to run] must be a number")
# ----------------------------#

# ---Downloading/Directory Ops---#
misc_check(os.path.exists(DIR), "Error: MPrime is already downloaded")
print("Making directory to house contents of MPrime")
os.mkdir(DIR)
misc_check(not os.path.exists(DIR), f"Error: Failed to create directory: {DIR}")

os.chdir(DIR)
DIR = os.getcwd()

print("\nDownloading MPrime\n")
with requests.get(f"https://www.mersenne.org/download/software/v30/30.19/{FILE}", stream=True) as r:
    r.raise_for_status()
    # r.headers.get('Content-Disposition', '')
    with open(FILE, "wb") as f:
        os.posix_fallocate(f.fileno(), 0, int(r.headers["Content-Length"]))
        for chunk in r.iter_content(chunk_size=None):
            if chunk:
                f.write(chunk)
misc_check(
    sha256sum(FILE).lower() == SUM,
    f'Error: sha256sum does not match. Please run "rm -r {shlex.quote(DIR)}" make sure you are using the latest version of this script and try running it again\nIf you still get this error, please create an issue: https://github.com/tdulcet/Distributed-Computing-Scripts/issues',
)

print("\nDecompressing the files")
with tarfile.open(FILE) as tar:
    tar.list()
    tar.extractall()
# ---------------------------------------#

# ---Configuration---#

print("Setting up MPrime.")
subprocess.check_call([sys.executable, "../exp.py", USERID, COMPUTER, TYPE])
# ---------------------------------------#

# ---Starting Program---#
print("Starting up MPrime.")
subprocess.Popen(["./mprime"])  # daemon process

with open("mprime.sh", "w", encoding="utf-8") as f:
    f.write(rf"""#!/bin/bash

# Copyright © 2020 Teal Dulcet
# Start MPrime if the computer has not been used in the specified idle time and stop it when someone uses the computer
# {shlex.quote(DIR)}/mprime.sh

NOW=${{EPOCHSECONDS:-$(date +%s)}}

if who -s | awk '{{ print $2 }}' | (cd /dev && xargs -r stat -c '%U %X') | awk '{{if ('"$NOW"'-$2<{TIME}) {{ print $1"\t"'"$NOW"'-$2; ++count }}}} END{{if (count>0) {{ exit 1 }}}}' >/dev/null; then
	pgrep -x mprime >/dev/null || (cd {shlex.quote(DIR)} && exec nohup ./mprime -d >> 'mprime.out' &)
else
	pgrep -x mprime >/dev/null && killall mprime
fi
""")
st = os.stat("mprime.sh")
os.chmod("mprime.sh", st.st_mode | stat.S_IEXEC)

print(
    "\nRun this command for it to start if the computer has not been used in the specified idle time and stop it when someone uses the computer:\n"
)
print(f'crontab -l | {{ cat; echo "* * * * * {shlex.quote(DIR)}/mprime.sh"; }} | crontab -')
print('\nTo edit the crontab, run "crontab -e"')
# ----------------------#
