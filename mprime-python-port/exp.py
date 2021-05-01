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
    p = subprocess.run('pip3 install pexpect', shell=True)
    import pexpect

# Prerequisites, gained from mprime.py
USERID, COMPUTER, TYPE  = sys.argv[1], sys.argv[2], sys.argv[3]

child = pexpect.spawn('./mprime -m') # starts shell to interact with
child.logfile = sys.stdout.buffer # enables output to screen (Python 3)
preThreadExpects = (("Join Gimps?", "y"), ("Use PrimeNet to get work and report results ()", "y"),
        ("Your user ID or", USERID), ("Optional computer name", COMPUTER))
        #("Type of work to get", TYPE), ("Your choice:", "5"))
postThreadExpects =  (("Get occasional proof certification work", ""),
                      ("Accept the answers above?", ""))
getThreads = False
finish = False
while 1:
    try:
        if getThreads == False and finish == False:
            # handle introductory cases
            for expect in preThreadExpects:
                child.expect(expect[0], timeout=2)
                child.sendline(expect[1])
            while 1:
                # case to handle multiple threads without needing to hardcode it
                try: 
                    child.expect("Type of work to get", timeout=2)
                    child.sendline(TYPE)
                    child.expect("CPU cores to use", timeout=2)
                    getThreads = True
                    break
                except Exception as e:
                    # will handle all default cases
                    child.sendline("")
        elif getThreads and finish == False:
            while True:
                try:
                    child.expect("Type of work to get", timeout=2)
                    child.sendline(TYPE)
                    child.expect("CPU cores to use", timeout=2)
                    child.sendline("")
                except Exception as e:
                    finish = True
                    break
        else:
            for expect in postThreadExpects:
                child.expect(expect[0], timeout=2)
                child.sendline(expect[1])
            child.expect("Your choice:")
            child.sendline("5")
            child.expect("Choose Test/Continue to restart")
            child.sendline("5")
            child.expect(pexpect.EOF)
            break
    except pexpect.TIMEOUT:
        child.sendline("")
