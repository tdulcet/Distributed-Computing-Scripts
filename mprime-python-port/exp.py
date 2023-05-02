#!/usr/bin/env python3

# Daniel Connelly
# based off of Tdulcet's 'mprime.exp'
# Python3 exp.py <User ID> <Computer name> <Type of work> <idle time to run>

# Note: * pexpect has quirks about nonempty ()s (e.g., (y)), *s, inline ''s, or +s.

import subprocess
import sys
from time import sleep

# Potentially installing dependency
try:
    import pexpect
except ImportError:
    print("Installing pexpect...")
    p = subprocess.run([sys.executable, "-m", "pip", "install", "pexpect"])
    import pexpect

# Prerequisites, gained from mprime.py
USERID, COMPUTER, TYPE = sys.argv[1], sys.argv[2], sys.argv[3]

child = pexpect.spawn("./mprime -m")  # starts shell to interact with
child.logfile = sys.stdout.buffer  # enables output to screen (Python 3)

expectDict = {"Join Gimps?": "y",
              "Use PrimeNet to get work and report results": "y",
              "Your user ID or": USERID,
              "Optional computer name": COMPUTER,
              "Type of work to get": TYPE,
              "Upload bandwidth limit in Mbps": "10000",
              "Skip advanced resource settings": "n",
              "Optional directory to hold": "",
              "Your choice:": 5,
              pexpect.TIMEOUT: "",
              # "Use the following values to select a work type:": "",
              "Done communicating with server.": "\x03",
              "Choose Test/Continue to restart.": "5"}

expects = list(expectDict.keys())
responses = list(expectDict.values())

while True:
    try:
        sleep(2)
        index = child.expect(expects, timeout=2)
        child.sendline(str(responses[index]))
    except pexpect.exceptions.EOF:
        break
