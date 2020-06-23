import requests
import hashlib
import random
import subprocess
import re
import sys
import os
import platform
import json
import time
from urllib.parse import urlencode # TODO -- delete
from optparse import OptionParser
from datetime import datetime as date

# Modified code from https://stackoverflow.com/a/13078519/8651748
def get_cpu_signature():
    output = ""
    if platform.system() == "Windows":
        output = subprocess.check_output('wmic cpu list brief').decode()
    elif platform.system() == "Darwin":
        os.environ['PATH'] = os.environ['PATH'] + os.pathsep + '/usr/sbin'
        command ="sysctl -n machdep.cpu.brand_string"
        output = subprocess.check_output(command).decode().strip()
    elif platform.system() == "Linux":
        command = "cat /proc/cpuinfo"
        all_info = subprocess.check_output(command, shell=True).strip().decode()
        for line in all_info.split("\n"):
            if "model name" in line:
                output = re.sub(".*model name.*:", "", line,1).lstrip()
                break
    return output

def get_cpu_name(signature):
    search = re.search(r'\bPHENOM\b|\bAMD\b|\bATOM\b|\bCore 2\b|\bCore(TM)2\b|\bCORE(TM) i7\b|\bPentium(R) M\b|\bCore\b|\bIntel\b|\bUnknown\b|\bK5\b|\bK6\b', signature)
    return search.group(0) if search else ""

def get_cpu_MHz(signature):
    search = re.search(r'\d+\.\d+', signature)
    return int(float(search.group(0))*1000) if search else ""

error_codes = {'0': 'No error',
        '3': 'Server busy',
        '4': 'Invalid version',
        '5': 'Invalid transaction',
	'7': 'Invalid parameter',
        '9': 'Access denied',
	'11': 'Server database malfunction',
        '13': "Server database full or broken",
        '21': "Invalid user",
        '30': "CPU not registered",
	'31': "Obsolete client, please upgrade",
	'32': "Stale cpu info",
	'33': "CPU identity mismatch",
	'34': "CPU configuration mismatch",
	'40': "No assignment",
	'43': "Invalid assignment key",
	'44': "Invalid assignment type",
	'45': "Invalid result type",
	'46': "Invalid work type",
	'47': "Work no longer needed", # TODO -- don't shut down based on this alone
}


cpu_signature = get_cpu_signature()
#cpu_speed = get_cpu_speed(cpu_signature)
cpu_speed = "100.0" # default. May use the average speed of last 3 calculations to update speed later (see CPU_SPEED variable in gwnum/cpuid.c file)
cpu_brand = get_cpu_name(cpu_signature)

#################### GLOBAL VARIABLES/OPTIONS ####################
# Basic file
#primenet_v5_url = "http://v5.mersenne.org/v5server/?px=GIMPS&"
primenet_v5_url = "http://v5.mersenne.org/v5server/?"

# Options. Credit goes to original primenet.py and Teal Dulcet for the `-i` option.
parser = OptionParser()
parser.add_option("-d", "--debug", action="store_true",
                  dest="debug", default=False, help="Display debugging info")
parser.add_option("-u", "--username", dest="username",
                  help="Primenet user name")
parser.add_option("-c", "--computername", dest="computer_name",
                  help="Computer name")
parser.add_option("-w", "--workdir", dest="workdir", default=".",
                  help="Working directory with worktodo.ini and results.txt, default current")
parser.add_option("-i", "--workfile", dest="workfile",
                  default="worktodo.ini", help="WorkFile filename, default %default")

# -t is reserved for timeout, instead use -T for assignment-type preference:
parser.add_option("-T", "--worktype", dest="worktype", default="101", help="Worktype code, default %defaults for double-check LL, alternatively 100 (smallest available first-time LL), 102 (world-record-sized first-time LL), 104 (100M digit number to LL test - not recommended), 150 (smallest available first-time PRP), 151 (double-check PRP), 152 (world-record-sized first-time PRP), 153 (100M digit number to PRP test - not recommended)")

parser.add_option("-n", "--num_cache", dest="num_cache",
                  default="2", help="Number of assignments to cache, default 2")

parser.add_option("-t", "--timeout", dest="timeout", default="21600",
                  help="Seconds to wait between network updates, default 21600 [6 hours]. Use 0 for a single update without looping.")

(options, args) = parser.parse_args()

progname = os.path.basename(sys.argv[0])
workdir = os.path.expanduser(options.workdir)
timeout = int(options.timeout)

localfile = os.path.join(workdir, "local.ini")
workfile = os.path.join(workdir, options.workfile)
resultsfile = os.path.join(workdir, "results.txt")

# A cumulative backup
sentfile = os.path.join(workdir, "results_sent.txt")

version = "v29.8" # TODO -- don't hardcode
build = "build 6" # TODO -- don't hardcode
program = "Prime95" # TODO -- don't hardcode

if not os.path.exists("prime.log"):
    with open("prime.log", "w") as f1:
        g = hashlib.md5(str.encode(cpu_brand + cpu_signature + str(date.now()))).hexdigest() # program's self-assigned permanent ID (guid)
        hg = hashlib.md5(str.encode(cpu_brand + cpu_signature)).hexdigest() # machine's hardware hash ID (guid)
        f1.write(f'g={g}\nhg={hg}')
else:
    with open("prime.log", "r") as f1:
        for line in f1:
            if 'g=' in line:
                g = re.search(r'(?<=g=).+',line).group(0)
            if 'hg=' in line:
                hg = re.search(r'(?<=hg=).+',line).group(0)

#################### ######################## ####################

# kind of what Teal was thinking initially
#assignment = {"px": "GIMPS",
#        "v": 0.95, # transaction API version (float)

# Note: Each request type (e.g., uc, ga, etc.) starts with: px, v, t, and g.
assignment = {"v": 0.95, # transaction API version (float)
        "px": "GIMPS",
        "t": "uc", # transaction type
	"g": g, # program's self-assigned permanent ID (guid)
        "hg": hg , # machine's hardware hash ID (guid)
        "wg": "", # machine's Windows hardware hash ID (guid) # TODO -- for Windows
        "a": f'{platform.system()}64,{program},{version},{build}', # application version string (min length 10, max length 64)
	"c": f'{cpu_signature}', # CPU model string (min length 8, max length 64)
        "f": "", # CPU features string (min length 0, max length 64) # TODO -- common.c 582
        "L1": 0, # level 1 cache of CPU in KB (integer; set 0 if unavailable)
        "L2": 0, # level 2 cache of CPU in KB (integer; set 0 if unavailable)
        "np": os.cpu_count(), # number of physical CPUs/cores available to run assignments (integer >= 1) # TODO -- this gives hp count...does not account for systems that do not have hp
        "hp": 1, # number of hyperthreaded CPUs on each physical CPU (integer >= 0)
        "m": 0, # number of megabytes of physical memory (integer >= 0; set 0 if unavailable)
        "s": get_cpu_MHz(cpu_signature), # speed of CPU in Mhz; assumes all CPUs are same speed (integer)
        "h": 24, # hours per day CPU runs application (integer 0-24)
        "r": 0, # rolling average (integer; set 0 if unavailable) TODO -- ?
        "L3": 0, # L3 - level 3 cache of CPU in KB (integer; optional)
        "u": options.username if options.username else 'psu', # existing server account userID to bind CPU's owning user (max length 20; may be null, see notes)
        "cn": options.computer_name, # user-friendly public name of CPU (max length 20; may be null, see notes) # TODO -- put "computer name" in here.
        "ss": random.randint(0, 4000000), # security salt, a random number (integer; may be null)
        #"sh": '183CFA034BE5D3A40B5E710D2F25A5AA', # security hash (guid; may be null) Must be 32 chars (a requirement not updated in v5 documentation)
}
#assignment['sh'] = hashlib.md5(str.encode(primenet_v5_url + urlencode(assignment))).hexdigest()

############################################## ######### ######## ####################################################

def error_code(code):
    '''checks return codes from endpoints for errors'''
    if code != '0':
        debug_exit(f'ERROR: {error_codes[code]}') if code in error_codes else debug_exit("Unknown error code")

# functions
def endpoint(data, job=""):
    print(data)
    r = requests.post(primenet_v5_url, data)

    print(r.text)
    if r.text == "": # or len(r.text) == 0, this means we got no response back
        sys.exit()
    for text in r.text.split("\n"):
        res = re.search(r'(?<=pnErrorResult=).+',text)
        if res:
            error_code(res.group(0))
    print(f'{job} successful.\n')

# python3 primenet.py -d -T $GPU_type_of_work -u $prime_ID -p $prime_password -i "{'worktodo' + computer_number + '.txt'}"

def debug_exit(message):
    print(message)
    sys.exit(2)

def main(args):
    ''' On each startup we 1) ping the server, 2) update the computer, 3)'''
    #print(get_cpu_signature())
    #sys.exit()
    #print(assignment['c'])
    print("Welcome to Teal and Daniel's v5 PrimeNet Port!")
    #
    #endpoint(json.loads('{"v": "0.95", "t": "ps", "q": "0", "ss": 0, "sh": "183CFA034BE5D3A40B5E710D2F25A5AA"}'), "Pinging server") # Mimicking example command: `curl -sSi 'http://v5.mersenne.org/v5server/?px=GIMPS&v=0.95&t=ps&q=0&ss=&sh='`
    print(primenet_v5_url + urlencode(assignment), "\n")

    endpoint(assignment, "Updating/Registering")

if __name__=="__main__":
    # TODO -- error checking here?
    main(sys.argv[1:])
