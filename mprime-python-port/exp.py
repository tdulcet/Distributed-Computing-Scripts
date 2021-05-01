#!/usr/bin/env python3

# Daniel Connelly
# based off of Tdulcet's 'mprime.exp'
# Python3 exp.py <User ID> <Computer name> <Type of work>

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

child = pexpect.spawn('./mprime -m') # starts shell to interact with
child.logfile = sys.stdout.buffer # enables output to screen (Python 3)
expects = (("Join Gimps?", "y"), ("Use PrimeNet to get work and report results ()", "y"),
        ("Your user ID or", USERID), ("Optional computer name", COMPUTER),
        ("Type of work to get", TYPE), ("Your choice:", "5"))
index = 0
while 1:
    try:
        if index != len(expects):
            child.expect(expects[index][0], timeout=1)
            sleep(1)
            child.sendline(expects[index][1])
            index += 1
        else:
            child.expect("Done communicating with server.")
            child.sendline("\x03")
            sleep(5)
            child.expect("Choose Test/Continue to restart.")
            sleep(1)
            child.sendline("5")
            child.expect(pexpect.EOF)
            break
    except pexpect.TIMEOUT:
        try: 
            child.expect("Type of work to get", timeout=1)
            sleep(1)
            child.sendline(TYPE)
            child.expect("CPU cores to use", timeout=5)
            sleep(1)
            child.sendline("")
            break
        except Exception as e:
            # will handle all default cases
            child.sendline("")
        #child.sendline("")
