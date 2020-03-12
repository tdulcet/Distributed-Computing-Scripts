#!/usr/bin/env python3

#Daniel Connelly
# Usage: ./mprime.py [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
# ./mprime.py [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
# ./mprime.py "$USER" "$HOSTNAME" 100 10
# ./mprime.py ANONYMOUS

import sys
import subprocess
import os
import re # regular expression matching
import hashlib # sha256
#import signal # debugging FIXME

def regex_check(reg, var, err):
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
    h  = hashlib.sha256()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda : f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()

# Main script

DIR = "mprime"
FILE = "p95v298b3.linux64.tar.gz"
SUM = "66117E8C30752426471C7B4A7A64FFBFC53C84D0F3140ACF87C08D3FEC8E99AC"
USERID, COMPUTER, TYPE  = sys.argv[1], sys.argv[2], sys.argv[3]
if len(sys.argv) == 5:
    TIME = sys.argv[4]
    regex_check(r'^([0-9]*[.])?[0-9]+$', TIME, "Usage: [Type of work] is not a valid number")

print("PrimeNet User ID:\t"+ USERID)
print("Computer name:\t\t"+ COMPUTER)
print("Type of work:\t\t"+ TYPE)
try: print("Idle time to run:\t"+ TIME + " minutes\n")
except: print("")

#---Dependencies/Downloads---#
print("Asserting Python version is >= Python3.6")
assert sys.version_info >= (3, 6)

try:
    import wget
except ImportError as error:
    print("Installing wget dependency")
    p = subprocess.run('pip install wget', shell=True)
    import wget
except Exception as error:
    misc_check(true, "Unexpected error occured when installing Python dependency:\n\n" + error)
#----------------------------#

#---Command Line Checks------#
misc_check(len(sys.argv) > 4, "Usage: " + sys.argv[0]+ " [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]")
regex_check(r'^([024568]|1(0[0124]|5[0124]|6[01])?)$', TYPE, "Usage: [Type of work] is not a valid number")
#----------------------------#

#---File/Folder checks-------#
misc_check(os.path.exists(DIR), "Error: Prime95 is already downloaded")
misc_check(sha256sum("./prime95/p95v298b3.linux64.tar.gz") == SUM, "Error: Prime95 is already downloaded")
#----------------------------#

#---Directory/unzipping---#
print("Making directory to house contents of Prime95")
os.mkdir(DIR)
misc_check(not os.path.exists(DIR), "Error: Failed to create directory: " + DIR)

print("Changing to directory")
os.chdir(DIR)

print("Downloading Prime95\n")
wget.download('https://www.mersenne.org/ftp_root/gimps/'+FILE)

print("Unzipping folder here...")
subprocess.run(['tar', '-xzvf', FILE])
#---------------------------------------#

#---Configuration---#
args = [USERID, COMPUTER, TYPE]
print("Setting up Prime95.")
p = subprocess.Popen(['python3', "../exp.py"] + args,
  stdout=subprocess.PIPE,
  universal_newlines=True,
  bufsize=0)

# This code block reads the output from the pexpect script p
for line in p.stdout:
    line=line[:-1]
    print(line)
#---------------------------------------#

#---Starting Program---#
print("Starting up Prime95.")
subprocess.Popen("./mprime -d") # daemon process
#subprocess.run("./mprime -d") # process # for Watson

#print("\nSetting it to start if the computer has not been used in the specified idle time and stop it whe    n someone uses the computer\n")
# FIXME  -- I need some explanation on what this is doing so I can port it, Teal
'''
#subprocess.run('crontab -l | { cat; echo "* * * * * if who -s | awk '{ print \$2 }' | (cd /dev && xargs -r stat -c '\%U \%X    ') | awk '{if ('\"\$(date +\%s)\"'-\$2<$TIME) { print \$1\"\t\"'\"\$(date +\%s)\"'-\$2; ++count }} END{if (    count>0) { exit 1 }}' > /dev/null; then pgrep mprime > /dev/null || (cd $DIR && nohup ./mprime &); else pgr    ep mprime > /dev/null && killall mprime; fi"; } | crontab -, shell=True)
'''

# TODO -- delete this comment block
''' # this reads the output for my testing purposes
print("Starting mprime")
p = subprocess.Popen(['./mprime', '-d'],
  stdout=subprocess.PIPE,
  universal_newlines=True,
  bufsize=0)

try:
  for line in p.stdout:
    line=line[:-1]
    print(line)
except KeyboardInterrupt:
  print("\nExiting...")
  os.kill(p, signal.SIGKILL)
  print("Done.")
'''

