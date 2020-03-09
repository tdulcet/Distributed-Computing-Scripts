#!/usr/bin/python3

# Daniel Connelly
 # based off of Tdulcet's expect script
# Python3 exp.py <User ID> <Computer name> <Type of work>

# NOTE/TODO -- Basically everything works, but some pexpects don't work "as expected".
#              Also, pexpects cannot handle '*'s.
import sys
import time
import os

# Dependencies
try:
    import pexpect
except ImportError as error:
    p = subprocess.run('pip install pexpect', shell=True)
    import pexpect

# Prerequisites
time.sleep(1)
os.environ["USERID"], os.environ["COMPUTER"], os.environ["TYPE"]  = sys.argv[1], sys.argv[2], sys.argv[3]

# Pexpect script
child = pexpect.spawn('./mprime -m')
child.expect('Join Gimps?')
#child.expect('Join Gimps? (*):')
time.sleep(1)
child.sendline('\r')
#child.expect("Use PrimeNet to get work and report results (*):")
print(child.before)
#child.expect("Use PrimeNet to get work and report results (Y):")
#print(child.before)
time.sleep(1)
child.sendline("r")
#child.expect("Your user ID or \"ANONYMOUS\" :")
child.expect("Your user ID or")
time.sleep(1)
child.sendline("-- "+os.environ["USERID"]+"\r")
child.expect("Optional computer name:")
time.sleep(1)
child.sendline("-- "+os.environ["COMPUTER"]+"\r")
#child.expect("Type of work to get") ## --- this marks where I broke the original expect {}
time.sleep(1)
child.sendline("-- "+os.environ["TYPE"]+"\r")
#child.expect("Your choice:\nUse the following values to select a work type:\n*: 1\n (*):")
child.expect("Your choice:")
time.sleep(1)
child.sendline("\r")
#child.expect("Done communicating with server.")
child.sendline("\x03")
time.sleep(10)
#child.expect("Choose Test/Continue to restart.")
time.sleep(1)
child.sendline("5\r")
child.expect(pexpect.EOF, timeout=None) # copied from: https://stackoverflow.com/questions/11160504/simplest-way-to-run-an-expect-script-from-python
cmd_show_data = child.before
#cmd_output = cmd_show_data.split('\r\n')
#for data in cmd_output:
#    print(data)
