#!/usr/bin/env python3

# Daniel Connelly
# based off of Tdulcet's 'mprime.exp'
# Python3 exp.py <User ID> <Computer name> <Type of work> <idle time to run>

# Note: * pexpect has quirks about nonempty ()s (e.g., (y)), *s, inline ''s, or +s.

import sys
from time import sleep
import subprocess

# Potentially installing dependency
try:
    import pexpect
except ImportError as error:
    print("Installing pexpect...")
    p = subprocess.run('pip install pexpect', shell=True)
    import pexpect

# Prerequisites, gained from mprime.py
USERID, COMPUTER, TYPE  = sys.argv[1], sys.argv[2], sys.argv[3]
PROOF_CERTIFICATION_WORK = "n"

child = pexpect.spawn('./mprime -m') # starts shell to interact with
child.logfile = sys.stdout.buffer # enables output to screen (Python 3)
expects = ["Join Gimps?", "Use PrimeNet to get work and report results ()", "Your user ID or", 
           "Optional computer name", "Type of work to get", "CPU cores to use", 
           "Your choice:", pexpect.TIMEOUT, "Done communicating with server.",
           "Choose Test/Continue to restart","Upload bandwidth limit in Mbps", "Skip advanced resource settings",
           "stage 2 memory in GB", "Max emergency memory in GB/worker", "Get occasional proof certification work"]
responses = ["y", "y", USERID, 
             COMPUTER, TYPE, "", 
             "5", "", "\x03", 
             "5", "10000", "n", 
             "12", "3", "n"]

while 1:
    try:
        sleep(1)
        index = child.expect(expects, timeout = 3)
        child.sendline(responses[index])
    except pexpect.exceptions.EOF:
        break
