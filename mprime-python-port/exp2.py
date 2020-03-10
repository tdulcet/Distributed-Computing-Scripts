import sys
import time
import os
from pexpect import *

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

(output, exit_code) = run('./mprime -m')
print(output, exit_code)
(output, exit_code) = run('y', events={'Join Gimps?'})
print(output, exit_code)


#child.logfile = sys.stdout.buffer # zartaz's comment: https://github.com/pexpect/pexpect/issues/518

child.expect('Join Gimps?')
time.sleep(1)
child.sendline('y\r')


