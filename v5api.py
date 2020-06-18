import requests
import sys
import json

primenet_v5_url = "http://v5.mersenne.org/v5server/?px=GIMPS"

""" # kind of what Teal was thinking initially
assignment = {"px": "GIMPS", # projection application identifier (string; minimum length 1, maximum length 8)
        "v": "0.95", # transaction API version (float)
        "t": "uc", # transaction type
	"g": mach_id, # program's self-assigned permanent ID (guid)
        "hg": hg, # machine's hardware hash ID (guid)
        "wg": wg, # machine's Windows hardware hash ID (guid)
        "a": a, # application version string (min length 10, max length 64)
	"c": 1, # CPU model string (min length 8, max length 64)
        "f": f, # CPU features string (min length 0, max length 64)
        "L1": L1, # level 1 cache of CPU in KB (integer; set 0 if unavailable)
        "L2": L2, # level 2 cache of CPU in KB (integer; set 0 if unavailable)
        "L3": L3, # L3 - level 3 cache of CPU in KB (integer; optional)
        "np": np, # number of physical CPUs/cores available to run assignments (integer >= 1)
        "hp": hp, # number of hyperthreaded CPUs on each physical CPU (integer >= 0)
        "m": m, # number of megabytes of physical memory (integer >= 0; set 0 if unavailable)
        "s": s, # speed of CPU in Mhz; assumes all CPUs are same speed (integer)
        "h": h, # hours per day CPU runs application (integer 0-24)
        "r": r, # rolling average (integer; set 0 if unavailable)
        "u": 'psu', # existing server account userID to bind CPU's owning user (max length 20; may be null, see notes)
        "cn": cn, # user-friendly public name of CPU (max length 20; may be null, see notes)
        "ss": '', # security salt, a random number (integer; may be null)
        "sh": '', # security hash (guid; may be null)
}
"""

############################################## Optional Helpers ####################################################
"""
def some_mersenne_function(args): # for example the "Update" API request
    #params = ["v=", "t="]
    params = ["v=", "t="]
    return "".join(f"&{tup[0]}{tup[1]}" for tup in zip(params, args))
    #return (f"{tup[0]}" p in zip(params, args).join('&'))
    #return "".join(map(str, zip(params, args)))
    #return map(params, args).join('&')
#print(some_mersenne_function(["0.95", "UC"]))
"""

"""
# https://stackoverflow.com/a/21584580/8651748
def query_string_to_dict(url):
    '''If we use the `some_mersenne_function` then we can easily
       convert the string produced to a dict, which is the urlencoding we need for a `request.get` call.
    '''
    from urllib.parse import urlsplit, parse_qs
    return dict(parse.parse_qs(parse.urlsplit(url).query))
"""
"""
def create_assign_dict(**kargs): # (preferred)
    '''Takes in named variables and returns them as a dictionary.
       Useful for creating an `assignment` dictionary with a small amount of code.
       (e.g., creat_assign_dict(px="GIMPS", v="0.95"...) -> {"px": "GIMPS", "V": "0.95"...})
    '''
    return kargs
"""
############################################## ######### ######## ####################################################

# functions
def uc(assignment):
    pass

def ps(data):
    '''Mimicking command: `curl -sSi 'http://v5.mersenne.org/v5server/?px=GIMPS&v=0.95&t=ps&q=0&ss=&sh='` '''
    r = requests.post(primenet_v5_url, data)
    print(r.text) # for Teal to see (successful) output
    return False if "SUCCESS" not in r.text else True

# python3 primenet.py -d -T $GPU_type_of_work -u $prime_ID -p $prime_password -i "{'worktodo' + computer_number + '.txt'}"

def debug_exit(message):
    print(message)
    sys.exit(2)

def main(args):
    commands = ["uc", "po", "ga", "ra", "au", "ap", "ar", "bd", "ps"]
    print("Welcome to Teal and Daniel's v5 PrimeNet Port!")
    string = args[0]
    print(string)
    assignment = json.loads(string)
    command =  [x for x in commands if x in assignment.values()][0]

    'if not ps(assignment):
        debug_exit("ERROR: could not connect to V5 API")
    '''
    '''
    ############# THIS #################
    if command == 'uc': # 'UPDATE COMPUTER':
        # call function
        pass
    elif command == 'po': # 'PROGRAM OPTIONS':
        pass
    elif command == 'ga': #'GET ASSIGNMENT':
        pass
    elif command == 'ra': # 'REGISTER ASSIGNMENT':
        pass
    elif command == 'au': # 'ASSIGNMENT UN-RESERVE'
        pass
    elif command == 'ap': # 'ASSIGNMENT PROGRESS'
        pass
    elif command == 'ar': # 'ASSIGNMENT RESULT'
        pass
    elif command == 'bd': # Benchmark Data Statistics
        pass
    ############# ##### #################
    '''
    ############# OR THIS ################# (if we named our functions `uc`, `po`, etc. Source: https://stackoverflow.com/a/22021058/8651748
    func_to_run = globals()[command]
    func_to_run(assignment)
    ############# ##### #################

if __name__=="__main__":
    # TODO -- error checking here?
    main(sys.argv[1:])
