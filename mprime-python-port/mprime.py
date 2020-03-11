#!/usr/bin/env python3

#Daniel Connelly
# Usage: ./mprime.py [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
# wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mprime.sh -qO - | bash -s --
# ./mprime.py [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
# ./mprime.py "$USER" "$HOSTNAME" 100 10
# ./mprime.py ANONYMOUS

import sys
import subprocess
from os import environ, path, chdir
import signal
import re # regular expression matching
from hashlib import sha256 # verifying we downloaded the correct mprime tar.gz
import hashlib

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

environ["DIR"] = "prime95" # TODO -- change to fit Teal's mprime filename
environ["FILE"] = "p95v298b3.linux64.tar.gz"
environ["SUM"] = "66117E8C30752426471C7B4A7A64FFBFC53C84D0F3140ACF87C08D3FEC8E99AC"
if len(sys.argv) == 5:
    environ["TIME"] = sys.argv[4]
    regex_check(r'^([0-9]*[.])?[0-9]+$', environ["TIME"], "Usage: [Type of work] is not a valid number")
environ["USERID"], environ["COMPUTER"], environ["TYPE"]  = sys.argv[1], sys.argv[2], sys.argv[3]

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
regex_check(r'^([024568]|1(0[0124]|5[0124]|6[01])?)$', environ["TYPE"], "Usage: [Type of work] is not a valid number")
#----------------------------#

#---File/Folder checks-------#
#misc_check(path.exists(environ["DIR"]), "Error: Prime95 is already downloaded")
misc_check(sha256sum("./prime95/p95v298b3.linux64.tar.gz") == environ["SUM"], "Error: Prime95 is already downloaded")
#----------------------------#

#---Directory/unzipping---#
#print("Making directory to house contents of prime95")
#os.mkdir("prime95")
#misc_check(not os.path.exists(DIR), "Error: Failed to create directory " + environ["DIR"])

print("Changing to directory")
chdir("prime95")

#print("Downloading prime95...")
#wget.download('https://www.mersenne.org/ftp_root/gimps/'+environ["FILE"])

print("Unzipping folder here...")
subprocess.run(['tar', '-xzvf', environ["FILE"]])
#---------------------------------------#

#---Configuration---#
args = [environ["USERID"], environ["COMPUTER"], environ["TYPE"]]
print("Setting up Prime95.")
p = subprocess.Popen(['python3', "../exp.py"] + args,
  stdout=subprocess.PIPE,
  universal_newlines=True,
  bufsize=0)

# This code block reads the output from the pexpect script
try:
  for line in p.stdout:
    line=line[:-1]
    print(line)
#---------------------------------------#

#---Starting Program---#
print("Starting up Prime95.")
subprocess.Popen("./mprime") # daemon process
print ("Mprime is running in the background...")
#subprocess.run('crontab -l | { cat; echo "* * * * * if who -s | awk '{ print \$2 }' | (cd /dev && xargs -r stat -c '\%U \%X    ') | awk '{if ('\"\$(date +\%s)\"'-\$2<$TIME) { print \$1\"\t\"'\"\$(date +\%s)\"'-\$2; ++count }} END{if (    count>0) { exit 1 }}' > /dev/null; then pgrep mprime > /dev/null || (cd $DIR && nohup ./mprime &); else pgr    ep mprime > /dev/null && killall mprime; fi"; } | crontab -, shell=True)

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

'''
#TODO -- I need some explanation on what this is doing, Teal
#subprocess.run('crontab -l | { cat; echo "* * * * * if who -s | awk '{ print \$2 }' | (cd /dev && xargs -r stat -c '\%U \%X    ') | awk '{if ('\"\$(date +\%s)\"'-\$2<$TIME) { print \$1\"\t\"'\"\$(date +\%s)\"'-\$2; ++count }} END{if (    count>0) { exit 1 }}' > /dev/null; then pgrep mprime > /dev/null || (cd $DIR && nohup ./mprime &); else pgr    ep mprime > /dev/null && killall mprime; fi"; } | crontab -, shell=True)
'''
