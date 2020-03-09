# Daniel Connelly
# Usage: ./mprime.sh [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]

import sys
import subprocess
import os
import signal
#print(sys.argv[0])
#sys.exit()

os.environ["USERID"], os.environ["COMPUTER"], os.environ["TYPE"]  = sys.argv[1], sys.argv[2], sys.argv[3]

#---Checks and Dependencies/Downloads---#
print("Asserting Python version is >= Python3.6")
assert sys.version_info >= (3, 6) #Pyhon 3 required

print("Installing wget dependency")
try:
    import wget
except ImportError as error:
    p = subprocess.run('pip install wget', shell=True)
    import wget
#---------------------------------------#
#---Directory/unzipping---#
print("Making directory to house contents of prime95")
os.mkdir("prime95")

print("Changing to directory")
os.chdir("prime95")

os.environ["FILE"] = "p95v298b3.linux64.tar.gz"
print("Downloading prime95...")
wget.download('https://www.mersenne.org/ftp_root/gimps/'+os.environ["FILE"])

print("Unzipping folder here...")
subprocess.run(['tar', '-xzvf', os.environ["FILE"]])
#---------------------------------------#

#---Configuration---#
args = [os.environ["USERID"], os.environ["COMPUTER"], os.environ["TYPE"]]
print("Configuring...")
p = subprocess.Popen(['python3', "../exp.py"] + args,
  stdout=subprocess.PIPE,
  universal_newlines=True,
  bufsize=0)

#p.wait()

try:
  for line in p.stdout:
    line=line[:-1]
    print(line)
except KeyboardInterrupt:
  print("\nExiting...")
  os.kill(p, signal.SIGKILL)
  print("Done.")
#---------------------------------------#

#---Starting Program---#
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
