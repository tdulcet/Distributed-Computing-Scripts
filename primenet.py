#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Automatic assignment handler for Mlucas, GpuOwl and CUDALucas.

[*] Revised by Teal Dulcet and Daniel Connelly for CUDALucas (2020)
    Original Authorship(s):
     * # EWM: adapted from https://github.com/MarkRose/primetools/blob/master/mfloop.py
            by teknohog and Mark Rose, with help rom Gord Palameta.
     * # 2020: support for computer registration and assignment-progress via
            direct Primenet-v5-API calls by Loïc Le Loarer <loic@le-loarer.org>

[*] List of supported v5 operations:
    * Update Computer Info (uc, register_instance) (Credit: Loarer & Dulcet)
    * Program Options (po, program_options) (Credit: Connelly & Dulcet)
    * Get Assignment (ga, get_assignment) (Credit: Connelly & Dulcet)
    * Register Assignment (ra, register_assignment) (Credit: Dulcet) NOTE: DONE; not used
    * Assignment Un-Reserve (au, assignment_unreserve) (Credit: Dulcet)
    * Assignment Progress (ap, send_progress) (Credit: Loarer & Dulcet)
    * Assignment Result (ar, report_result) (Credit: Loarer & Dulcet)
'''

################################################################################
#                                                                              #
#   (C) 2017-2021 by Daniel Connelly and Teal Dulcet.                          #
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
from __future__ import division, print_function, unicode_literals
import subprocess
import random
import uuid
from collections import namedtuple
import sys
import os
import re
import time
from datetime import datetime, timedelta
import optparse
from hashlib import md5
import json
import platform
import logging
import csv
import math
from decimal import Decimal
import threading
import shutil
import locale

try:
    # Python 3
    from urllib.parse import urlencode
    from requests.exceptions import ConnectionError, HTTPError
except ImportError:
    # Python 2
    from urllib import urlencode
    from urllib2 import URLError as ConnectionError
    from urllib2 import HTTPError

try:
    from configparser import ConfigParser, Error as ConfigParserError
except ImportError:
    from ConfigParser import ConfigParser, Error as ConfigParserError  # ver. < 3.0

if sys.version_info[:2] >= (3, 7):
    # If is OK to use dict in 3.7+ because insertion order is guaranteed to be preserved
    # Since it is also faster, it is better to use raw dict()
    OrderedDict = dict
else:
    try:
        from collections import OrderedDict
    except ImportError:
        # For Python 2.6 and before which don't have OrderedDict
        try:
            from ordereddict import OrderedDict
        except ImportError:
            # Tests will not work correctly but it doesn't affect the
            # functionality
            OrderedDict = dict

try:
    from statistics import median_low
except ImportError:
    def median_low(mylist):
        sorts = sorted(mylist)
        length = len(sorts)
        return sorts[(length - 1) // 2]

try:
    from math import log2
except ImportError:
    def log2(x):
        return math.log(x, 2)

try:
    import requests
except ImportError:
    print("Installing requests as dependency")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    print("The Requests library has been installed. Please run the program again")
    sys.exit(0)

locale.setlocale(locale.LC_ALL, '')
s = requests.Session()  # session that maintains our cookies

# [***] Daniel Connelly's functions


# register assignment
# Note: this function is not used
def register_assignment(cpu, assignment, retry_count=0):
    """Register an assignment with the PrimeNet server."""
    if retry_count >= 5:
        logging.info("Retry count exceeded.")
        return
    args = primenet_v5_bargs.copy()
    args["t"] = "ra"
    args["g"] = guid
    args["c"] = cpu
    args["w"] = assignment.work_type
    args["n"] = assignment.n
    if assignment.work_type == primenet_api.WORK_TYPE_FIRST_LL or assignment.work_type == primenet_api.WORK_TYPE_DBLCHK:
        if assignment.work_type == primenet_api.WORK_TYPE_FIRST_LL:
            work_type_str = "LL"
        else:
            work_type_str = "Double check"
        args["sf"] = assignment.sieve_depth
        args["p1"] = assignment.pminus1ed
    elif assignment.work_type == primenet_api.WORK_TYPE_PRP:
        work_type_str = "PRP"
        args["A"] = "{0:.0f}".format(assignment.k)
        args["b"] = assignment.b
        args["C"] = assignment.c
        args["sf"] = assignment.sieve_depth
        args["saved"] = assignment.tests_saved
    elif assignment.work_type == primenet_api.WORK_TYPE_PFACTOR:
        work_type_str = "P-1"
        args["A"] = "{0:.0f}".format(assignment.k)
        args["b"] = assignment.b
        args["C"] = assignment.c
        args["sf"] = assignment.sieve_depth
        args["saved"] = assignment.tests_saved
    elif assignment.work_type == primenet_api.WORK_TYPE_PMINUS1:
        work_type_str = "P-1"
        args["A"] = "{0:.0f}".format(assignment.k)
        args["b"] = assignment.b
        args["C"] = assignment.c
        args["B1"] = "{0:.0f}".format(assignment.B1)
        if assignment.B2 != 0:
            args["B2"] = "{0:.0f}".format(assignment.B2)
    retry = False
    logging.info("Registering assignment: {0} {1}".format(
        work_type_str, assignment.n))
    result = send_request(guid, args)
    if result is None:
        logging.debug("ERROR while registering assignment on mersenne.org")
        retry = True
    else:
        rc = int(result["pnErrorResult"])
        if rc == primenet_api.ERROR_OK:
            assignment.uid = result["k"]
            logging.info(
                "Assignment registered as: {0}".format(assignment.uid))
            # TODO: Update assignment in workfile
        else:
            logging.debug("ERROR while registering assignment on mersenne.org")
            if rc == primenet_api.ERROR_UNREGISTERED_CPU:
                logging.debug(
                    "UNREGISTERED CPU ERROR: pick a new GUID and register again")
                register_instance(None)
                retry = True
            elif rc == primenet_api.ERROR_STALE_CPU_INFO:
                logging.debug("STALE CPU INFO ERROR: re-send computer update")
                register_instance(guid)
                retry = True
    if retry:
        return ra(assignment, retry_count + 1)


# TODO -- have people set their own program options for commented out portions
def program_options(guid, first_time, retry_count=0):
    """Sets the program options on the PrimeNet server."""
    if retry_count >= 5:
        logging.info("Retry count exceeded.")
        return
    args = primenet_v5_bargs.copy()
    args["t"] = "po"
    args["g"] = guid
    # no value updates all cpu threads with given worktype
    args["c"] = ""  # cpu
    if first_time:
        args["w"] = worktype
        args["nw"] = options.WorkerThreads
        # args["Priority"] = 1
        args["DaysOfWork"] = int(round(options.DaysOfWork))
        memory = int(.9 * options.memory)
        args["DayMemory"] = memory
        args["NightMemory"] = memory
        # args["DayStartTime"] = 0
        # args["NightStartTime"] = 0
        # args["RunOnBattery"] = 1
    retry = False
    logging.info("Exchanging program options with server")
    result = send_request(guid, args)
    if result is None:
        parser.error("Error while setting program options on mersenne.org")
    else:
        rc = int(result["pnErrorResult"])
        if rc == primenet_api.ERROR_OK:
            pass
        else:
            if rc == primenet_api.ERROR_UNREGISTERED_CPU:
                logging.debug(
                    "UNREGISTERED CPU ERROR: pick a new GUID and register again")
                register_instance(None)
                retry = True
            elif rc == primenet_api.ERROR_STALE_CPU_INFO:
                logging.debug("STALE CPU INFO ERROR: re-send computer update")
                register_instance(guid)
                retry = True
            if retry:
                return program_options(guid, first_time, retry_count + 1)
            parser.error("Error while setting program options on mersenne.org")
    if "w" in result and int(result["w"]):
        config.set("PrimeNet", "WorkPreference", result["w"])
    if "nw" in result:
        config.set("PrimeNet", "WorkerThreads", result["nw"])
    if "Priority" in result:
        config.set("PrimeNet", "Priority", result["Priority"])
    if "DaysOfWork" in result:
        config.set("PrimeNet", "DaysOfWork", result["DaysOfWork"])
    if "RunOnBattery" in result:
        config.set("PrimeNet", "RunOnBattery", result["RunOnBattery"])
    # if not config.has_option("PrimeNet", "first_time"):
        # config.set("PrimeNet", "first_time", "false")
    if first_time:
        config.set("PrimeNet", "SrvrP00", str(int(config.get(
            "PrimeNet", "SrvrP00")) + 1 if config.has_option("PrimeNet", "SrvrP00") else 0))
    else:
        config.set("PrimeNet", "SrvrP00", result["od"])


def assignment_unreserve(assignment, retry_count=0):
    """Unreserves an assignment from the PrimeNet server."""
    if guid is None:
        logging.error("Cannot unreserve, the registration is not done")
    if not assignment or not assignment.uid:
        return
    if retry_count >= 5:
        logging.info("Retry count exceeded.")
        return
    args = primenet_v5_bargs.copy()
    args["t"] = "au"
    args["g"] = guid
    args["k"] = assignment.uid
    retry = False
    logging.info("Unreserving {0}".format(assignment.n))
    result = send_request(guid, args)
    if result is None:
        logging.debug(
            "ERROR while releasing assignment on mersenne.org: assignment_id={0}".format(assignment.uid))
        retry = True
    else:
        rc = int(result["pnErrorResult"])
        if rc == primenet_api.ERROR_OK:
            # TODO: Delete assignment from workfile
            pass
        else:
            logging.debug(
                "ERROR while releasing assignment on mersenne.org: assignment_id={0}".format(assignment.uid))
            if rc == primenet_api.ERROR_UNREGISTERED_CPU:
                logging.debug(
                    "UNREGISTERED CPU ERROR: pick a new GUID and register again")
                register_instance(None)
                retry = True
    if retry:
        return assignment_unreserve(assignment, retry_count + 1)


def unreserve(dirs, p):
    """Unreserve a specific exponent from the workfile."""
    for dir in dirs:
        workfile = os.path.join(dir, options.workfile)
        tasks = readonly_list_file(workfile)
        assignment = next((assignment for assignment in (parse_assignment(
            dir, task) for task in tasks) if assignment and assignment.n == p), None)
        if assignment:
            assignment_unreserve(assignment)
            break
    else:
        logging.error("Error unreserving exponent: {0} not found in workfile{1}".format(
            p, "s" if len(dirs) > 1 else ""))


def unreserve_all(dirs):
    """Unreserves all assignments in the given directories."""
    logging.info("Quitting GIMPS immediately.")
    for dir in dirs:
        workfile = os.path.join(dir, options.workfile)
        tasks = readonly_list_file(workfile)
        assignments = OrderedDict((assignment.uid, assignment) for assignment in (
            parse_assignment(dir, task) for task in tasks) if assignment and assignment.uid).values()
        for assignment in assignments:
            assignment_unreserve(assignment)
        # os.remove(workfile)


def get_cpu_signature():
    """Returns the CPU signature, which is a string that uniquely identifies the CPU."""
    output = ""
    if platform.system() == "Windows":
        output = subprocess.check_output('wmic cpu list brief').decode()
    elif platform.system() == "Darwin":
        os.environ['PATH'] = os.environ['PATH'] + os.pathsep + '/usr/sbin'
        command = "sysctl -n machdep.cpu.brand_string"
        output = subprocess.check_output(command).decode().strip()
    elif platform.system() == "Linux":
        with open('/proc/cpuinfo', 'r') as f1:
            for line in f1:
                if "model name" in line:
                    output = re.sub(".*model name.*:", "",
                                    line.rstrip(), 1).lstrip()
                    break
    return output


cpu_signature = get_cpu_signature()

# END Daniel's Functions


primenet_v5_burl = "http://v5.mersenne.org/v5server/"
PRIMENET_TRANSACTION_API_VERSION = 0.95
# GIMPS programs to use in the application version string when registering with PrimeNet
PROGRAMS = [
    {"name": "Prime95", "version": "30.7", "build": 9},
    {"name": "Mlucas", "version": "20.1"},
    {"name": "GpuOwl", "version": "7.2"},
    {"name": "CUDALucas", "version": "2.06"}]
ERROR_RATE = 0.018  # Estimated LL error rate on clean run
# Estimated PRP error rate (assumes Gerbicz error-checking)
PRP_ERROR_RATE = 0.0001
_V5_UNIQUE_TRUSTED_CLIENT_CONSTANT_ = 17737
primenet_v5_bargs = OrderedDict(
    (("px", "GIMPS"), ("v", PRIMENET_TRANSACTION_API_VERSION)))
primenet_baseurl = "https://www.mersenne.org/"
primenet_login = False


class primenet_api:
    ERROR_OK = 0
    ERROR_SERVER_BUSY = 3
    ERROR_INVALID_VERSION = 4
    ERROR_INVALID_TRANSACTION = 5
    # Returned for length, type, or character invalidations.
    ERROR_INVALID_PARAMETER = 7
    ERROR_ACCESS_DENIED = 9
    ERROR_DATABASE_CORRUPT = 11
    ERROR_DATABASE_FULL_OR_BROKEN = 13
    # Account related errors:
    ERROR_INVALID_USER = 21
    # Computer cpu/software info related errors:
    ERROR_UNREGISTERED_CPU = 30
    ERROR_OBSOLETE_CLIENT = 31
    ERROR_STALE_CPU_INFO = 32
    ERROR_CPU_IDENTITY_MISMATCH = 33
    ERROR_CPU_CONFIGURATION_MISMATCH = 34
    # Work assignment related errors:
    ERROR_NO_ASSIGNMENT = 40
    ERROR_INVALID_ASSIGNMENT_KEY = 43
    ERROR_INVALID_ASSIGNMENT_TYPE = 44
    ERROR_INVALID_RESULT_TYPE = 45
    ERROR_INVALID_WORK_TYPE = 46
    ERROR_WORK_NO_LONGER_NEEDED = 47

    WP_WHATEVER = 0  # Whatever makes most sense
    WP_FACTOR_LMH = 1  # Factor big numbers to low limits
    WP_FACTOR = 2  # Trial factoring
    WP_PMINUS1 = 3  # P-1 of small Mersennes --- not supported
    WP_PFACTOR = 4  # P-1 of large Mersennes
    WP_ECM_SMALL = 5  # ECM of small Mersennes looking for first factors
    WP_ECM_FERMAT = 6  # ECM of Fermat numbers
    WP_ECM_CUNNINGHAM = 7  # ECM of Cunningham numbers --- not supported
    WP_ECM_COFACTOR = 8  # ECM of Mersenne cofactors
    WP_LL_FIRST = 100  # LL first time tests
    WP_LL_DBLCHK = 101  # LL double checks
    WP_LL_WORLD_RECORD = 102  # LL test of world record Mersenne
    WP_LL_100M = 104  # LL 100 million digit
    WP_PRP_FIRST = 150  # PRP test of big Mersennes
    WP_PRP_DBLCHK = 151  # PRP double checks
    WP_PRP_WORLD_RECORD = 152  # PRP test of world record Mersennes
    WP_PRP_100M = 153  # PRP test of 100M digit Mersennes
    WP_PRP_NO_PMINUS1 = 154  # PRP test that if possible also needs P-1
    WP_PRP_DC_PROOF = 155  # PRP double-check where a proof will be produced
    WP_PRP_COFACTOR = 160  # PRP test of Mersenne cofactors
    WP_PRP_COFACTOR_DBLCHK = 161  # PRP double check of Mersenne cofactors

    WORK_TYPE_FACTOR = 2
    WORK_TYPE_PMINUS1 = 3
    WORK_TYPE_PFACTOR = 4
    WORK_TYPE_ECM = 5
    WORK_TYPE_PPLUS1 = 6		# Not yet supported by the server
    WORK_TYPE_FIRST_LL = 100
    WORK_TYPE_DBLCHK = 101
    WORK_TYPE_PRP = 150
    WORK_TYPE_CERT = 200

    AR_NO_RESULT = 0		# No result, just sending done msg
    AR_TF_FACTOR = 1		# Trial factoring, factor found
    AR_P1_FACTOR = 2		# P-1, factor found
    AR_ECM_FACTOR = 3		# ECM, factor found
    AR_TF_NOFACTOR = 4		# Trial Factoring no factor found
    AR_P1_NOFACTOR = 5		# P-1 factoring no factor found
    AR_ECM_NOFACTOR = 6		# ECM factoring no factor found
    AR_PP1_FACTOR = 7  # P+1, factor found
    AR_PP1_NOFACTOR = 8  # P+1 factoring no factor found
    AR_LL_RESULT = 100  # LL result, not prime
    AR_LL_PRIME = 101  # LL result, Mersenne prime
    AR_PRP_RESULT = 150  # PRP result, not prime
    AR_PRP_PRIME = 151  # PRP result, probably prime
    AR_CERT = 200  # Certification result


errors = {
    primenet_api.ERROR_SERVER_BUSY: "Server busy",
    primenet_api.ERROR_INVALID_VERSION: "Invalid version",
    primenet_api.ERROR_INVALID_TRANSACTION: "Invalid transaction",
    primenet_api.ERROR_INVALID_PARAMETER: "Invalid parameter",
    primenet_api.ERROR_ACCESS_DENIED: "Access denied",
    primenet_api.ERROR_DATABASE_CORRUPT: "Server database malfunction",
    primenet_api.ERROR_DATABASE_FULL_OR_BROKEN: "Server database full or broken",
    primenet_api.ERROR_INVALID_USER: "Invalid user",
    primenet_api.ERROR_UNREGISTERED_CPU: "CPU not registered",
    primenet_api.ERROR_OBSOLETE_CLIENT: "Obsolete client, please upgrade",
    primenet_api.ERROR_STALE_CPU_INFO: "Stale cpu info",
    primenet_api.ERROR_CPU_IDENTITY_MISMATCH: "CPU identity mismatch",
    primenet_api.ERROR_CPU_CONFIGURATION_MISMATCH: "CPU configuration mismatch",
    primenet_api.ERROR_NO_ASSIGNMENT: "No assignment",
    primenet_api.ERROR_INVALID_ASSIGNMENT_KEY: "Invalid assignment key",
    primenet_api.ERROR_INVALID_ASSIGNMENT_TYPE: "Invalid assignment type",
    primenet_api.ERROR_INVALID_RESULT_TYPE: "Invalid result type"}

# Assignment = namedtuple('Assignment', "work_type, uid, k, b, n, c, sieve_depth, pminus1ed, B1, B2, tests_saved, prp_base, prp_residue_type, known_factors, prp_dblchk, cert_squarings")
Assignment = namedtuple(
    'Assignment',
    "work_type, uid, k, b, n, c, sieve_depth, pminus1ed, B1, B2, tests_saved, prp_dblchk")


def greplike(pattern, lines):
    """Return a list of all the strings in lines that match the regular expression pattern."""
    output = []
    for line in lines:
        s = pattern.search(line)
        if s:
            output.append(s.group(0))
    return output


def readonly_list_file(filename, mode="r"):
    """Reads a file line by line into a list. """
    # Used when there is no intention to write the file back, so don't
    # check or write lockfiles. Also returns a single string, no list.
    try:
        with open(filename, mode=mode) as File:
            return [line.rstrip() for line in File]
    except (IOError, OSError):
        return []


def write_list_file(filename, line, mode="w"):
    """Write a list of strings to a file."""
    # A "null append" is meaningful, as we can call this to clear the
    # lockfile. In this case the main file need not be touched.
    if not ("a" in mode and len(line) == 0):
        newline = b'\n' if 'b' in mode else '\n'
        content = newline.join(line) + newline
        with open(filename, mode) as File:
            File.write(content)


def is_prime(n):
    """This function checks if a number is prime."""
    if n < 2:
        return False

    for p in range(2, int(math.sqrt(n)) + 1):
        if n % p == 0:
            return False
    return True


def header_lines(filename):
    """Read the first five lines of a file and return them as a list of strings."""
    with open(filename, mode='rb') as f:
        return [f.readline().decode().rstrip() for _ in range(5)]


def checksum_md5(filename):
    """Calculates the MD5 checksum of a file."""
    amd5 = md5()
    with open(filename, mode='rb') as f:
        for chunk in iter(lambda: f.read(128 * amd5.block_size), b''):
            amd5.update(chunk)
    return amd5.hexdigest()


def upload_proof(filename):
    """Upload a file to the PrimeNet server."""
    header = header_lines(filename)
    if header[0] != 'PRP PROOF':
        return False
    exponent = header[4].partition("=")[2]
    logging.info("Proof file exponent is {0}".format(exponent))
    fileHash = checksum_md5(filename)
    logging.info("MD5 of “{0}” is {1}".format(filename, fileHash))
    fileSize = os.path.getsize(filename)
    logging.info("Filesize of “{0}” is {1:n}".format(filename, fileSize))

    while True:
        args = {"UserID": options.username,
                "Exponent": exponent[1:],
                "FileSize": fileSize,
                "FileMD5": fileHash}
        r = s.get(primenet_baseurl + 'proof_upload/',
                  params=args, timeout=180)
        json = r.json()
        if 'error_status' in json:
            if json['error_status'] == 409:
                logging.error("Proof “{0}” already uploaded".format(filename))
                logging.error(str(json))
                return True
            logging.error(
                "Unexpected error during “{0}” upload".format(filename))
            logging.error(str(json))
            return False
        r.raise_for_status()
        if 'URLToUse' not in json:
            logging.error(
                "For proof “{0}”, server response missing URLToUse:".format(filename))
            logging.error(str(json))
            return False
        if 'need' not in json:
            logging.error(
                "For proof “{0}”, server response missing need list:".format(filename))
            logging.error(str(json))
            return False

        origUrl = json['URLToUse']
        baseUrl = 'https' + \
            origUrl[4:] if origUrl.startswith('http:') else origUrl
        pos, end = next((int(a), b) for a, b in json['need'].items())
        if pos > end or end >= fileSize:
            logging.error(
                "For proof “{0}”, need list entry bad:".format(filename))
            logging.error(str(json))
            return False

        if pos:
            logging.info("Resuming from offset {0:n}".format(pos))

        with open(filename, mode='rb') as f:
            while pos < end:
                f.seek(pos)
                size = min(end - pos + 1, 5 * 1024 * 1024)
                chunk = f.read(size)
                args = {
                    "FileMD5": fileHash,
                    "DataOffset": pos,
                    "DataSize": len(chunk),
                    "DataMD5": md5(chunk).hexdigest()}
                response = s.post(baseUrl, params=args, files={
                                  'Data': (None, chunk)}, timeout=180)
                json = response.json()
                if 'error_status' in json:
                    logging.error(
                        "Unexpected error during “{0}” upload".format(filename))
                    logging.error(str(json))
                    return False
                response.raise_for_status()
                if 'FileUploaded' in json:
                    logging.info(
                        "Proof file “{0}” successfully uploaded".format(filename))
                    return True
                if 'need' not in json:
                    logging.error(
                        "For proof “{0}”, no entries in need list:".format(filename))
                    logging.error(str(json))
                    return False
                start, end = next((int(a), b) for a, b in json['need'].items())
                if start <= pos:
                    logging.error(
                        "For proof “{0}”, sending data did not advance need list:".format(filename))
                    logging.error(str(json))
                    return False
                pos = start
                if pos > end or end >= fileSize:
                    logging.error(
                        "For proof “{0}”, need list entry bad:".format(filename))
                    logging.error(str(json))
                    return False


def upload_proofs(dir):
    """Uploads the proof file in the given directory to the server."""
    if config.has_option("PrimeNet", "ProofUploads") and not config.getboolean(
            "PrimeNet", "ProofUploads"):
        return
    proof = os.path.join(dir, 'proof')
    if not os.path.isdir(proof):
        logging.debug("Proof directory “{0}” does not exist".format(proof))
        return
    entries = os.listdir(proof)
    if not entries:
        logging.debug("No proof files to upload.")
        return
    if options.ProofArchiveDir:
        archive = os.path.join(dir, options.ProofArchiveDir)
        if not os.path.isdir(archive):
            os.makedirs(archive)
    for entry in entries:
        if entry.endswith(".proof"):
            filename = os.path.join(proof, entry)
            if upload_proof(filename):
                if options.ProofArchiveDir:
                    shutil.move(filename, os.path.join(archive, entry))
                else:
                    os.remove(filename)


def aupload_proofs(dirs):
    """Uploads any proof files found in the given directory."""
    for dir in dirs:
        upload_proofs(dir)


def digits(n):
    """Returns the number of digits in the decimal representation of n."""
    return int(n * Decimal(2).log10() + 1)


def output_status(dirs):
    logging.info(
        "Below is a report on the work you have queued and any expected completion dates.")
    ll_and_prp_cnt = 0
    prob = 0.0
    for i, dir in enumerate(dirs):
        if options.status and options.WorkerThreads > 1:
            logging.info("[Worker #{0:n}]".format(i + 1))
        workfile = os.path.join(dir, options.workfile)
        tasks = readonly_list_file(workfile)
        if not tasks:
            logging.info("No work queued up.")
            continue
        assignments = OrderedDict((assignment.uid, assignment) for assignment in (
            parse_assignment(dir, task) for task in tasks) if assignment and assignment.uid).values()
        msec_per_iter = None
        if config.has_option("PrimeNet", "msec_per_iter"):
            msec_per_iter = float(config.get("PrimeNet", "msec_per_iter"))
        cur_time_left = 0
        mersennes = True
        now = datetime.now()
        for assignment in assignments:
            iteration, _, _, bits, s2 = get_progress_assignment(
                dir, assignment)
            if not assignment:
                continue
            _, time_left = compute_progress(
                assignment, iteration, msec_per_iter, bits, s2)
            bits = int(assignment.sieve_depth)
            if bits < 32:
                bits = 32
            all_and_prp_cnt = False
            aprob = 0.0
            if assignment.work_type == primenet_api.WORK_TYPE_FIRST_LL:
                work_type_str = "Lucas-Lehmer test"
                all_and_prp_cnt = True
                aprob += (bits - 1) * 1.733 * (1.04 if assignment.pminus1ed else 1.0) / (
                    log2(assignment.k) + log2(assignment.b) * assignment.n)
            elif assignment.work_type == primenet_api.WORK_TYPE_DBLCHK:
                work_type_str = "Double-check"
                all_and_prp_cnt = True
                aprob += (bits - 1) * 1.733 * ERROR_RATE * (1.04 if assignment.pminus1ed else 1.0) / (
                    log2(assignment.k) + log2(assignment.b) * assignment.n)
            elif assignment.work_type == primenet_api.WORK_TYPE_PRP:
                all_and_prp_cnt = True
                if not assignment.prp_dblchk:
                    work_type_str = "PRP"
                    aprob += (bits - 1) * 1.733 * (1.04 if assignment.pminus1ed else 1.0) / (
                        log2(assignment.k) + log2(assignment.b) * assignment.n)
                else:
                    work_type_str = "PRPDC"
                    aprob += (bits - 1) * 1.733 * PRP_ERROR_RATE * (1.04 if assignment.pminus1ed else 1.0) / (
                        log2(assignment.k) + log2(assignment.b) * assignment.n)
            elif assignment.work_type == primenet_api.WORK_TYPE_PMINUS1:
                work_type_str = "P-1 B1={0:.0f}".format(assignment.B1)
            elif assignment.work_type == primenet_api.WORK_TYPE_PFACTOR:
                work_type_str = "P-1"
            elif assignment.work_type == primenet_api.WORK_TYPE_CERT:
                work_type_str = "Certify"
            prob += aprob
            if assignment.k != 1.0 or assignment.b != 2 or assignment.c != -1:
                amersennes = mersennes = False
            else:
                amersennes = True
            if time_left is None:
                logging.info("{0}, {1}, Finish cannot be estimated".format(
                    assignment.n, work_type_str))
            else:
                cur_time_left += time_left
                time_left = timedelta(seconds=cur_time_left)
                logging.info("{0}, {1}, {2} ({3})".format(
                    assignment.n, work_type_str, str(time_left), (now + time_left).strftime('%c')))
            if all_and_prp_cnt:
                ll_and_prp_cnt += 1
                logging.info("The chance that the exponent ({0}) you are testing will yield a {1}prime is about 1 in {2:n} ({3:%}).".format(
                    assignment.n, "Mersenne " if amersennes else "", int(1.0 / aprob), aprob))
            # print("Calculating the number of digits for {0}…".format(assignment.n))
            # num = str(assignment.k * assignment.b**assignment.n + assignment.c)
            # print("{0:n} has {1:n} decimal digits: {2}…{3}".format(assignment.n, len(num), num[:10], num[-10:]))
            if assignment.k == 1.0 and assignment.b == 2 and assignment.c == -1:
                logging.info("The exponent {0:n} has approximately {1:n} decimal digits (using formula p * log10(2) + 1)".format(
                    assignment.n, digits(assignment.n)))
    if ll_and_prp_cnt > 1:
        logging.info("The chance that one of the {0:n} exponents you are testing will yield a {1}prime is about 1 in {2:n} ({3:%}).".format(
            ll_and_prp_cnt, "Mersenne " if mersennes else "", int(1.0 / prob), prob))


def get_assignment(cpu, retry_count=0):
    """Get an assignment from the server."""
    if retry_count >= 5:
        logging.info("Retry count exceeded.")
        return
    guid = get_guid(config)
    args = primenet_v5_bargs.copy()
    args["t"] = "ga"			# transaction type
    args["g"] = guid
    args["c"] = cpu
    args["a"] = ""
    if options.GetMinExponent:
        args["min"] = options.GetMinExponent
    if options.GetMaxExponent:
        args["max"] = options.GetMaxExponent
    logging.debug("Fetching using v5 API")
    supported = frozenset([primenet_api.WORK_TYPE_FIRST_LL, primenet_api.WORK_TYPE_DBLCHK,
                          primenet_api.WORK_TYPE_PRP] + ([primenet_api.WORK_TYPE_PFACTOR] if not options.cudalucas else []))
    retry = False
    logging.info("Getting assignment from server")
    r = send_request(guid, args)
    if r is None:
        logging.debug("ERROR while requesting an assignment on mersenne.org")
        retry = True
    else:
        rc = int(r["pnErrorResult"])
        if rc == primenet_api.ERROR_OK:
            pass
        else:
            logging.debug(
                "ERROR while requesting an assignment on mersenne.org")
            if rc == primenet_api.ERROR_UNREGISTERED_CPU:
                logging.debug(
                    "UNREGISTERED CPU ERROR: pick a new GUID and register again")
                register_instance(None)
                retry = True
            elif rc == primenet_api.ERROR_STALE_CPU_INFO:
                logging.debug("STALE CPU INFO ERROR: re-send computer update")
                register_instance(guid)
                retry = True
            elif rc == primenet_api.ERROR_CPU_CONFIGURATION_MISMATCH:
                logging.debug(
                    "CPU CONFIGURATION MISMATCH: re-send computer update")
                register_instance(guid)
                retry = True
            if not retry:
                return
    if retry:
        return get_assignment(cpu, retry_count + 1)
    w = int(r['w'])
    if int(r['n']) < 15000000 and w in [primenet_api.WORK_TYPE_FACTOR, primenet_api.WORK_TYPE_PFACTOR,
                                        primenet_api.WORK_TYPE_FIRST_LL, primenet_api.WORK_TYPE_DBLCHK]:
        logging.error("Server sent bad exponent: " + r['n'] + ".")
        return
    if w not in supported:
        logging.error("Returned assignment from server is not a supported worktype {0} for {1}.".format(
            w, PROGRAMS[idx]["name"]))
        # TODO: Unreserve assignment
        # assignment_unreserve()
        return
    if w == primenet_api.WORK_TYPE_FIRST_LL:
        work_type_str = "LL"
        test = "Test"
        temp = [r[i] for i in ['k', 'n', 'sf', 'p1']]
        if options.gpuowl:  # GpuOwl
            logging.warning(
                "First time LL tests are not supported with the latest versions of GpuOwl")
    elif w == primenet_api.WORK_TYPE_DBLCHK:
        work_type_str = "Double check"
        test = "DoubleCheck"
        temp = [r[i] for i in ['k', 'n', 'sf', 'p1']]
        if options.gpuowl:  # GpuOwl
            logging.warning(
                "Double check LL tests are not supported with the latest versions of GpuOwl")
    elif w == primenet_api.WORK_TYPE_PRP:
        work_type_str = "PRPDC" if 'dc' in r else "PRP"
        test = "PRP" + ("DC" if 'dc' in r else "")
        temp = [r[i] for i in ['k', 'A', 'b', 'n', 'c']]
        if 'sf' in r or 'saved' in r:
            temp += [r[i] for i in ['sf', 'saved']]
            if 'base' in r or 'rt' in r:
                # Mlucas
                if not (options.cudalucas or options.gpuowl) and (
                        int(r['base']) != 3 or int(r['rt']) not in [1, 5]):
                    logging.error(
                        "PRP base is not 3 or residue type is not 1 or 5")
                    # TODO: Unreserve assignment
                    # assignment_unreserve()
                temp += [r[i] for i in ['base', 'rt']]
        if 'kf' in r:
            temp += ['"' + r['kf'] + '"']
    elif w == primenet_api.WORK_TYPE_PFACTOR:
        work_type_str = "P-1"
        test = "Pfactor"
        temp = [r[i] for i in ['k', 'A', 'b', 'n', 'c', 'sf', 'saved']]
    elif w == primenet_api.WORK_TYPE_CERT:
        work_type_str = "CERT"
        test = "Cert"
        temp = [r[i] for i in ['k', 'A', 'b', 'n', 'c', 'ns']]
    else:
        logging.error("Received unknown worktype: {0}.".format(w))
        return
    test += "=" + ",".join(temp)
    logging.info("Got assignment {0}: {1} {2}".format(
        r['k'], work_type_str, r['n']))
    return test


def primenet_fetch(cpu, num_to_get):
    """Get a number of assignments from the PrimeNet server."""
    if options.password and not primenet_login:
        return []
    # As of early 2018, here is the full list of assignment-type codes supported by the Primenet server; Mlucas
    # v20 (and thus this script) supports only the subset of these indicated by an asterisk in the left column.
    # Supported assignment types may be specified via either their PrimeNet number code or the listed Mnemonic:
    #			Worktype:
    # Code		Mnemonic			Description
    # ----	-----------------	-----------------------
    #    0						Whatever makes the most sense
    #    1						Trial factoring to low limits
    #    2						Trial factoring
    # *  4	Pfactor				P-1 factoring
    #    5						ECM for first factor on Mersenne numbers
    #    6						ECM on Fermat numbers
    #    8						ECM on mersenne cofactors
    # *100	SmallestAvail		Smallest available first-time tests
    # *101	DoubleCheck			Double-checking
    # *102	WorldRecord			World record primality tests
    # *104	100Mdigit			100M digit number to LL test (not recommended)
    # *150	SmallestAvailPRP	First time PRP tests (Gerbicz)
    # *151	DoubleCheckPRP		Doublecheck PRP tests (Gerbicz)
    # *152	WorldRecordPRP		World record sized numbers to PRP test (Gerbicz)
    # *153	100MdigitPRP		100M digit number to PRP test (Gerbicz)
    #  160						PRP on Mersenne cofactors
    #  161						PRP double-checks on Mersenne cofactors

    try:
        # Get assignment (Loarer's way)
        if options.password:
            assignment = OrderedDict((
                ("cores", options.WorkerThreads),
                ("num_to_get", num_to_get),
                ("pref", worktype),
                ("exp_lo", options.GetMinExponent if options.GetMinExponent else ""),
                ("exp_hi", options.GetMaxExponent if options.GetMaxExponent else ""),
                ("B1", "Get Assignments")
            ))
            logging.debug("Fetching using manual assignments")
            r = s.post(
                primenet_baseurl +
                "manual_assignment/?",
                data=assignment)
            r.raise_for_status()
            res = r.text
            BEGIN_MARK = "<!--BEGIN_ASSIGNMENTS_BLOCK-->"
            begin = res.find(BEGIN_MARK)
            if begin >= 0:
                begin += len(BEGIN_MARK)
                end = res.find("<!--END_ASSIGNMENTS_BLOCK-->", begin)
                if end >= 0:
                    return res[begin:end].splitlines()
            return greplike(workpattern, (line.decode(
                'utf-8') for line in r.iter_lines()))

        # Get assignment using v5 API
        else:
            tests = []
            for _ in range(num_to_get):
                test = get_assignment(cpu)
                if test:
                    tests.append(test)
                else:
                    break

            return tests
    except ConnectionError:
        logging.exception("URL open error at primenet_fetch")
        return []


def get_assignments(dir, cpu, progress):
    """Get new assignments from the PrimeNet server."""
    if config.has_option("PrimeNet", "NoMoreWork") and config.getboolean(
            "PrimeNet", "NoMoreWork"):
        return 0
    workfile = os.path.join(dir, options.workfile)
    tasks = readonly_list_file(workfile)
    assignments = OrderedDict((assignment.uid, assignment) for assignment in (
        parse_assignment(dir, task) for task in tasks) if assignment and assignment.uid).values()
    (percent, time_left) = None, None
    if progress is not None and isinstance(
            progress, tuple) and len(progress) == 2:
        (percent, time_left) = progress  # unpack update_progress output
    num_cache = options.num_cache + 1
    if options.password:
        num_cache += 1
    if time_left is not None:
        time_left = timedelta(seconds=time_left)
        days_work = timedelta(days=options.DaysOfWork)
        if time_left <= days_work:
            num_cache += 1
            logging.debug("Time left is {0} and smaller than DaysOfWork ({1}), so num_cache is increased by one to {2:n}".format(
                str(time_left), str(days_work), num_cache))
    length = len(assignments)
    num_to_get = num_cache - length

    if num_to_get <= 0:
        logging.debug("{0:n} ≥ {1:n} entries already in “{2}”, not getting new work".format(
            length, num_cache, workfile))
        return 0
    logging.debug("Found {0:n} < {1:n} entries in “{2}”, getting {3:n} new assignment{4}".format(
        length, num_cache, workfile, num_to_get, "s" if num_to_get > 1 else ""))

    new_tasks = primenet_fetch(cpu, num_to_get)
    num_fetched = len(new_tasks)
    if num_fetched > 0:
        logging.debug("Fetched {0:n} assignment{1}:".format(
            num_fetched, "s" if num_fetched > 1 else ""))
        for i, new_task in enumerate(new_tasks):
            assignment = parse_assignment(dir, new_task)
            if not assignment:
                logging.error("Invalid assignment '{0}'".format(new_task))
            else:
                if assignment.work_type == primenet_api.WORK_TYPE_PRP and not assignment.prp_dblchk and int(
                        options.WorkPreference) in option_dict:
                    logging.debug(
                        "Original assignment: '{0}'".format(new_task))
                    new_tasks[i] = "Test=" + ",".join(
                        [str(j) for j in [assignment.uid, assignment.n, int(assignment.sieve_depth), int(not assignment.tests_saved)]])
                logging.debug("New assignment: '{0}'".format(new_tasks[i]))
    write_list_file(workfile, new_tasks, "a")
    output_status([dir])
    if num_fetched < num_to_get:
        logging.error("Failed to get requested number of new assignments, {0:n} requested, {1:n} successfully retrieved".format(
            num_to_get, num_fetched))
    return num_fetched


resultpattern = re.compile(r"Program: E|Mlucas|CUDALucas v|gpuowl")


def mersenne_find(line, complete=True):
    """Check for result in a line of text."""
    # Pre-v19 old-style HRF-formatted result used "Program:..."; starting
    # w/v19 JSON-formatted result uses "program",
    return resultpattern.search(line)


def parse_stat_file(dir, p):
    """Parse the stat file for the progress of the assignment."""
    # Mlucas
    statfile = os.path.join(dir, 'p' + str(p) + '.stat')
    if not os.path.exists(statfile):
        logging.debug("stat file “{0}” does not exist".format(statfile))
        return 0, None, None, 0, 0

    w = readonly_list_file(statfile)  # appended line by line, no lock needed
    found = 0
    regex = re.compile(
        r"(Iter#|S1|S2)(?: bit| at q)? = ([0-9]+) \[ ?([0-9]+\.[0-9]+)% complete\] .*\[ *([0-9]+\.[0-9]+) (m?sec)/iter\]")
    fft_regex = re.compile(r'FFT length [0-9]{3,}K = ([0-9]{6,})')
    s2_regex = re.compile(r'Stage 2 q0 = ([0-9]+)')
    list_msec_per_iter = []
    fftlen = None
    s2 = 0
    bits = 0
    # get the 5 most recent Iter line
    for line in reversed(w):
        res = regex.search(line)
        fft_res = fft_regex.search(line)
        s2_res = s2_regex.search(line)
        if res and found < 5:
            found += 1
            # keep the last iteration to compute the percent of progress
            if found == 1:
                iteration = int(res.group(2))
                percent = float(res.group(3))
                if res.group(1) == "S1":
                    bits = int(iteration / (percent / 100))
                elif res.group(1) == "S2":
                    s2 = iteration
            if (not bits or res.group(1) == "S1") and (
                    not s2 or res.group(1) == "S2"):
                msec_per_iter = float(res.group(4))
                if res.group(5) == "sec":
                    msec_per_iter *= 1000
                list_msec_per_iter.append(msec_per_iter)
        elif s2 and s2_res:
            s2 = int(((iteration - int(s2_res.group(1))) / (percent / 100)) / 20)
            iteration = int(s2 * (percent / 100))
        elif fft_res and not fftlen:
            fftlen = int(fft_res.group(1))
        if found == 5 and fftlen:
            break
    if found == 0:
        # iteration is 0, but don't know the estimated speed yet
        return 0, None, fftlen, bits, s2
    # take the median of the last grepped lines
    msec_per_iter = median_low(list_msec_per_iter)
    return iteration, msec_per_iter, fftlen, bits, s2


def parse_v5_resp(r):
    """Parse the response from the server into a dict."""
    ans = {}
    for line in r.splitlines():
        if line == "==END==":
            break
        option, _, value = line.partition("=")
        ans[option] = value
    return ans


__v5salt_ = 0


def secure_v5_url(guid, args):
    k = bytearray(md5(guid.encode("utf-8")).digest())

    for i in range(16):
        k[i] ^= k[(k[i] ^ (_V5_UNIQUE_TRUSTED_CLIENT_CONSTANT_ & 0xFF)) %
                  16] ^ (_V5_UNIQUE_TRUSTED_CLIENT_CONSTANT_ // 256)

    p_v5key = md5(k).hexdigest().upper()

    global __v5salt_
    if not __v5salt_:
        random.seed()

    __v5salt_ = random.randint(0, sys.maxsize) & 0xFFFF

    args["ss"] = __v5salt_
    URL = urlencode(args) + '&' + p_v5key

    ahash = md5(URL.encode("utf-8")).hexdigest().upper()

    args["sh"] = ahash


def send_request(guid, args):
    """Send a request to the PrimeNet server."""
    try:
        if idx:
            args["ss"] = 19191919
            args["sh"] = "ABCDABCDABCDABCDABCDABCDABCDABCD"
        else:
            secure_v5_url(guid, args)
        r = s.get(primenet_v5_burl, params=args, timeout=180)
        r.raise_for_status()
        result = parse_v5_resp(r.text)
        rc = int(result["pnErrorResult"])
        if rc:
            if rc in errors:
                resmsg = errors[rc]
            else:
                resmsg = "Unknown error code"
            logging.error("PrimeNet error {0}: {1}".format(rc, resmsg))
            logging.error(result["pnErrorDetail"])
        else:
            if result["pnErrorDetail"] != "SUCCESS":
                logging.info("PrimeNet success code with additional info:")
                logging.info(result["pnErrorDetail"])

    except HTTPError as e:
        logging.exception("ERROR receiving answer to request: " + r.url)
        return None
    except ConnectionError as e:
        logging.exception("ERROR connecting to server for request: ")
        return None
    return result


def create_new_guid():
    """Create a new GUID."""
    global guid
    guid = uuid.uuid4().hex
    return guid


def register_instance(guid):
    """Register the computer with the PrimeNet server."""
    # register the instance to server, guid is the instance identifier
    if config.has_option("PrimeNet", "HardwareGUID"):
        hardware_id = config.get("PrimeNet", "HardwareGUID")
    else:
        hardware_id = md5((options.cpu_model + str(uuid.getnode())
                           ).encode("utf-8")).hexdigest()  # similar as MPrime
        config.set("PrimeNet", "HardwareGUID", hardware_id)
    args = primenet_v5_bargs.copy()
    args["t"] = "uc"					# update compute command
    if guid is None:
        guid = create_new_guid()
    args["g"] = guid
    args["hg"] = hardware_id			# 32 hex char (128 bits)
    args["wg"] = ""						# only filled on Windows by MPrime
    args["a"] = "{0},{1},v{2}{3}".format(platform.system() + ('64' if platform.machine().endswith('64') else ''), PROGRAMS[idx]
                                         ["name"], PROGRAMS[idx]["version"], ",build " + str(PROGRAMS[idx]["build"]) if "build" in PROGRAMS[idx] else '')
    if config.has_option("PrimeNet", "sw_version"):
        args["a"] = config.get("PrimeNet", "sw_version")
    args["c"] = options.cpu_model[:64]  # CPU model (len between 8 and 64)
    args["f"] = options.features[:64]  # CPU option (like asimd, max len 64)
    args["L1"] = options.L1				# L1 cache size in KBytes
    args["L2"] = options.L2				# L2 cache size in KBytes
    # if smaller or equal to 256,
    # server refuses to gives LL assignment
    args["np"] = options.NumCores				# number of cores
    args["hp"] = options.CpuNumHyperthreads				# number of hyperthreading cores
    args["m"] = options.memory			# number of megabytes of physical memory
    args["s"] = options.CpuSpeed		# CPU frequency
    args["h"] = options.CPUHours
    args["r"] = 0						# pretend to run at 100%
    if config.has_option("PrimeNet", "RollingAverage"):
        args["r"] = config.get("PrimeNet", "RollingAverage")
    if options.L3:
        args["L3"] = options.L3
    if options.username:
        args["u"] = options.username		#
    if options.ComputerID:
        args["cn"] = options.ComputerID[:20]  # truncate to 20 char max
    logging.info("Updating computer information on the server")
    result = send_request(guid, args)
    if result is None:
        parser.error("Error while registering on mersenne.org")
    else:
        rc = int(result["pnErrorResult"])
        if rc == primenet_api.ERROR_OK:
            pass
        else:
            parser.error("Error while registering on mersenne.org")
    # Save program options in case they are changed by the PrimeNet server.
    config.set("PrimeNet", "username", result["u"])
    config.set("PrimeNet", "ComputerID", result["cn"])
    config.set("PrimeNet", "name", result["un"])
    options_counter = int(result["od"])
    config_write(config, guid=guid)
    # if options_counter == 1:
    # program_options(guid, False)
    program_options(guid, True)
    if options_counter > int(config.get("PrimeNet", "SrvrP00")):
        program_options(guid, False)
    merge_config_and_options(config, options)
    config_write(config)
    logging.info("GUID {guid} correctly registered with the following features:".format(
        guid=guid))
    logging.info("Username: {0}".format(options.username))
    logging.info("Computer name: {0}".format(options.ComputerID))
    logging.info("CPU model: {0}".format(options.cpu_model))
    logging.info("CPU features: {0}".format(options.features))
    logging.info("CPU L1 Cache size: {0:n} KIB".format(options.L1))
    logging.info("CPU L2 Cache size: {0:n} KiB".format(options.L2))
    logging.info("CPU cores: {0:n}".format(options.NumCores))
    logging.info("CPU threads per core: {0:n}".format(
        options.CpuNumHyperthreads))
    logging.info("CPU frequency/speed: {0:n} MHz".format(options.CpuSpeed))
    logging.info("Total RAM: {0:n} MiB".format(options.memory))
    logging.info("To change these values, please rerun the script with different options or edit the “{0}” file".format(
        options.localfile))
    logging.info("You can see the result in this page:")
    logging.info(
        "https://www.mersenne.org/editcpu/?g={guid}".format(guid=guid))
    return


def config_read():
    """Reads the configuration file."""
    config = ConfigParser(dict_type=OrderedDict)
    config.optionxform = lambda option: option
    localfile = os.path.join(workdir, options.localfile)
    try:
        config.read([localfile])
    except ConfigParserError as e:
        logging.exception("ERROR reading “{0}” file:".format(localfile))
    if not config.has_section("PrimeNet"):
        # Create the section to avoid having to test for it later
        config.add_section("PrimeNet")
    return config


def get_guid(config):
    """Returns the GUID from the config file, or None if it is not present."""
    try:
        return config.get("PrimeNet", "ComputerGUID")
    except ConfigParserError:
        return None


def config_write(config, guid=None):
    """Write the given configuration object to the local config file."""
    # generate a new local.ini file
    if guid is not None:  # update the guid if necessary
        config.set("PrimeNet", "ComputerGUID", guid)
    localfile = os.path.join(workdir, options.localfile)
    with open(localfile, "w") as configfile:
        config.write(configfile)


def merge_config_and_options(config, options):
    """Updates the options object with the values found in the local configuration file."""
    # getattr and setattr allow access to the options.xxxx values by name
    # which allow to copy all of them programmatically instead of having
    # one line per attribute. Only the attr_to_copy list need to be updated
    # when adding an option you want to copy from argument options to
    # local.ini config.
    attr_to_copy = ["workfile", "resultsfile", "ProofArchiveDir", "username", "password", "WorkPreference", "GetMinExponent", "GetMaxExponent", "gpuowl", "cudalucas", "WorkerThreads",
                    "num_cache", "DaysOfWork", "no_report_100m", "ComputerID", "cpu_model", "features", "CpuSpeed", "memory", "L1", "L2", "L3", "NumCores", "CpuNumHyperthreads", "CPUHours"]
    updated = False
    for attr in attr_to_copy:
        # if "attr" has its default value in options, copy it from config
        attr_val = getattr(options, attr)
        if not hasattr(opts_no_defaults, attr) \
                and config.has_option("PrimeNet", attr):
            # If no option is given and the option exists in local.ini, take it
            # from local.ini
            if isinstance(attr_val, bool):
                new_val = config.getboolean("PrimeNet", attr)
            else:
                new_val = config.get("PrimeNet", attr)
            # config file values are always str()
            # they need to be converted to the expected type from options
            if attr_val is not None:
                new_val = type(attr_val)(new_val)
            setattr(options, attr, new_val)
        elif attr_val is not None and (not config.has_option("PrimeNet", attr)
                                       or config.get("PrimeNet", attr) != str(attr_val)):
            # If an option is given (even default value) and it is not already
            # identical in local.ini, update local.ini
            logging.debug("update “{0}” with {1}={2}".format(
                options.localfile, attr, attr_val))
            config.set("PrimeNet", attr, str(attr_val))
            updated = True

    return updated


def update_progress(cpu, assignment, iteration, msec_per_iter,
                    fftlen, bits, s2, now, cur_time_left):
    """Update the progress of a given assignment."""
    if not assignment:
        return
    percent, time_left = compute_progress(
        assignment, iteration, msec_per_iter, bits, s2)
    logging.debug("p:{0} is {1:.4n}% done ({2:n} / {3:n})".format(assignment.n, percent, iteration,
                  s2 if s2 else bits if bits else assignment.n if assignment.work_type == primenet_api.WORK_TYPE_PRP else assignment.n - 2))
    if time_left is None:
        logging.debug("Finish cannot be estimated")
    else:
        cur_time_left += time_left
        delta = timedelta(seconds=cur_time_left)
        logging.debug(
            "Finish estimated in {0} (used {1:.4n} msec/iter estimation)".format(str(delta), msec_per_iter))
        send_progress(cpu, assignment, percent, cur_time_left,
                      now, delta, fftlen, bits, s2)
    return percent, cur_time_left


def update_progress_all(dir, cpu):
    """Update the progress of all the assignments in the workfile."""
    workfile = os.path.join(dir, options.workfile)
    tasks = readonly_list_file(workfile)
    if not tasks:
        return  # don't update if no worktodo
    assignments = iter(OrderedDict((assignment.uid, assignment) for assignment in (
        parse_assignment(dir, task) for task in tasks) if assignment and assignment.uid).values())
    # Treat the first assignment. Only this one is used to save the msec_per_iter
    # The idea is that the first assignment is having a .stat file with correct values
    # Most of the time, a later assignment would not have a .stat file to obtain information,
    # but if it has, it may come from an other computer if the user moved the files, and so
    # it doesn't have relevant values for speed estimation.
    # Using msec_per_iter from one p to another is a good estimation if both p are close enough
    # if there is big gap, it will be other or under estimated.
    # Any idea for a better estimation of assignment duration when only p and
    # type (LL or PRP) is known ?
    now = datetime.now()
    assignment = next(assignments)
    iteration, msec_per_iter, fftlen, bits, s2 = get_progress_assignment(
        dir, assignment)
    if msec_per_iter is not None:
        config.set("PrimeNet", "msec_per_iter",
                   "{0:.4f}".format(msec_per_iter))
    elif config.has_option("PrimeNet", "msec_per_iter"):
        # If not speed available, get it from the local.ini file
        msec_per_iter = float(config.get("PrimeNet", "msec_per_iter"))
    # Do the other assignment accumulating the time_lefts
    cur_time_left = None if msec_per_iter is None else 0
    percent, cur_time_left = update_progress(
        cpu, assignment, iteration, msec_per_iter, fftlen, bits, s2, now, cur_time_left)
    for assignment in assignments:
        iteration, _, fftlen, bits, s2 = get_progress_assignment(
            dir, assignment)
        percent, cur_time_left = update_progress(
            cpu, assignment, iteration, msec_per_iter, fftlen, bits, s2, now, cur_time_left)
    config.set("PrimeNet", "LastEndDatesSent", str(int(time.time())))
    config_write(config)
    return percent, cur_time_left


def get_progress_assignment(dir, assignment):
    """Get the progress of an assignment."""
    if not assignment:
        return
    # P-1 Stage 1 bits
    bits = 0
    # P-1 Stage 2 location/buffers/blocks
    s2 = 0
    if options.gpuowl:  # GpuOwl
        iteration, msec_per_iter, fftlen, bits, s2 = parse_stat_file_gpu(
            dir, assignment.n)
    elif options.cudalucas:  # CUDALucas
        iteration, msec_per_iter, fftlen = parse_stat_file_cuda(
            dir, assignment.n)
    else:  # Mlucas
        iteration, msec_per_iter, fftlen, bits, s2 = parse_stat_file(
            dir, assignment.n)
    return iteration, msec_per_iter, fftlen, bits, s2


def parse_assignment(dir, task):
    """Parse a line from a workfile into an Assignment namedtuple."""
    # Ex: Test=197ED240A7A41EC575CB408F32DDA661,57600769,74
    found = workpattern.search(task)
    if not found:
        logging.error("Unable to extract valid PrimeNet assignment ID from entry in “{0}” file: {1}".format(
            os.path.join(dir, options.workfile), task))
        return None
    # logging.debug(task)
    work_type = found.group(1)  # e.g., "Test"
    assignment_uid = found.group(2)  # e.g., "197ED240A7A41EC575CB408F32DDA661"
    # k*b^n+c
    k = 1.0
    b = 2
    c = -1
    sieve_depth = 99.0
    pminus1ed = 1
    tests_saved = 0.0
    B1 = 0.0
    B2 = 0.0
    prp_dblchk = False
    # e.g., "57600769", "197ED240A7A41EC575CB408F32DDA661"
    # logging.debug("type = {0}, assignment_id = {1}".format(work_type, assignment_uid))
    found = list(csv.reader([task.split("=", 1)[1]]))[0]
    if not assignment_uid:
        found.insert(0, "")
    length = len(found)
    idx = 1 if work_type == "Test" or work_type == "DoubleCheck" else 3
    if length <= idx:
        logging.error("Unable to extract valid exponent substring from entry in “{0}” file: {1}".format(
            os.path.join(dir, options.workfile), task))
        return None
    # Extract the subfield containing the exponent, whose position depends on
    # the assignment type:
    if work_type == "Test" or work_type == "DoubleCheck":
        work_type = primenet_api.WORK_TYPE_FIRST_LL if work_type == "Test" else primenet_api.WORK_TYPE_DBLCHK
        n = int(found[1])
        sieve_depth = float(found[2])
        pminus1ed = int(found[3])
    elif work_type == "PRP" or work_type == "PRPDC":
        if work_type == "PRPDC":
            prp_dblchk = True
        work_type = primenet_api.WORK_TYPE_PRP
        k = float(found[1])
        b = int(found[2])
        n = int(found[3])
        c = int(found[4])
        # idx = 5
        if length >= 6:
            sieve_depth = float(found[5])
            tests_saved = float(found[6])
            # idx = 7
            # if length >= 8:
            # prp_base = int(found[7])
            # prp_residue_type = int(found[8])
            # idx = 9
        # if length >= idx:
            # known_factors = found[idx]
    elif work_type == "PFactor" or work_type == "Pfactor":
        work_type = primenet_api.WORK_TYPE_PFACTOR
        k = float(found[1])
        b = int(found[2])
        n = int(found[3])
        c = int(found[4])
        sieve_depth = float(found[5])
        tests_saved = float(found[6])
    elif work_type == "PMinus1" or work_type == "Pminus1":
        work_type = primenet_api.WORK_TYPE_PMINUS1
        k = float(found[1])
        b = int(found[2])
        n = int(found[3])
        c = int(found[4])
        B1 = float(found[5])
        B2 = float(found[6])
        if length >= 8:
            sieve_depth = float(found[7])
            # if length >= 9:
            # B2_start = float(found[8])
            # if length >= 10:
            # known_factors = found[9]
    elif work_type == "Cert":
        work_type = primenet_api.WORK_TYPE_CERT
        k = float(found[1])
        b = int(found[2])
        n = int(found[3])
        c = int(found[4])
        # cert_squarings = int(found[5])
    if k == 1.0 and b == 2 and not is_prime(
            n) and c == -1 and work_type != primenet_api.WORK_TYPE_PMINUS1:
        logging.error("“{0}” file contained composite exponent: {1}.".format(
            os.path.join(dir, options.workfile), n))
        return None
    if work_type == primenet_api.WORK_TYPE_PMINUS1 and B1 < 50000:
        logging.error("“{0}” file has P-1 with B1 < 50000 (exponent: {1}).".format(
            os.path.join(dir, options.workfile), n))
        return None
    # return Assignment(work_type, assignment_uid, k, b, n, c, sieve_depth,
    # pminus1ed, B1, B2, tests_saved, prp_base, prp_residue_type,
    # known_factors, prp_dblchk, cert_squarings)
    return Assignment(work_type, assignment_uid, k, b, n, c,
                      sieve_depth, pminus1ed, B1, B2, tests_saved, prp_dblchk)


def parse_stat_file_cuda(dir, p):
    """Parse the CUDALucas output file for the progress of the assignment."""
    # CUDALucas
    # appended line by line, no lock needed
    gpu = os.path.join(dir, options.cudalucas)
    if not os.path.exists(gpu):
        logging.debug("CUDALucas file “{0}” does not exist".format(gpu))
        return 0, None, None

    w = readonly_list_file(gpu)
    found = 0
    num_regex = re.compile(r'\bM([0-9]{7,})\b')
    iter_regex = re.compile(r'\b[0-9]{5,}\b')
    ms_per_regex = re.compile(r'\b[0-9]+\.[0-9]{1,5}\b')
    eta_regex = re.compile(
        r'\b(?:(?:([0-9]+):)?([0-9]{1,2}):)?([0-9]{1,2}):([0-9]{2})\b')
    fft_regex = re.compile(r'\b([0-9]{3,})K\b')
    list_msec_per_iter = []
    fftlen = None
    # get the 5 most recent Iter line
    for line in reversed(w):
        num_res = re.findall(num_regex, line)
        iter_res = re.findall(iter_regex, line)
        ms_res = re.findall(ms_per_regex, line)
        eta_res = re.findall(eta_regex, line)
        fft_res = re.findall(fft_regex, line)
        if num_res and iter_res and ms_res and eta_res and fft_res:
            if int(num_res[0]) != p:
                if found == 0:
                    logging.debug(
                        "Looking for the exponent {0}, but found {1}".format(p, num_res[0]))
                break
            found += 1
            # keep the last iteration to compute the percent of progress
            if found == 1:
                iteration = int(iter_res[0])
                eta = eta_res[1]
                time_left = int(eta[3]) + (int(eta[2]) * 60)
                if eta[1]:
                    time_left += int(eta[1]) * 60 * 60
                if eta[0]:
                    time_left += int(eta[0]) * 60 * 60 * 24
                avg_msec_per_iter = (time_left * 1000) / (p - iteration)
                fftlen = int(fft_res[0]) * 1024
            elif int(iter_res[0]) > iteration:
                break
            list_msec_per_iter.append(float(ms_res[1]))
            if found == 5:
                break
    if found == 0:
        return 0, None, fftlen  # iteration is 0, but don't know the estimated speed yet
    # take the median of the last grepped lines
    msec_per_iter = median_low(list_msec_per_iter)
    logging.debug("Current {0:.6n} msec/iter estimation, Average {1:.6n} msec/iter".format(
        msec_per_iter, avg_msec_per_iter))
    return iteration, avg_msec_per_iter, fftlen


def parse_stat_file_gpu(dir, p):
    """Parse the gpuowl log file for the progress of the assignment."""
    # GpuOwl
    # appended line by line, no lock needed
    gpuowl = os.path.join(dir, 'gpuowl.log')
    if not os.path.exists(gpuowl):
        logging.debug("Log file “{0}” does not exist".format(gpuowl))
        return 0, None, None, 0, 0

    w = readonly_list_file(gpuowl)
    found = 0
    regex = re.compile(r"([0-9]{7,}) (LL|P1|OK|EE)? +([0-9]{5,})")
    us_per_regex = re.compile(r'\b([0-9]+) us/it;?\b')
    fft_regex = re.compile(r'\b[0-9]{7,} FFT: ([0-9]+(?:\.[0-9]+)?[KM])\b')
    bits_regex = re.compile(
        r'\b[0-9]{7,} P1(?: B1=[0-9]+, B2=[0-9]+;|\([0-9]+(?:\.[0-9])?M?\)) ([0-9]+) bits;?\b')
    blocks_regex = re.compile(
        r'[0-9]{7,} P2\([0-9]+(?:\.[0-9])?M?,[0-9]+(?:\.[0-9])?M?\) ([0-9]+) blocks: ([0-9]+) - ([0-9]+);')
    p1_regex = re.compile(r'\| P1\([0-9]+(?:\.[0-9])?M?\)')
    p2_regex = re.compile(
        r"[0-9]{7,} P2(?: ([0-9]+)/([0-9]+)|\([0-9]+(?:\.[0-9])?M?,[0-9]+(?:\.[0-9])?M?\) OK @([0-9]+)):")
    list_usec_per_iter = []
    fftlen = None
    p1 = False
    p2 = False
    buffs = 0
    bits = 0
    # get the 5 most recent Iter line
    for line in reversed(w):
        res = regex.search(line)
        us_res = re.findall(us_per_regex, line)
        fft_res = re.findall(fft_regex, line)
        bits_res = re.findall(bits_regex, line)
        blocks_res = re.search(blocks_regex, line)
        p2_res = re.search(p2_regex, line)
        if res and int(res.group(1)) != p:
            if found == 0:
                logging.debug(
                    "Looking for the exponent {0}, but found {1}".format(p, res.group(1)))
            break
        if p2_res:
            found += 1
            if found == 1:
                if p2_res.group(3):
                    iteration = int(p2_res.group(3))
                    p2 = True
                else:
                    iteration = int(p2_res.group(1))
                    buffs = int(p2_res.group(2))
        elif res and us_res and found < 20:
            found += 1
            # keep the last iteration to compute the percent of progress
            if found == 1:
                iteration = int(res.group(3))
                p1 = res.group(2) == 'P1'
            elif int(res.group(3)) > iteration:
                break
            if not p1 and not (p2 or buffs):
                p1_res = re.findall(p1_regex, line)
                p1 = res.group(2) == 'OK' and bool(p1_res)
            if len(list_usec_per_iter) < 5:
                list_usec_per_iter.append(int(us_res[0]))
        elif p2 and blocks_res:
            if not buffs:
                buffs = int(blocks_res.group(1))
                iteration -= int(blocks_res.group(2))
        elif p1 and bits_res:
            if not bits:
                bits = int(bits_res[0])
                if iteration > bits:
                    iteration = bits
        elif fft_res and not fftlen:
            unit = fft_res[0][-1:]
            fftlen = int(float(
                fft_res[0][: -1]) * (1024 if unit == 'K' else 1024 * 1024 if unit == 'M' else 1))
        if (buffs or (found == 20 and not p2 and (not p1 or bits))) and fftlen:
            break
    if found == 0:
        # iteration is 0, but don't know the estimated speed yet
        return 0, None, fftlen, bits, buffs
    # take the median of the last grepped lines
    msec_per_iter = median_low(list_usec_per_iter) / \
        1000 if list_usec_per_iter else None
    return iteration, msec_per_iter, fftlen, bits, buffs


def compute_progress(assignment, iteration, msec_per_iter, bits, s2):
    """Computes the progress of a given assignment."""
    percent = 100 * iteration / (s2 if s2 else bits if bits else assignment.n if assignment.work_type ==
                                 primenet_api.WORK_TYPE_PRP else assignment.n - 2)
    if msec_per_iter is None:
        return percent, None
    if bits:
        time_left = msec_per_iter * (bits - iteration)
        # 1.5 suggested by EWM for Mlucas v20.0 and 1.13-1.275 for v20.1
        time_left += msec_per_iter * bits * 1.2
        if assignment.work_type in [primenet_api.WORK_TYPE_FIRST_LL,
                                    primenet_api.WORK_TYPE_DBLCHK, primenet_api.WORK_TYPE_PRP]:
            time_left += msec_per_iter * assignment.n
    elif s2:
        time_left = msec_per_iter * \
            (s2 - iteration) if not options.gpuowl else options.timeout
        if assignment.work_type in [primenet_api.WORK_TYPE_FIRST_LL,
                                    primenet_api.WORK_TYPE_DBLCHK, primenet_api.WORK_TYPE_PRP]:
            time_left += msec_per_iter * assignment.n
    else:
        time_left = msec_per_iter * ((assignment.n if assignment.work_type ==
                                     primenet_api.WORK_TYPE_PRP else assignment.n - 2) - iteration)
    time_left *= 24.0 / options.CPUHours
    return percent, time_left / 1000


def send_progress(cpu, assignment, percent, time_left, now,
                  delta, fftlen, s1, s2, retry_count=0):
    """Sends the expected completion date for a given assignment to the server."""
    guid = get_guid(config)
    if guid is None:
        logging.error("Cannot update, the registration is not done")
        return
    if not assignment.uid:
        return
    if retry_count >= 5:
        logging.info("Retry count exceeded.")
        return
    # Assignment Progress fields:
    # g= the machine's GUID (32 chars, assigned by Primenet on 1st-contact from a given machine, stored in 'guid=' entry of local.ini file of rundir)
    #
    args = primenet_v5_bargs.copy()
    args["t"] = "ap"  # update compute command
    args["g"] = guid
    # k= the assignment ID (32 chars, follows '=' in Primenet-generated workfile entries)
    args["k"] = assignment.uid
    # p= progress in %-done, 4-char format = xy.z
    args["p"] = "{0:.4f}".format(percent)
    # d= when the client is expected to check in again (in seconds ... )
    args["d"] = options.timeout if options.timeout else 24 * 60 * 60
    # e= the ETA of completion in seconds, if unknown, just put 1 week
    args["e"] = int(time_left) if time_left is not None else 7 * 24 * 60 * 60
    # c= the worker thread of the machine
    args["c"] = cpu
    # stage= LL in this case, although an LL test may be doing TF or P-1 work
    # first so it's possible to be something besides LL
    if percent > 0:
        if s1:
            args["stage"] = "S1"
        elif s2:
            args["stage"] = "S2"
        elif assignment.work_type == primenet_api.WORK_TYPE_FIRST_LL or assignment.work_type == primenet_api.WORK_TYPE_DBLCHK:
            args["stage"] = "LL"
        elif assignment.work_type == primenet_api.WORK_TYPE_PRP:
            args["stage"] = "PRP"
        elif assignment.work_type == primenet_api.WORK_TYPE_CERT:
            args["stage"] = "CERT"
    if fftlen:
        args["fftlen"] = fftlen
    retry = False
    logging.info("Sending expected completion date for {0}: {1} ({2})".format(
        assignment.n, str(delta), (now + delta).strftime('%c')))
    result = send_request(guid, args)
    if result is None:
        logging.debug(
            "ERROR while sending progress on mersenne.org: assignment_id={0}".format(assignment.uid))
        # Try again
        retry = True
    else:
        rc = int(result["pnErrorResult"])
        if rc == primenet_api.ERROR_OK:
            logging.debug("Update correctly sent to server")
        else:
            logging.debug(
                "ERROR while sending progress on mersenne.org: assignment_id={0}".format(assignment.uid))
            if rc == primenet_api.ERROR_STALE_CPU_INFO:
                logging.debug("STALE CPU INFO ERROR: re-send computer update")
                register_instance(guid)
                retry = True
            elif rc == primenet_api.ERROR_UNREGISTERED_CPU:
                logging.debug(
                    "UNREGISTERED CPU ERROR: pick a new GUID and register again")
                register_instance(None)
                retry = True
            elif rc == primenet_api.ERROR_INVALID_ASSIGNMENT_KEY:
                # TODO: Delete assignment from workfile
                pass
            elif rc == primenet_api.ERROR_WORK_NO_LONGER_NEEDED:
                # TODO: Delete assignment from workfile
                pass
            elif rc == primenet_api.ERROR_SERVER_BUSY:
                retry = True
    if retry:
        return send_progress(cpu, assignment, percent, time_left,
                             now, delta, fftlen, s1, s2, retry_count + 1)
    return


def get_cuda_ar_object(dir, sendline):
    # CUDALucas

    # sendline example: 'M( 108928711 )C, 0x810d83b6917d846c, offset = 106008371, n = 6272K, CUDALucas v2.06, AID: 02E4F2B14BB23E2E4B95FC138FC715A8'
    # sendline example: 'M( 108928711 )P, offset = 106008371, n = 6272K, CUDALucas v2.06, AID: 02E4F2B14BB23E2E4B95FC138FC715A8'
    ar = {}
    regex = re.compile(
        r'^M\( ([0-9]{7,}) \)(P|C, (0x[0-9a-f]{16})), offset = ([0-9]+), n = ([0-9]{3,})K, (CUDALucas v[^\s,]+)(?:, AID: ([0-9A-F]{32}))?$')
    res = regex.search(sendline)
    if not res:
        logging.error("Unable to parse entry in “{0}”: {1}".format(
            os.path.join(dir, options.resultsfile), sendline))
        return None

    if res.group(7):
        ar['aid'] = res.group(7)
    ar['worktype'] = 'LL'  # CUDALucas only does LL tests
    ar['status'] = res.group(2)[0]
    ar['exponent'] = int(res.group(1))

    ar['res64'] = "0" * 16 if res.group(2)[0] == 'P' else res.group(3)[2:]
    ar['shift-count'] = res.group(4)
    ar['fft-length'] = int(res.group(5)) * 1024
    program = res.group(6).split()
    ar['program'] = {}
    ar['program']['name'] = program[0]
    ar['program']['version'] = program[1]
    return ar


def submit_one_line(dir, sendline):
    """Submits a result to the server."""
    if not options.cudalucas:  # Mlucas or GpuOwl
        try:
            ar = json.loads(sendline)
            is_json = True
        except json.decoder.JSONDecodeError:
            logging.exception("Unable to decode entry in “{0}”: {1}".format(
                os.path.join(dir, options.resultsfile), sendline))
            # Mlucas
            if not options.gpuowl and "Program: E" in sendline:
                logging.info("Please upgrade to Mlucas v19 or greater.")
            # GpuOwl
            if options.gpuowl and "gpuowl v" in sendline:
                logging.info("Please upgrade to GpuOwl v0.7 or greater.")
            is_json = False
    else:  # CUDALucas
        ar = get_cuda_ar_object(dir, sendline)

    guid = get_guid(config)
    if guid is not None and ar is not None and (options.cudalucas or is_json):
        # If registered and the ar object was returned successfully, submit using the v5 API
        # The result will be attributed to the registered computer
        # If registered and the line is a JSON, submit using the v5 API
        # The result will be attributed to the registered computer
        sent = report_result(dir, sendline, guid, ar)
    else:
        # The result will be attributed to "Manual testing"
        sent = submit_one_line_manually(sendline)
    return sent


def announce_prime_to_user(exponent, worktype):
    """Announce a newly found prime to the user."""
    while True:
        if worktype == 'LL':
            print("New Mersenne Prime!!!! M{0} is prime!".format(exponent))
        else:
            print(
                "New Probable Prime!!!! {0} is a probable prime!".format(exponent))
        print("Please send e-mail to woltman@alum.mit.edu and ewmayer@aol.com.")
        try:
            import winsound
        except ImportError:
            print('\a')
        else:
            winsound.MessageBeep(type=-1)
        time.sleep(1)


def get_result_type(ar):
    """Returns the result type for the assignment result."""
    if ar['worktype'] == 'LL':
        if ar['status'] == 'P':
            return primenet_api.AR_LL_PRIME
        else:  # elif ar['status'] == 'C':
            return primenet_api.AR_LL_RESULT
    elif ar['worktype'].startswith('PRP'):
        if ar['status'] == 'P':
            return primenet_api.AR_PRP_PRIME
        else:  # elif ar['status'] == 'C':
            return primenet_api.AR_PRP_RESULT
    elif ar['worktype'] == 'PM1':
        if ar['status'] == 'F':
            return primenet_api.AR_P1_FACTOR
        else:  # elif ar['status'] == 'NF':
            return primenet_api.AR_P1_NOFACTOR
    else:
        raise ValueError(
            "This is a bug in the script, Unsupported worktype {0}".format(ar['worktype']))


def report_result(dir, sendline, guid, ar, retry_count=0):
    """Submit one result line using v5 API, will be attributed to the computed identified by guid"""
    """Return False if the submission should be retried"""
    if retry_count >= 5:
        logging.info("Retry count exceeded.")
        return False
    # JSON is required because assignment_id is necessary in that case
    # and it is not present in old output format.
    logging.debug("Submitting using v5 API")
    logging.debug("Program: " + " ".join(ar['program'].values()))
    aid = ar.get('aid', 0)
    result_type = get_result_type(ar)
    if result_type in [primenet_api.AR_LL_PRIME, primenet_api.AR_PRP_PRIME]:
        if not (config.has_option("PrimeNet", "SilentVictory")
                and config.getboolean("PrimeNet", "SilentVictory")):
            thread = threading.Thread(target=announce_prime_to_user, args=(
                ar['exponent'], ar['worktype']), daemon=True)
            thread.start()
        if options.no_report_100m and digits(int(ar['exponent'])) >= 100000000:
            return True
    args = primenet_v5_bargs.copy()
    args["t"] = "ar"								# assignment result
    args["g"] = guid
    args["k"] = aid			# assignment id
    args["m"] = sendline							# message is the complete JSON string
    args["r"] = result_type							# result type
    args["n"] = ar['exponent']
    if result_type in [primenet_api.AR_LL_RESULT, primenet_api.AR_LL_PRIME]:
        args["d"] = 1
        if result_type == primenet_api.AR_LL_RESULT:
            args["rd"] = ar['res64'].strip().zfill(16)
        args['sc'] = ar['shift-count']
        args["ec"] = ar['error-code'] if 'error-code' in ar else "00000000"
    elif result_type in [primenet_api.AR_PRP_RESULT, primenet_api.AR_PRP_PRIME]:
        args["d"] = 1
        args.update((("A", 1), ("b", 2), ("c", -1)))
        if result_type == primenet_api.AR_PRP_RESULT:
            args["rd"] = ar['res64'].strip().zfill(16)
            if 'residue-type' in ar:
                args["rt"] = ar['residue-type']
        args["ec"] = ar['error-code'] if 'error-code' in ar else "00000000"
        if 'known-factors' in ar:
            args['nkf'] = len(ar['known-factors'])
        args["base"] = ar['worktype'][4:]  # worktype == PRP-base
        if 'shift-count' in ar:
            args['sc'] = ar['shift-count']
        # 1 if Gerbicz error checking used in PRP test
        args['gbz'] = 1
        if 'proof' in ar:
            args['pp'] = ar['proof']['power']
            args['ph'] = ar['proof']['md5']
    elif result_type in [primenet_api.AR_P1_FACTOR, primenet_api.AR_P1_NOFACTOR]:
        workfile = os.path.join(dir, options.workfile)
        tasks = readonly_list_file(workfile)
        args["d"] = 1 if result_type == primenet_api.AR_P1_FACTOR or not any(assignment.n == int(
            ar['exponent']) for assignment in (parse_assignment(dir, task) for task in tasks) if assignment) else 0
        args.update((("A", 1), ("b", 2), ("c", -1)))
        args['B1'] = ar['B1']
        if 'B2' in ar:
            args['B2'] = ar['B2']
        if result_type == primenet_api.AR_P1_FACTOR:
            args["f"] = ar['factors'][0]
    # elif result_type == primenet_api.AR_CERT:
    if 'fft-length' in ar:
        args['fftlen'] = ar['fft-length']
    logging.info("Sending result to server: {0}".format(sendline))
    result = send_request(guid, args)
    if result is None:
        logging.debug(
            "ERROR while submitting result on mersenne.org: assignment_id={0}".format(aid))
        # if this happens, the submission can be retried
        # since no answer has been received from the server
        # return False
    else:
        rc = int(result["pnErrorResult"])
        if rc == primenet_api.ERROR_OK:
            logging.info("Result correctly send to server")
            return True
        else:  # non zero ERROR code
            logging.debug(
                "ERROR while submitting result on mersenne.org: assignment_id={0}".format(aid))
            if rc == primenet_api.ERROR_STALE_CPU_INFO:
                logging.debug("STALE CPU INFO ERROR: re-send computer update")
                register_instance(guid)
            elif rc == primenet_api.ERROR_UNREGISTERED_CPU:
                # should register again and retry
                logging.debug(
                    "UNREGISTERED CPU ERROR: pick a new GUID and register again")
                register_instance(None)
                # return False
            elif rc == primenet_api.ERROR_INVALID_PARAMETER:
                logging.error(
                    "INVALID PARAMETER: This may be a bug in the script, please create an issue: https://github.com/tdulcet/Distributed-Computing-Scripts/issues")
                return False
            # In all other error case, the submission must not be retried
            elif rc == primenet_api.ERROR_INVALID_ASSIGNMENT_KEY:
                # TODO: Delete assignment from workfile if it is not done
                return True
            elif rc == primenet_api.ERROR_WORK_NO_LONGER_NEEDED:
                # TODO: Delete assignment from workfile if it is not done
                return True
            elif rc == primenet_api.ERROR_NO_ASSIGNMENT:
                # TODO: Delete assignment from workfile if it is not done
                return True
            elif rc == primenet_api.ERROR_INVALID_RESULT_TYPE:
                return True

    return report_result(dir, sendline, guid, ar, retry_count + 1)


def submit_one_line_manually(sendline):
    """Submit results using manual testing, will be attributed to "Manual Testing" in mersenne.org"""
    logging.debug("Submitting using manual results")
    logging.info("Sending result: " + sendline)
    try:
        r = s.post(
            primenet_baseurl +
            "manual_result/default.php",
            data={
                "data": sendline})
        r.raise_for_status()
        res_str = r.text
        if "Error code" in res_str:
            ibeg = res_str.find("Error code")
            iend = res_str.find("</div>", ibeg)
            logging.error(
                "Submission failed: '{0}'".format(res_str[ibeg:iend]))
            if res_str[ibeg:iend].startswith('Error code: 40'):
                logging.error('Already sent, will not retry')
        elif "Accepted" in res_str:
            begin = res_str.find("CPU credit is")
            end = res_str.find("</div>", begin)
            if begin >= 0 and end >= 0:
                logging.info(res_str[begin:end])
        else:
            logging.error("Submission of results line '" + sendline +
                          "' failed for reasons unknown - please try manual resubmission.")
    except ConnectionError:
        logging.exception("URL open ERROR")
        return False
    return True  # EWM: Append entire results_send rather than just sent to avoid resubmitting
    # bad results (e.g. previously-submitted duplicates) every time the script
    # executes.


def submit_work(dir):
    """Submits the results file to PrimeNet."""
    # A cumulative backup
    sentfile = os.path.join(dir, "results_sent.txt")
    results_send = frozenset(readonly_list_file(sentfile))
    # Only submit completed work, i.e. the exponent must not exist in worktodo file any more
    # appended line by line, no lock needed
    resultsfile = os.path.join(dir, options.resultsfile)
    results = readonly_list_file(resultsfile)
    # EWM: Note that readonly_list_file does not need the file(s) to exist - nonexistent files simply yield 0-length rs-array entries.
    # remove nonsubmittable lines from list of possibles
    results = filter(mersenne_find, results)

    # if a line was previously submitted, discard
    results_send = [line for line in results if line not in results_send]

    # Only for new results, to be appended to results_sent
    sent = []

    length = len(results_send)
    if length == 0:
        logging.debug("No new results in “{0}”.".format(resultsfile))
        return
    logging.debug("Found {0:n} new result{1} to report in “{0}”".format(
        length, "s" if length > 1 else "", resultsfile))
    # EWM: Switch to one-result-line-at-a-time submission to support
    # error-message-on-submit handling:
    for sendline in results_send:
        # case where password is entered (not needed in v5 API since we have a key)
        if options.password:
            is_sent = submit_one_line_manually(sendline)
        else:
            is_sent = submit_one_line(dir, sendline)
        if is_sent:
            sent.append(sendline)
    write_list_file(sentfile, sent, "a")

#######################################################################################################
#
# Start main program here
#
#######################################################################################################


parser = optparse.OptionParser(version="%prog 1.0", description="""This program will automatically get assignments, report assignment results and optionally progress to PrimeNet for the GpuOwl, CUDALucas and Mlucas GIMPS programs. It also saves its configuration to a “local.ini” file, so it is only necessary to give most of the arguments the first time it is run.
The first time it is run, if a password is NOT provided, it will register the current GpuOwl/CUDALucas/Mlucas instance with PrimeNet (see below).
Then, it will get assignments, report the results, upload any proofs and report the progress, if registered, to PrimeNet on a “timeout” interval, or only once if timeout is 0.
"""
                               )

# options not saved to local.ini
parser.add_option("-d", "--debug", action="count", dest="debug", default=0,
                  help="Output detailed information. Provide multiple times for even more verbose output.")
parser.add_option("-w", "--workdir", dest="workdir", default=".",
                  help="Working directory with the local file from this program, Default: %default (current directory)")
parser.add_option("-D", "--dir", action="append", dest="dirs",
                  help="Directories with the worktodo and results files from the GIMPS program. Provide once for each worker thread. It automatically sets the --cpu_num option for each directory.")
parser.add_option("-i", "--workfile", dest="workfile",
                  default="worktodo.ini", help="WorkFile filename, Default: “%default”")
parser.add_option("-r", "--resultsfile", dest="resultsfile",
                  default="results.txt", help="ResultsFile filename, Default: “%default”")
parser.add_option("-l", "--localfile", dest="localfile", default="local.ini",
                  help="Local configuration file filename, Default: “%default”")
parser.add_option("--archive_proofs", dest="ProofArchiveDir",
                  help="Directory to archive PRP proof files after upload, Default: %default")

# all other options are saved to local.ini
parser.add_option("-u", "--username", dest="username", default="ANONYMOUS",
                  help="GIMPS/PrimeNet User ID. Create a GIMPS/PrimeNet account: https://www.mersenne.org/update/. If you do not want a PrimeNet account, you can use ANONYMOUS.")
parser.add_option("-p", "--password", dest="password",
                  help="Optional GIMPS/PrimeNet Password. Only provide if you want to do manual testing and not report the progress. This was the default behavior for old versions of this script.")

# -t is reserved for timeout, instead use -T for assignment-type preference:
parser.add_option("-T", "--worktype", dest="WorkPreference", default=str(primenet_api.WP_LL_FIRST), help="""Type of work, Default: %default,
4 (P-1 factoring),
100 (smallest available first-time LL),
101 (double-check LL),
102 (world-record-sized first-time LL),
104 (100M digit number LL),
150 (smallest available first-time PRP),
151 (double-check PRP),
152 (world-record-sized first-time PRP),
153 (100M digit number PRP),
154 (smallest available first-time PRP that needs P-1 factoring),
155 (double-check using PRP with proof),
160 (first time Mersenne cofactors PRP),
161 (double-check Mersenne cofactors PRP)
"""
                  )
parser.add_option("--min_exp", dest="GetMinExponent", type="int", default=0,
                  help="Minimum exponent to get from PrimeNet (2 - 999,999,999)")
parser.add_option("--max_exp", dest="GetMaxExponent", type="int", default=0,
                  help="Maximum exponent to get from PrimeNet (2 - 999,999,999)")

parser.add_option("-g", "--gpuowl", action="store_true", dest="gpuowl", default=False,
                  help="Get assignments for a GPU (GpuOwl) instead of the CPU (Mlucas).")
parser.add_option("--cudalucas", dest="cudalucas",
                  help="Get assignments for a GPU (CUDALucas) instead of the CPU (Mlucas). This option takes as an argument the CUDALucas output filename.")
parser.add_option("--num_workers", dest="WorkerThreads", type="int", default=1,
                  help="Number of worker threads (CPU Cores/GPUs), Default: %default")
parser.add_option("-c", "--cpu_num", dest="cpu", type="int", default=0,
                  help="CPU core or GPU number to get assignments for, Default: %default")
parser.add_option("-n", "--num_cache", dest="num_cache", type="int", default=0,
                  help="Number of assignments to cache, Default: %default (automatically set to 1 when doing manual testing)")
parser.add_option("-W", "--days_work", dest="DaysOfWork", type="float", default=3.0,
                  help="Days of work to queue (1-90 days), Default: %default days. Adds one to num_cache when the time left for the current assignment is less then this number of days.")
parser.add_option("--no_report_100m", action="store_true", dest="no_report_100m", default=False,
                  help="Do not report any prime results for exponents greater than 100 million digits. You must setup another method to notify yourself.")

parser.add_option("-t", "--timeout", dest="timeout", type="int", default=60 * 60,
                  help="Seconds to wait between network updates, Default: %default seconds (1 hour). Users with slower internet may want to set a larger value to give time for any PRP proofs to upload. Use 0 for a single update without looping.")
parser.add_option("-s", "--status", action="store_true", dest="status", default=False,
                  help="Output a status report and any expected completion dates for all assignments and exit.")
parser.add_option("--upload_proofs", action="store_true", dest="proofs", default=False,
                  help="Report assignment results, upload all PRP proofs and exit. Requires PrimeNet User ID.")
parser.add_option("--unreserve_all", action="store_true", dest="unreserve_all", default=False,
                  help="Unreserve all assignments and exit. Quit GIMPS immediately. Requires that the instance is registered with PrimeNet.")
parser.add_option("--no_more_work", action="store_true", dest="NoMoreWork", default=False,
                  help="Prevent script from getting new assignments and exit. Quit GIMPS after current work completes.")

group = optparse.OptionGroup(parser, "Registering Options: sent to PrimeNet/GIMPS when registering. The progress will automatically be sent and the program can then be monitored on the GIMPS website CPUs page (https://www.mersenne.org/cpus/), just like with Prime95/MPrime. This also allows for the program to get much smaller Category 0 and 1 exponents, if it meets the other requirements (https://www.mersenne.org/thresholds/).")
group.add_option("-H", "--hostname", dest="ComputerID", default=platform.node()[:20],
                 help="Optional computer name, Default: %default")
# TODO: add detection for most parameter, including automatic change of the hardware
group.add_option("--cpu_model", dest="cpu_model", default=cpu_signature if cpu_signature else "cpu.unknown",
                 help="Processor (CPU) model, Default: %default")
group.add_option("--features", dest="features", default="",
                 help="CPU features, Default: '%default'")
group.add_option("--frequency", dest="CpuSpeed", type="int", default=1000,
                 help="CPU frequency/speed (MHz), Default: %default MHz")
group.add_option("-m", "--memory", dest="memory", type="int", default=0,
                 help="Total memory (RAM) (MiB), Default: %default MiB. Required for P-1 assignments.")
group.add_option("--L1", dest="L1", type="int", default=8,
                 help="L1 Cache size (KiB), Default: %default KiB")
group.add_option("--L2", dest="L2", type="int", default=512,
                 help="L2 Cache size (KiB), Default: %default KiB")
group.add_option("--L3", dest="L3", type="int", default=0,
                 help="L3 Cache size (KiB), Default: %default KiB")
group.add_option("--np", dest="NumCores", type="int", default=1,
                 help="Number of physical CPU cores, Default: %default")
group.add_option("--hp", dest="CpuNumHyperthreads", type="int", default=0,
                 help="Number of CPU threads per core (0 is unknown), Default: %default. Choose 1 for non-hyperthreaded and 2 or more for hyperthreaded.")
group.add_option("--hours", dest="CPUHours", type="int", default=24,
                 help="Hours per day you expect to run the GIMPS program (1 - 24), Default: %default hours. Used to give better estimated completion dates.")
parser.add_option_group(group)

opts_no_defaults = optparse.Values()
__, args = parser.parse_args(values=opts_no_defaults)
options = optparse.Values(parser.get_default_values().__dict__)
options._update_careful(opts_no_defaults.__dict__)

logging.basicConfig(level=max(logging.INFO - (options.debug * 10), 0), format='%(filename)s: ' + (
    '%(funcName)s:\t' if options.debug > 0 else '') + '[%(threadName)s %(asctime)s]  %(levelname)s: %(message)s')

workdir = os.path.expanduser(options.workdir)
dirs = [os.path.join(workdir, dir)
        for dir in options.dirs] if options.dirs else [workdir]

# r'^(?:(Test|DoubleCheck)=([0-9A-F]{32})(,[0-9]+){3}|(PRP(?:DC)?)=([0-9A-F]{32})(,-?[0-9]+){4,8}(,"[0-9]+(?:,[0-9]+)*")?|(P[Ff]actor)=([0-9A-F]{32})(,-?[0-9]+){6}|(P[Mm]inus1)=([0-9A-F]{32})(,-?[0-9]+){6,8}(,"[0-9]+(?:,[0-9]+)*")?|(Cert)=([0-9A-F]{32})(,-?[0-9]+){5})$'
workpattern = re.compile(
    r'^(Test|DoubleCheck|PRP(?:DC)?|P[Ff]actor|P[Mm]inus1|Cert)\s*=\s*(?:(?:([0-9A-F]{32})|[Nn]/[Aa]|0),)?(?:(-?[0-9]+|"[0-9]+(?:,[0-9]+)*")(?:,|$)){3,9}$')

# mersenne.org limit is about 4 KB; stay on the safe side
# sendlimit = 3000  # TODO: enforce this limit

# If debug is requested

# https://stackoverflow.com/questions/10588644/how-can-i-see-the-entire-http-request-thats-being-sent-by-my-python-application
if options.debug > 1:
    try:
        from http.client import HTTPConnection
    except ImportError:
        # Python 2
        from httplib import HTTPConnection
    HTTPConnection.debuglevel = 1

    # You must initialize logging, otherwise you'll not see debug output.
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

# load local.ini and update options
config = config_read()
config_updated = merge_config_and_options(config, options)

# check options after merging so that if local.ini file is changed by hand,
# values are also checked
# TODO: check that input char are ascii or at least supported by the server
if not (8 <= len(options.cpu_model) <= 64):
    parser.error("cpu_model must be between 8 and 64 characters")
if options.ComputerID is not None and len(options.ComputerID) > 20:
    parser.error("ComputerID must be less than 21 characters")
if options.features is not None and len(options.features) > 64:
    parser.error("features must be less than 64 characters")

# Index into programs array
idx = 3 if options.cudalucas else 2 if options.gpuowl else 1

# Convert mnemonic-form worktypes to corresponding numeric value, check
# worktype value vs supported ones:
worktypes = {
    "Pfactor": primenet_api.WP_PFACTOR,
    "SmallestAvail": primenet_api.WP_LL_FIRST,
    "DoubleCheck": primenet_api.WP_LL_DBLCHK,
    "WorldRecord": primenet_api.WP_LL_WORLD_RECORD,
    "100Mdigit": primenet_api.WP_LL_100M,
    "SmallestAvailPRP": primenet_api.WP_PRP_FIRST,
    "DoubleCheckPRP": primenet_api.WP_PRP_DBLCHK,
    "WorldRecordPRP": primenet_api.WP_PRP_WORLD_RECORD,
    "100MdigitPRP": primenet_api.WP_PRP_100M}
# this and the above line of code enables us to use words or numbers on the cmdline
if options.WorkPreference in worktypes:
    options.WorkPreference = worktypes[options.WorkPreference]
supported = frozenset([primenet_api.WP_LL_FIRST,
                       primenet_api.WP_LL_DBLCHK,
                       primenet_api.WP_LL_WORLD_RECORD,
                       primenet_api.WP_LL_100M] + ([primenet_api.WP_PFACTOR,
                                                    primenet_api.WP_PRP_FIRST,
                                                    primenet_api.WP_PRP_DBLCHK,
                                                    primenet_api.WP_PRP_WORLD_RECORD,
                                                    primenet_api.WP_PRP_100M,
                                                    primenet_api.WP_PRP_NO_PMINUS1] if not options.cudalucas else []) + ([primenet_api.WP_PRP_DC_PROOF] if options.gpuowl else []))
if not options.WorkPreference.isdigit() or int(
        options.WorkPreference) not in supported:
    parser.error("Unsupported/unrecognized worktype = " +
                 options.WorkPreference + " for " + PROGRAMS[idx]["name"])
worktype = int(options.WorkPreference)
# Convert first time LL worktypes to PRP
option_dict = {
    primenet_api.WP_LL_FIRST: primenet_api.WP_PRP_FIRST,
    primenet_api.WP_LL_WORLD_RECORD: primenet_api.WP_PRP_WORLD_RECORD,
    primenet_api.WP_LL_100M: primenet_api.WP_PRP_100M}
if worktype in option_dict:
    worktype = option_dict[worktype]

# write back local.ini if necessary
if config_updated:
    logging.debug("write " + options.localfile)
    config_write(config)

# if guid already exist, recover it, this way, one can (re)register to change
# the CPU model (changing instance name can only be done in the website)
guid = get_guid(config)
if options.password and options.username is None:
    parser.error("Username must be given")

if options.dirs and len(options.dirs) != options.WorkerThreads:
    parser.error(
        "The number of directories must be equal to the number of worker threads")

if options.cpu >= options.WorkerThreads:
    parser.error(
        "CPU core or GPU number must be less than the number of worker threads")

if options.gpuowl and options.cudalucas:
    parser.error(
        "This script can only be used with GpuOwl or CUDALucas")

if 0 < options.timeout < 60 * 60:
    parser.error(
        "Timeout must be greater than or equal to {0:n} seconds (1 hour)".format(60 * 60))

if options.status:
    output_status(dirs)
    sys.exit(0)

if options.proofs:
    for i, dir in enumerate(dirs):
        if options.dirs:
            logging.info("[Worker #{0:n}]".format(i + 1))
        submit_work(dir)
        upload_proofs(dir)
    sys.exit(0)

if options.unreserve_all:
    unreserve_all(dirs)
    sys.exit(0)

if options.NoMoreWork:
    logging.info("Quitting GIMPS after current work completes.")
    config.set("PrimeNet", "NoMoreWork", "1")
    config_write(config)
    sys.exit(0)

# use the v5 API for registration and program options
if options.password is None:
    if guid is None:
        register_instance(guid)
        if options.timeout <= 0:
            sys.exit(0)
    # worktype has changed, update worktype preference in program_options()
    elif config_updated:
        register_instance(guid)

while True:
    config = config_read()
    # Carry on with Loarer's style of primenet
    if options.password:
        try:
            login_data = {"user_login": options.username,
                          "user_password": options.password}
            r = s.post(primenet_baseurl + "default.php", data=login_data)
            r.raise_for_status()

            if options.username + "<br>logged in" not in r.text:
                primenet_login = False
                logging.error("Login failed.")
            else:
                primenet_login = True
        except HTTPError as e:
            logging.exception("Login failed.")

    for i, dir in enumerate(dirs):
        if options.dirs:
            logging.info("[Worker #{0:n}]".format(i + 1))
        cpu = i if options.dirs else options.cpu
        # branch 1 or branch 2 above was taken
        if not options.password or primenet_login:
            submit_work(dir)
            progress = update_progress_all(dir, cpu)
            got = get_assignments(dir, cpu, progress)
            # logging.debug("Got: {0:n}".format(got))
            if got > 0 and not options.password:
                logging.debug(
                    "Redo progress update to acknowledge receipt of the just obtained assignment" + ("s" if got > 1 else ""))
                time.sleep(1)
                update_progress_all(dir, cpu)
        if options.timeout <= 0:
            upload_proofs(dir)
    if options.timeout <= 0:
        break
    thread = threading.Thread(target=aupload_proofs, args=(dirs,))
    thread.start()
    try:
        time.sleep(options.timeout)
    except KeyboardInterrupt:
        break
    thread.join()

sys.exit(0)
