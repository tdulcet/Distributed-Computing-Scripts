#!/usr/bin/env python3

'''
DC: Reverted remaining Python2 pieces to Python3 by Daniel Connelly. This version is used in the Google Colab scripts: https://github.com/tdulcet/Distributed-Computing-Scripts.
EWM: adapted from https://github.com/MarkRose/primetools/blob/master/mfloop.py by teknohog and Mark Rose, with help from Gord Palameta.
Automatic assignment handler for CUDALucas using manual testing forms at mersenne.org

Use `./primenet.py -h` to get more help
'''

################################################################################
#                                                                              #
#   (C) 2020 by Daniel Connelly.                                               #
#                                                                              #
#  This program is free software; you can redistribute it and/or modify it     #
#  under the terms of the GNU General Public License as published by the       #
#  Free Software Foundation; either version 2 of the License, or (at your      #
#  option) any later version.                                                  #
#                                                                              #
#  This program is distributed in the hope that it will be useful, but WITHOUT #
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or       #
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for   #
#  more details.                                                               #
#                                                                              #
#  You should have received a copy of the GNU General Public License along     #
#  with this program; see the file GPL.txt.  If not, you may view one at       #
#  http://www.fsf.org/licenses/licenses.html, or obtain one by writing to the  #
#  Free Software Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA     #
#  02111-1307, USA.                                                            #
#                                                                              #
################################################################################

import sys
import re
from time import sleep
import os
from optparse import OptionParser
import requests
from requests.exceptions import HTTPError

s = requests.Session() # session that maintains our cookies

primenet_v5_burl = b"http://v5.mersenne.org/v5server/?v=0.95&px=GIMPS"
primenet_baseurl = b"https://www.mersenne.org/"
primenet_login = False


def ass_generate(assignment):
    output = ""
    for key in assignment:
        output += key + "=" + assignment[key] + "&"
    # return output.rstrip("&")
    return output


def debug_print(text):
    if options.debug:
        print(progname + ": " + text)
        sys.stdout.flush()


def greplike(pattern, l):
    output = []
    for line in l:
        s = re.search(r"(" + pattern + ")$", line)
        if s:
            output.append(s.groups()[0])
    return output


def num_to_fetch(l, targetsize):
    num_existing = len(l)
    num_needed = targetsize - num_existing
    return max(num_needed, 0)


def readonly_file(filename):
    # Used when there is no intention to write the file back, so don't
    # check or write lockfiles. Also returns a single string, no list.
    contents = ""
    if os.path.exists(filename):
        with open(filename, "r") as f1:
            contents = f1.read()
    return contents


def read_list_file(filename):
    # Used when we plan to write the new version, so use locking
    lockfile = filename + ".lck"
    try:
        fd = os.open(lockfile, os.O_CREAT | os.O_EXCL)
        os.close(fd)
        if os.path.exists(filename):
            with open(filename, "r") as f1:
                contents = f1.readlines()
            return map(lambda x: x.rstrip(), contents)
        return []
    # This python2-style exception decl gives a syntax error in python3:
    # except OSError, e:
    # https://stackoverflow.com/questions/11285313/try-except-as-error-in-python-2-5-python-3-x
    # gives the fugly but portable-between-both-python2-and-python3 syntactical workaround:
    except OSError:
        _, e, _ = sys.exc_info()
        if e.errno == 17:
            return "locked"
        else:
            raise


def write_list_file(filename, l, mode="w"):
    # Assume we put the lock in upon reading the file, so we can
    # safely write the file and remove the lock
    lockfile = filename + ".lck"
    # A "null append" is meaningful, as we can call this to clear the
    # lockfile. In this case the main file need not be touched.
    if mode != "a" or len(l) > 0:
        content = "\n".join(l) + "\n"
        with open(filename, mode) as f1:
            f1.write(content)
    os.remove(lockfile)


def unlock_file(filename):
    lockfile = filename + ".lck"
    os.remove(lockfile)


def primenet_fetch(num_to_get):
    if not primenet_login:
        return []
    # As of early 2018, here is the full list of assignment-type codes supported by the Primenet server; Mlucas
    # v18 (and thus this script) supports only the subset of these indicated by an asterisk in the left column.
    # Supported assignment types may be specified via either their PrimeNet number code or the listed Mnemonic:
    #			Worktype:
    # Code		Mnemonic			Description
    # ----	-----------------	-----------------------
    #    0						Whatever makes the most sense
    #    1						Trial factoring to low limits
    #    2						Trial factoring
    #    4						P-1 factoring
    #    5						ECM for first factor on Mersenne numbers
    #    6						ECM on Fermat numbers
    #    8						ECM on mersenne cofactors
    # *100	SmallestAvail		                Smallest available first-time tests
    # *101	DoubleCheck			        Double-checking
    # *102	WorldRecord			        World record primality tests
    # *104	100Mdigit			        100M digit number to LL test (not recommended)
    # *150	SmallestAvailPRP	                First time PRP tests (Gerbicz)
    # *151	DoubleCheckPRP		                Doublecheck PRP tests (Gerbicz)
    # *152	WorldRecordPRP		                World record sized numbers to PRP test (Gerbicz)
    # *153	100MdigitPRP		                100M digit number to PRP test (Gerbicz)
    #  160						PRP on Mersenne cofactors
    #  161						PRP double-checks on Mersenne cofactors

    # Convert mnemonic-form worktypes to corresponding numeric value, check worktype value vs supported ones:
    if options.worktype == "SmallestAvail":
        options.worktype = "100"
    elif options.worktype == "DoubleCheck":
        options.worktype = "101"
    elif options.worktype == "WorldRecord":
        options.worktype = "102"
    elif options.worktype == "100Mdigit":
        options.worktype = "104"
    if options.worktype == "SmallestAvailPRP":
        options.worktype = "150"
    elif options.worktype == "DoubleCheckPRP":
        options.worktype = "151"
    elif options.worktype == "WorldRecordPRP":
        options.worktype = "152"
    elif options.worktype == "100MdigitPRP":
        options.worktype = "153"
    supported = set(['100', '101', '102', '104', '150', '151', '152', '153'])
    if options.worktype not in supported:
        debug_print("Unsupported/unrecognized worktype = " + options.worktype)
        return []
    assignment = {"cores": "1",
                  "num_to_get": str(num_to_get),
                  "pref": options.worktype,
                  "exp_lo": "",
                  "exp_hi": "",
                  }
    try:
        openurl = primenet_baseurl.decode(
            "utf-8") + "manual_assignment/?" + ass_generate(assignment) + "B1=Get+Assignments"
        # debug_print("Fetching work via URL = "+openurl)
        r = s.post(openurl)
        return greplike(workpattern, [line.decode() for line in r.iter_lines()])
    except HTTPError:
        debug_print("URL open error at primenet_fetch")
        return []


def get_assignment():
    w = read_list_file(workfile)
    if w == "locked":
        return "locked"

    tasks = greplike(workpattern, w)
    num_to_get = num_to_fetch(tasks, int(options.num_cache))

    if num_to_get < 1:
        debug_print(workfile + " already has >= " +
                    str(len(tasks)) + " entries, not getting new work")
        # Must write something anyway to clear the lockfile
        new_tasks = []
    else:
        debug_print("Fetching " + str(num_to_get) + " assignments")
        new_tasks = primenet_fetch(num_to_get)

    num_fetched = len(new_tasks)
    # debug_print("Fetched " + str() + " new_tasks: " + str(new_tasks))
    write_list_file(workfile, new_tasks, "a")
    if num_fetched < num_to_get:
        debug_print("Error: Failed to obtain requested number of new assignments, " +
                    str(num_to_get) + " requested, " + str(num_fetched) + " successfully retrieved")


def mersenne_find(line, complete=True):
    return re.search(r"rogram|CUDALucas", line)

# This has not been tested yet and thus is not called.
def update_progress():
    w = read_list_file(workfile)
    unlock_file(workfile)

    tasks = greplike(workpattern, w)
    found = re.search('=(.+?),', tasks[0])
    if found:
        assignment_id = found.group(1)
        # debug_print("update_progress: assignment_id = " + assignment_id)
    else:
        debug_print(
            "update_progress: Unable to extract valid Primenet assignment ID from first entry in " + workfile + ": " + tasks[0])
        return []
    found = re.search(',(.+?),', tasks[0])
    if found:
        p = found.group(1)
        statfile = 'p' + p + '.stat'
        w = read_list_file(statfile)
        unlock_file(statfile)
        # Extract iteration from most-recent statfile entry:
        found = re.search('= (.+?) ', w[len(w)-1])
        if found:
            iter = found.group(1)
            # debug_print("Iteration = " + iter)
            percent = str(100*float(iter)/float(p))
            percent = percent[0:4]
            # debug_print("% done = " + percent)
        else:
            debug_print(
                "update_progress: Unable to find .stat file corresponding to first entry in " + workfile + ": " + tasks[0])
            return []
    else:
        debug_print(
            "update_progress: Unable to extract valid exponent substring from first entry in " + workfile + ": " + tasks[0])
        return []
    # Found eligible current-assignment in workfile and a matching p*.stat file with last-entry containing "Iteration = ":
    mach_id = ""
    # debug_print("len(mach_id) = " + str(len(mach_id)))
    w = read_list_file(localfile)
    unlock_file(localfile)
    # debug_print("len(localfile) = " + str(len(w)))
    for i in range(len(w)):
        found = re.search('mach_id', w[i])
        if found:
            j = len(w[i])
            # Assume primenet-assigned guid is 32 chars, at end of line:
            mach_id = w[i][j-32:j]
            break
    # debug_print("len(mach_id) = " + str(len(mach_id)))
    if len(mach_id) == 0:
        debug_print(
            "update_progress: Unable to extract valid mach_id entry from " + localfile)
        return []

    # Assignment Progress fields:
    # g= the machine's GUID (32 chars, assigned by Primenet on 1st-contact from a given machine, stored in 'mach_id = ' entry of local.ini file of rundir)
    # k= the assignment ID (32 chars, follows '=' in Primenet-geerated workfile entries)
    # stage= LL in this case, although an LL test may be doing TF or P-1 work first so it's possible to be something besides LL
    # c= the worker thread of the machine ... always sets = 1 for now, elaborate later is desired
    # p= progress in %-done, 4-char format = xy.z
    # d= when the client is expected to check in again (in seconds ... 86400 = 24 hours)
    # e= the ETA of completion - I just set it to 86400/24 hours as an example
    #
    ap_url = primenet_v5_burl.decode() + "&t=ap&g=" + mach_id + "&k=" + \
        assignment_id + "&stage=LL&c=1&p=" + percent + "&d=86400&e=86400"


    debug_print("ap_url: " + ap_url)
    try:
        r = s.post(ap_url)
        page = r.content.decode()

        # debug_print("update_progress returns: " + str(len(page)) + " lines:")
        for i in range(len(page)):
            # debug_print("line[" + str(i) + "] = " + page[i])
            found = re.search('SUCCESS', page[i])
            if found:
                # debug_print("Current-assignment [p = " + p + "] update_progress was successful.")
                return []
        # debug_print("Current-assignment [p = " + p + "] update_progress may have failed; return value:")
        # for i in range(len(page)):
        #	debug_print("line[" + str(i) + "] = " + page[i])
    except HTTPError:
        debug_print("update_progress: URL open error")

    return []


def submit_work():
    # Only submit completed work, i.e. the exponent must not exist in worktodo file any more
    files = [resultsfile, sentfile]
    rs = list(map(read_list_file, files))
    #
    # EWM: Mark Rose comments:
    # This code is calling the read_list_file function for every item in the files list. It's putting the
    # results of the function for the first file, resultsfile, in the first position in the array, rs[0].
    # Inside read_list_file, it's opening the file, calling readlines to get the contents of it into an array,
    # then calling the rstrip function on every line to remove trailing whitespace. It then returns the array.
    #
    # EWM: Note that read_list_file does not need the file(s) to exist - nonexistent files simply yield 0-length rs-array entries.

    if "locked" in rs:
        # Remove the lock in case one of these was unlocked at start
        for i in range(len(files)):
            if rs[i] != "locked":
                debug_print("Calling write_list_file() for" + files[i])
                write_list_file(files[i], [], "a")
        return "locked"

    results = rs[0]
    # remove nonsubmittable lines from list of possibles
    results = filter(mersenne_find, results)
    # if a line was previously submitted, discard
    results_send = [line for line in results if line not in rs[1]]
    # In case resultsfile contained duplicate lines for some reason
    results_send = list(set(results_send))
    debug_print("New-results has " + str(len(results_send)) + " entries.")

    # Only for new results, to be appended to results_sent
    sent = []

    if len(results_send) == 0:
        debug_print("No complete results found to send.")
        # Don't just return here, files are still locked...
    else:
        # EWM: Switch to one-result-line-at-a-time submission to support error-message-on-submit handling:
        for sendline in results_send:
            debug_print("Submitting\n" + sendline)
            try:
                url = primenet_baseurl + b"manual_result/default.php"
                r = s.post(url, data={"data": sendline})
                res = r.text
                if "Error" in res:
                    ibeg = res.find("Error")
                    iend = res.find("</div>", ibeg)
                    print("Submission failed: '" + res[ibeg:iend] + "'")
                elif "Accepted" in res:
                    sent += sendline
                else:
                    print("Submission of results line '" + sendline +
                          "' failed for reasons unknown - please try manual resubmission.")
            except HTTPError:
                debug_print("URL open error")

    # EWM: Append entire results_send rather than just sent to avoid resubmitting
    write_list_file(sentfile, results_send, "a")
    # bad results (e.g. previously-submitted duplicates) every time the script executes.
    # EWM: don't write anything to resultsfile, but still need to remove lock placed on it by read_list_file
    unlock_file(resultsfile)


parser = OptionParser()

parser.add_option("-d", "--debug", action="store_true",
                  dest="debug", default=False, help="Display debugging info")

parser.add_option("-u", "--username", dest="username",
                  help="Primenet user name")
parser.add_option("-p", "--password", dest="password",
                  help="Primenet password")
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

# Good refs re. Python regexp: https://www.geeksforgeeks.org/pattern-matching-python-regex/, https://www.python-course.eu/re.php
# pre-v19 only handled LL-test assignments starting with either DoubleCheck or Test, followed by =, and ending with 3 ,number pairs:
#
#	workpattern = r"(DoubleCheck|Test)=.*(,[0-9]+){3}"
#
# v19 we add PRP-test support - both first-time and DC of these start with PRP=, the DCs tack on 2 more ,number pairs representing
# the PRP base to use and the PRP test-tyoe (the latter is a bit complex to explain here). Sample of the 4 worktypes supported by v19:
#
#	Test=7A30B8B6C0FC79C534A271D9561F7DCC,89459323,76,1
#	DoubleCheck=92458E009609BD9E10577F83C2E9639C,50549549,73,1
#	PRP=BC914675C81023F252E92CF034BEFF6C,1,2,96364649,-1,76,0
#	PRP=51D650F0A3566D6C256B1679C178163E,1,2,81348457,-1,75,0,3,1
#
# and the obvious regexp pattern-modification is
#
#	workpattern = r"(DoubleCheck|Test|PRP)=.*(,[0-9]+){3}"
#
# Here is where we get to the kind of complication the late baseball-philosopher Yogi Berra captured via his aphorism,
# "In theory, theory and practice are the same. In practice, they're different". Namely, while the above regexp pattern
# should work on all 4 assignment patterns, since each has a string of at least 3 comma-separated nonnegative ints somewhere
# between the 32-hexchar assignment ID and end of the line, said pattern failed on the 3rd of the above 4 assignments,
# apparently because when the regexp is done via the 'greplike' below, the (,[0-9]+){3} part of the pattern gets implicitly
# tiled to the end of the input line. Assignment # 3 above happens to have a negative number among the final 3, thus the
# grep fails. This weird behavior is not reproducible running Python in console mode:
#
#	>>> import re
#	>>> s1 = "DoubleCheck=92458E009609BD9E10577F83C2E9639C,50549549,73,1"
#	>>> s2 = "Test=7A30B8B6C0FC79C534A271D9561F7DCC,89459323,76,1"
#	>>> s3 = "PRP=BC914675C81023F252E92CF034BEFF6C,1,2,96364649,-1,76,0"
#	>>> s4 = "PRP=51D650F0A3566D6C256B1679C178163E,1,2,81348457,-1,75,0,3,1"
#	>>> print re.search(r"(DoubleCheck|Test|PRP)=.*(,[0-9]+){3}" , s1)
#	<_sre.SRE_Match object at 0x1004bd250>
#	>>> print re.search(r"(DoubleCheck|Test|PRP)=.*(,[0-9]+){3}" , s2)
#	<_sre.SRE_Match object at 0x1004bd250>
#	>>> print re.search(r"(DoubleCheck|Test|PRP)=.*(,[0-9]+){3}" , s3)
#	<_sre.SRE_Match object at 0x1004bd250>
#	>>> print re.search(r"(DoubleCheck|Test|PRP)=.*(,[0-9]+){3}" , s4)
#	<_sre.SRE_Match object at 0x1004bd250>
#
# Anyhow, based on that I modified the grep pattern to work around the weirdness, by appending .* to the pattern, thus
# changing things to "look for 3 comma-separated nonnegative ints somewhere in the assignment, followed by anything",
# also now to specifically look for a 32-hexchar assignment ID preceding such a triplet, and to allow whitespace around
# the =. The latter bit is not  needed based on current server assignment format, just a personal aesthetic bias of mine:
#
workpattern = r"(DoubleCheck|Test|PRP)\s*=\s*([0-9A-F]){32}(,[0-9]+){3}.*"

# mersenne.org limit is about 4 KB; stay on the safe side
sendlimit = 3000

while True:
    # Log in to primenet
    try:
        login_data = {"user_login": options.username,
                      "user_password": options.password,
                      }

        url = primenet_baseurl + b"default.php"
        #r = requests.post(url, data=login_data)
        r = s.post(url, data=login_data)
        if options.username + "<br>logged in" not in r.text:
            primenet_login = False
            debug_print("Login failed.")
        else:
            primenet_login = True
            # while update_progress() == "locked":
            #	debug_print("Waiting for workfile access...")
            #	sleep(2)
            while submit_work() == "locked":
                debug_print("Waiting for results file access...")
                sleep(2)
    except HTTPError:
        debug_print("Primenet URL open error")

    if primenet_login:
        while get_assignment() == "locked":
            debug_print("Waiting for worktodo.ini access...")
            sleep(2)
    if timeout <= 0:
        break
    sleep(timeout)
