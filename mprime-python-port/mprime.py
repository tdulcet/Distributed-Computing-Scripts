#!/usr/bin/env python3

# Daniel Connelly
# Usage: ./mprime.py [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
# ./mprime.py "$USER" "$HOSTNAME" 150 10
# ./mprime.py ANONYMOUS

import sys
import subprocess
import os
import socket
import re  # regular expression matching
import hashlib  # sha256
import time

DIR = "mprime"
FILE = "p95v307b9.linux64.tar.gz"
SUM = "d47d766c734d1cca4521cf7b37c1fe351c2cf1fbe5b7c70c457061a897a5a380"


def regex_check(reg, var, err):
    '''Checks cmdline args for proper bounds using regex
    Parameters:
    reg (string): regex string to check against
    var (string): variable to check against regex string
    err (string): output to put to STDERR if regex does not match
    Returns:
    None
    '''
    if not re.match(reg, var):
        sys.stderr.write(err)
        sys.exit(1)


def misc_check(condition, err):
    if condition:
        sys.stderr.write(err)
        sys.exit(1)

# Source: https://stackoverflow.com/questions/22058048/hashing-a-file-in-python
# There is no sha256sum in the hashlib library normally
def sha256sum(filename):
    '''Completes a checksum of the folder
    Parameters:
    filename (string): directory to be checked
    Returns:
    The hash sum string in hexidecimal digits
    '''
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda: f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()


# Main script
USERID = sys.argv[1] if len(sys.argv) > 1 else os.environ["USER"]
COMPUTER = sys.argv[2] if len(sys.argv) > 2 else socket.gethostname()
TYPE = sys.argv[3] if len(sys.argv) > 3 else str(150)
TIME = str(int(sys.argv[4]) * 60) if len(sys.argv) > 4 else str(10 * 60)


print("PrimeNet User ID:\t" + USERID)
print("Computer name:\t\t" + COMPUTER)
print("Type of work:\t\t" + TYPE)
print("Idle time to run:\t" + str(int(TIME) // 60) + " minutes\n")

#---Dependencies/Downloads---#
print("Asserting Python version is >= Python3.6")
assert sys.version_info >= (3, 0)

try:
    import wget
except ImportError as error:
    print("Installing wget dependency")
    p = subprocess.run('pip install wget', shell=True)
    import wget
except Exception as error:
    misc_check(True, "Unexpected error occurred when installing Python dependency:\n\n" + str(error) + "\n")
#----------------------------#
#---Command Line Checks------#
misc_check(len(sys.argv) > 5, "Usage: " + sys.argv[0] + " [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]")
regex_check(r'^([024568]|1(0[0124]|5[0123]|6[01])?)$', TYPE, "Usage: [Type of work] is not a valid number")
regex_check(r'^([0-9]*[.])?[0-9]+$', TIME, err="Usage: [Idle time to run] must be a number")
#----------------------------#

#---Downloading/Directory Ops---#
misc_check(os.path.exists(DIR), "Error: Prime95 is already downloaded")
print("Making directory to house contents of Prime95")
os.mkdir(DIR)
misc_check(not os.path.exists(DIR), "Error: Failed to create directory: " + DIR)

os.chdir(DIR)
os.environ["DIR"] = os.getcwd()

print("\nDownloading Prime95\n")
wget.download('https://www.mersenne.org/ftp_root/gimps/' + FILE)
misc_check(sha256sum(FILE).lower() == SUM, "Error: sha256sum does not match. Please run \"rm -r " + DIR + "\" make sure you are using the latest version of this script and try running it again\nIf you still get this error, please create an issue: https://github.com/tdulcet/Distributed-Computing-Scripts/issues")

print("\nDecompressing the files")
subprocess.run(['tar', '-xzvf', FILE])
#---------------------------------------#

#---Configuration---#
args = [USERID, COMPUTER, TYPE]

print("Setting up Prime95.")
p = subprocess.Popen([sys.executable, "../exp.py"] + args,
                     stdout=subprocess.PIPE,
                     universal_newlines=True,
                     bufsize=0)

# This code block reads the output from the pexpect script p
for line in p.stdout:
    line = line[:-1]
    print(line)
#---------------------------------------#

#---Starting Program---#
print("Starting up Prime95.")
subprocess.Popen("./mprime")  # daemon process

print("\nSetting it to start if the computer has not been used in the specified idle time and stop it when someone uses the computer\n")

os.environ["TIME"] = TIME
subprocess.Popen("crontab -l | { cat; echo \"* * * * * if who -s | awk \'{ print \\$2 }\' | (cd /dev && xargs -r stat -c \'\\%U \\%X\') | awk \'{if (\'\\\"\\${EPOCHSECONDS:-\\$(date +\\%s)}\\\"\'-\\$2<$TIME) { print \\$1\\\"\\t\\\"\'\\\"\\${EPOCHSECONDS:-\\$(date +\\%s)}\\\"\'-\\$2; ++count }} END{if (count>0) { exit 1 }}\' >/dev/null; then pgrep -x mprime >/dev/null || (cd \'$DIR\' && nohup ./mprime &); else pgrep -x mprime >/dev/null && killall mprime; fi\"; } | crontab -", shell=True)
#----------------------#
