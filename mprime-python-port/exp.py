#!/usr/bin/python3

# Daniel Connelly
# based off of Tdulcet's expect script
# Python3 exp.py <User ID> <Computer name> <Type of work>

# NOTE(s)
'''
* pexpect has quirks about nonempty ()s (e.g., (y)), *s, inline ''s, or +s.
* this pexpect script cannot handle skipping past prompts like regular expect (something to fix, if possible).
'''

import sys
import time

# Installing dependency
try:
    import pexpect
except ImportError as error:
    print("Installing pexpect...")
    p = subprocess.run('pip install pexpect', shell=True)
    import pexpect

# Prerequisites, gained from mprime.py
USERID, COMPUTER, TYPE  = sys.argv[1], sys.argv[2], sys.argv[3]
# FIXME -- Teal, should we use this?
#if len(sys.argv) == 5:
#    TIME = sys.argv[4]

# Pexpect script
child = pexpect.spawn('./mprime -m') # starts shell to interact with
child.logfile = sys.stdout.buffer # enables output to screen (Python 3)

child.expect('Join Gimps?')
time.sleep(1)
child.sendline('y') # another acceptable version: child.send('y\r')
child.expect("Use PrimeNet to get work and report results ()") # () is a subpattern
time.sleep(1)
child.sendline("y")
child.expect("Your user ID or")
time.sleep(1)
child.sendline(USERID)
child.expect("Optional computer name:")
time.sleep(1)
child.sendline(COMPUTER)
child.expect("Computer uses a dial-up connection")
time.sleep(1)
child.sendline("N")
child.expect("Use a proxy server")
time.sleep(1)
child.sendline("N")
child.expect("Output debug info to prime.log")
time.sleep(1)
child.sendline("0")
child.expect("Accept the answers above?")
time.sleep(1)
child.sendline("Y")
child.expect("Hours per day this program will run")
time.sleep(1)
child.sendline("24")
child.expect("Daytime P-1/ECM stage 2")
time.sleep(1)
child.sendline("8")
child.expect("Nighttime P-1/ECM stage 2")
time.sleep(1)
child.sendline("8")
child.expect("Accept the answers above")
time.sleep(1)
child.sendline("Y")
child.expect("Number of workers to run")
time.sleep(1)
child.sendline("1")
child.expect("Priority ()")
time.sleep(1)
child.sendline("10")
child.expect("Type of work to get ()")
time.sleep(1)
child.sendline(TYPE)
child.expect("CPU cores to use ()") # Change for IBMs Watson machine
time.sleep(1)
child.sendline("56")
child.expect("Use hyperthreading for trial factoring ()")
time.sleep(1)
child.sendline("Y")
child.expect("Use hyperthreading for LL, P-1, ECM ()")
time.sleep(1)
child.sendline("N")
child.expect("Accept the answers above?")
time.sleep(1)
child.sendline("Y")
