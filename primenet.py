#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Automatic assignment handler for Mlucas, GpuOwl and CUDALucas.

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
    * Register Assignment (ra, register_assignment) (Credit: Dulcet)
    * Assignment Un-Reserve (au, assignment_unreserve) (Credit: Dulcet)
    * Assignment Progress (ap, send_progress) (Credit: Loarer & Dulcet)
    * Assignment Result (ar, report_result) (Credit: Loarer & Dulcet)
    * Benchmark Data Statistics (bd) N/A
    * Ping Server (ps, ping_server) (Credit: Dulcet)
"""

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

import csv
import json
import locale
import logging
import math
import optparse
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import threading
import time
import timeit
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from hashlib import md5

try:
    # Python 3+
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

try:
    # Python 3+
    from configparser import ConfigParser
    from configparser import Error as ConfigParserError
except ImportError:
    from ConfigParser import ConfigParser
    from ConfigParser import Error as ConfigParserError

if sys.version_info[:2] >= (3, 7):
    # Python 3.7+
    # If is OK to use dict in 3.7+ because insertion order is guaranteed to be preserved
    # Since it is also faster, it is better to use raw dict()
    OrderedDict = dict
else:
    try:
        # Python 2.7 and 3.1+
        from collections import OrderedDict
    except ImportError:
        # Tests will not work correctly but it doesn't affect the
        # functionality
        OrderedDict = dict

try:
    # Python 3.4+
    from statistics import median_low
except ImportError:
    def median_low(data):
        sorts = sorted(data)
        length = len(sorts)
        return sorts[(length - 1) // 2]

try:
    # Python 3.3+
    from math import log2
except ImportError:
    def log2(x):
        return math.log(x, 2)

try:
    # Python 3.2+
    from math import expm1
except ImportError:
    def expm1(x):
        return math.exp(x) - 1

try:
    # Windows
    import winsound
except ImportError:
    def beep():
        print("\a")
else:
    def beep():
        winsound.MessageBeep(type=-1)

try:
    import requests
    from requests.exceptions import ConnectionError, HTTPError, Timeout
except ImportError:
    print("Installing requests as dependency")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    print("The Requests library has been installed. Please run the program again")
    sys.exit(0)

locale.setlocale(locale.LC_ALL, "")

VERSION = "1.1"
section = "PrimeNet"
# GIMPS programs to use in the application version string when registering with PrimeNet
PROGRAMS = [
    {"name": "Prime95", "version": "30.8", "build": 17},
    {"name": "Mlucas", "version": "20.1.1"},
    {"name": "GpuOwl", "version": "7.2.1"},
    {"name": "CUDALucas", "version": "2.06"}]

primenet_v5_burl = "http://v5.mersenne.org/v5server/"
TRANSACTION_API_VERSION = 0.95
ERROR_RATE = 0.018  # Estimated LL error rate on clean run
# Estimated PRP error rate (assumes Gerbicz error-checking)
PRP_ERROR_RATE = 0.0001
_V5_UNIQUE_TRUSTED_CLIENT_CONSTANT_ = 17737
primenet_v5_bargs = OrderedDict(
    (("px", "GIMPS"), ("v", TRANSACTION_API_VERSION)))
primenet_baseurl = "https://www.mersenne.org/"
primenet_login = False

is_64bit = platform.machine().endswith("64")
system = platform.system()
PORT = None
if system == "Windows":
    PORT = 4 if is_64bit else 1
elif system == "Darwin":
    PORT = 10 if is_64bit else 9
elif system == "Linux":
    PORT = 8 if is_64bit else 2
session = requests.Session()  # session that maintains our cookies


class PRIMENET:
    # Error codes returned to client
    ERROR_OK = 0  # no error
    ERROR_SERVER_BUSY = 3  # server is too busy now
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

    # Valid work_preference values
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

    # Valid work_types returned by ga
    WORK_TYPE_FACTOR = 2
    WORK_TYPE_PMINUS1 = 3
    WORK_TYPE_PFACTOR = 4
    WORK_TYPE_ECM = 5
    WORK_TYPE_PPLUS1 = 6		# Not yet supported by the server
    WORK_TYPE_FIRST_LL = 100
    WORK_TYPE_DBLCHK = 101
    WORK_TYPE_PRP = 150
    WORK_TYPE_CERT = 200

    # This structure is passed for the ar - Assignment Result call
    AR_NO_RESULT = 0  # No result, just sending done msg
    AR_TF_FACTOR = 1  # Trial factoring, factor found
    AR_P1_FACTOR = 2  # P-1, factor found
    AR_ECM_FACTOR = 3  # ECM, factor found
    AR_TF_NOFACTOR = 4  # Trial Factoring no factor found
    AR_P1_NOFACTOR = 5  # P-1 factoring no factor found
    AR_ECM_NOFACTOR = 6  # ECM factoring no factor found
    AR_PP1_FACTOR = 7  # P+1, factor found
    AR_PP1_NOFACTOR = 8  # P+1 factoring no factor found
    AR_LL_RESULT = 100  # LL result, not prime
    AR_LL_PRIME = 101  # LL result, Mersenne prime
    AR_PRP_RESULT = 150  # PRP result, not prime
    AR_PRP_PRIME = 151  # PRP result, probably prime
    AR_CERT = 200  # Certification result


errors = {
    PRIMENET.ERROR_SERVER_BUSY: "Server busy",
    PRIMENET.ERROR_INVALID_VERSION: "Invalid version",
    PRIMENET.ERROR_INVALID_TRANSACTION: "Invalid transaction",
    PRIMENET.ERROR_INVALID_PARAMETER: "Invalid parameter",
    PRIMENET.ERROR_ACCESS_DENIED: "Access denied",
    PRIMENET.ERROR_DATABASE_CORRUPT: "Server database malfunction",
    PRIMENET.ERROR_DATABASE_FULL_OR_BROKEN: "Server database full or broken",
    PRIMENET.ERROR_INVALID_USER: "Invalid user",
    PRIMENET.ERROR_UNREGISTERED_CPU: "CPU not registered",
    PRIMENET.ERROR_OBSOLETE_CLIENT: "Obsolete client, please upgrade",
    PRIMENET.ERROR_STALE_CPU_INFO: "Stale cpu info",
    PRIMENET.ERROR_CPU_IDENTITY_MISMATCH: "CPU identity mismatch",
    PRIMENET.ERROR_CPU_CONFIGURATION_MISMATCH: "CPU configuration mismatch",
    PRIMENET.ERROR_NO_ASSIGNMENT: "No assignment",
    PRIMENET.ERROR_INVALID_ASSIGNMENT_KEY: "Invalid assignment key",
    PRIMENET.ERROR_INVALID_ASSIGNMENT_TYPE: "Invalid assignment type",
    PRIMENET.ERROR_INVALID_RESULT_TYPE: "Invalid result type"}


class Assignment(object):

    """Assignment(work_type, uid, k, b, n, c, sieve_depth, pminus1ed, B1, B2, B2_start, tests_saved, prp_base, prp_residue_type, prp_dblchk, known_factors, ra_failed)."""

    __slots__ = (
        "work_type", "uid", "k", "b", "n", "c", "sieve_depth", "pminus1ed",
        "B1", "B2", "B2_start", "tests_saved", "prp_base", "prp_residue_type",
        "prp_dblchk", "known_factors", "ra_failed")

    def __init__(self, work_type=None):
        """Create new instance of Assignment(work_type, uid, k, b, n, c, sieve_depth, pminus1ed, B1, B2, B2_start, tests_saved, prp_base, prp_residue_type, prp_dblchk, known_factors, ra_failed)."""
        self.work_type = work_type
        self.uid = None
        # k*b^n+c
        self.k = 1.0
        self.b = 2
        self.n = 0
        self.c = -1
        self.sieve_depth = 99.0
        self.pminus1ed = 1
        self.B1 = 0
        self.B2 = 0
        self.B2_start = 0
        self.tests_saved = 0.0
        self.prp_base = 0
        self.prp_residue_type = 0
        self.prp_dblchk = False
        self.known_factors = None
        self.ra_failed = False
        # self.cert_squarings = 0


suffix_power_char = ["", "K", "M", "G", "T", "P", "E", "Z", "Y", "R", "Q"]


def readonly_list_file(filename, mode="r"):
    """Reads a file line by line into a list."""
    # Used when there is no intention to write the file back, so don't
    # check or write lockfiles. Also returns a single string, no list.
    try:
        with open(filename, mode) as file:
            return [line.rstrip() for line in file]
    except (IOError, OSError):
        # logging.debug("Error reading {0!r} file.".format(filename))
        return []


def write_list_file(filename, line, mode="w"):
    """Write a list of strings to a file."""
    # A "null append" is meaningful, as we can call this to clear the
    # lockfile. In this case the main file need not be touched.
    if "a" not in mode or line:
        newline = b"\n" if "b" in mode else "\n"
        with open(filename, mode) as file:
            if line:
                file.write(newline.join(line) + newline)


def check_output(args):
    """Runs the command specified by args and returns its output."""
    process = subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    stdout, stderr = process.communicate()
    retcode = process.poll()
    if retcode or stderr:
        print("Exit code:", retcode, "\nArgs:", args,
              "\nstdout:\n", stdout, "\nstderr:\n", stderr)
    return stdout


def config_read():
    """Reads the configuration file."""
    config = ConfigParser(dict_type=OrderedDict)
    config.optionxform = lambda option: option
    localfile = os.path.join(workdir, options.localfile)
    try:
        config.read([localfile])
    except ConfigParserError:
        logging.exception("ERROR reading {0!r} file:".format(localfile))
    if not config.has_section(section):
        # Create the section to avoid having to test for it later
        config.add_section(section)
    return config


def config_write(config, guid=None):
    """Write the given configuration object to the local config file."""
    # generate a new local.ini file
    if guid is not None:  # update the guid if necessary
        config.set(section, "ComputerGUID", guid)
    localfile = os.path.join(workdir, options.localfile)
    with open(localfile, "w") as configfile:
        config.write(configfile)


def get_guid(config):
    """Returns the GUID from the config file, or None if it is not present."""
    try:
        return config.get(section, "ComputerGUID")
    except ConfigParserError:
        return None


def create_new_guid():
    """Create a new GUID."""
    return uuid.uuid4().hex


def merge_config_and_options(config, options):
    """Updates the options object with the values found in the local configuration file."""
    # getattr and setattr allow access to the options.xxxx values by name
    # which allow to copy all of them programmatically instead of having
    # one line per attribute. Only the attr_to_copy list need to be updated
    # when adding an option you want to copy from argument options to
    # local.ini config.
    attr_to_copy = {
        "worktodo_file": "workfile", "results_file": "resultsfile",
        "logfile": "logfile", "archive_dir": "ProofArchiveDir",
        "user_id": "username", "password": "password",
        "work_preference": "WorkPreference", "min_exp": "GetMinExponent",
        "max_exp": "GetMaxExponent", "gpuowl": "gpuowl",
        "cudalucas": "cudalucas", "num_worker_threads": "WorkerThreads",
        "num_cache": "num_cache", "days_of_work": "DaysOfWork",
        "tests_saved": "tests_saved", "pm1_multiplier": "pm1_multiplier",
        "no_report_100m": "no_report_100m",
        "convert_ll_to_prp": "convert_ll_to_prp",
        "convert_prp_to_ll": "convert_prp_to_ll",
        "hours_between_checkins": "HoursBetweenCheckins",
        "computer_id": "ComputerID", "cpu_brand": "CpuBrand",
        "cpu_features": "cpu_features", "cpu_speed": "CpuSpeed",
        "memory": "memory", "day_night_memory": "Memory",
        "cpu_l1_cache_size": "L1", "cpu_l2_cache_size": "L2",
        "cpu_l3_cache_size": "L3", "num_cores": "NumCores",
        "cpu_hyperthreads": "CpuNumHyperthreads", "cpu_hours": "CPUHours"}
    updated = False
    for attr, option in attr_to_copy.items():
        # if "attr" has its default value in options, copy it from config
        attr_val = getattr(options, attr)
        if not hasattr(opts_no_defaults, attr) and config.has_option(
                section, option):
            # If no option is given and the option exists in local.ini, take it
            # from local.ini
            if isinstance(attr_val, bool):
                new_val = config.getboolean(section, option)
            else:
                new_val = config.get(section, option)
            # config file values are always str()
            # they need to be converted to the expected type from options
            if attr_val is not None:
                new_val = type(attr_val)(new_val)
            setattr(options, attr, new_val)
        elif attr_val is not None and (not config.has_option(section, option)
                                       or config.get(section, option) != str(attr_val)):
            # If an option is given (even default value) and it is not already
            # identical in local.ini, update local.ini
            logging.debug("update {0!r} with {1}={2}".format(
                options.localfile, option, attr_val))
            config.set(section, option, str(attr_val))
            updated = True

    return updated


def is_known_mersenne_prime(p):
    """Returns True if the given Mersenne prime is known, and False otherwise."""
    primes = frozenset(
        [2, 3, 5, 7, 13, 17, 19, 31, 61, 89, 107, 127, 521, 607, 1279, 2203,
         2281, 3217, 4253, 4423, 9689, 9941, 11213, 19937, 21701, 23209, 44497,
         86243, 110503, 132049, 216091, 756839, 859433, 1257787, 1398269,
         2976221, 3021377, 6972593, 13466917, 20996011, 24036583, 25964951,
         30402457, 32582657, 37156667, 42643801, 43112609, 57885161, 74207281,
         77232917, 82589933])
    return p in primes


def is_prime(n):
    """Return True if n is a prime number, else False."""
    if n < 2:
        return False
    if n in {2, 3, 5}:
        return True
    for p in (2, 3, 5):
        if not n % p:
            return False

    # math.isqrt(n)
    for p in range(7, int(math.sqrt(n)) + 1, 30):
        for i in (0, 4, 6, 10, 12, 16, 22, 24):
            if not n % (p + i):
                return False
    return True


def digits(n):
    """Returns the number of digits in the decimal representation of n."""
    return int(n * Decimal(2).log10() + 1)


def parse_assignment(task):
    """Parse a line from a workfile into an Assignment namedtuple."""
    # Ex: Test=197ED240A7A41EC575CB408F32DDA661,57600769,74
    found = workpattern.search(task)
    if not found:
        return None
    # logging.debug(task)
    work_type = found.group(1)  # e.g., "Test"
    value = found.group(2)
    assignment = Assignment()
    assignment.uid = found.group(3)  # e.g., "197ED240A7A41EC575CB408F32DDA661"
    assignment.ra_failed = bool(value) and not assignment.uid
    # e.g., "57600769", "197ED240A7A41EC575CB408F32DDA661"
    # logging.debug("type = {0}, assignment_id = {1}".format(work_type, assignment.uid))
    temp = task.split("=", 1)[1]
    found = next(csv.reader([temp]))
    afound = temp.split(",", len(found) - 1)
    if value:
        found.pop(0)
        afound.pop(0)
    length = len(found)
    idx = 0 if work_type in {"Test", "DoubleCheck"} else 2
    if length <= idx:
        return None
    # Extract the subfield containing the exponent, whose position depends on
    # the assignment type:
    if work_type in {"Test", "DoubleCheck"}:
        assignment.work_type = PRIMENET.WORK_TYPE_FIRST_LL if work_type == "Test" else PRIMENET.WORK_TYPE_DBLCHK
        assignment.n = int(found[0])
        if length > 2:
            assignment.sieve_depth = float(found[1])
            assignment.pminus1ed = int(found[2])
        # assignment.tests_saved = 1.3 if assignment.work_type == PRIMENET.WORK_TYPE_FIRST_LL else 1.0
    elif work_type in {"PRP", "PRPDC"}:
        assignment.prp_dblchk = work_type == "PRPDC"
        assignment.work_type = PRIMENET.WORK_TYPE_PRP
        assignment.k = float(found[0])
        assignment.b = int(found[1])
        assignment.n = int(found[2])
        assignment.c = int(found[3])
        idx = 4
        if length > 5 and not afound[4].startswith('"'):
            assignment.sieve_depth = float(found[4])
            assignment.tests_saved = float(found[5])
            idx += 2
            if length > 7 and not afound[6].startswith('"'):
                assignment.prp_base = int(found[6])
                assignment.prp_residue_type = int(found[7])
                idx += 2
        if length > idx and afound[idx].startswith('"'):
            assignment.known_factors = found[idx]
    elif work_type in {"PFactor", "Pfactor"}:
        assignment.work_type = PRIMENET.WORK_TYPE_PFACTOR
        assignment.k = float(found[0])
        assignment.b = int(found[1])
        assignment.n = int(found[2])
        assignment.c = int(found[3])
        assignment.sieve_depth = float(found[4])
        assignment.tests_saved = float(found[5])
    elif work_type in {"PMinus1", "Pminus1"}:
        assignment.work_type = PRIMENET.WORK_TYPE_PMINUS1
        assignment.k = float(found[0])
        assignment.b = int(found[1])
        assignment.n = int(found[2])
        assignment.c = int(found[3])
        assignment.B1 = int(found[4])
        assignment.B2 = int(found[5])
        idx = 6
        assignment.sieve_depth = 0.0
        if length > idx and not afound[idx].startswith('"'):
            assignment.sieve_depth = float(found[idx])
            idx += 1
            if length > idx and not afound[idx].startswith('"'):
                assignment.B2_start = int(found[idx])
                idx += 1
        if length > idx and afound[idx].startswith('"'):
            assignment.known_factors = found[idx]
    elif work_type == "Cert":
        assignment.work_type = PRIMENET.WORK_TYPE_CERT
        assignment.k = float(found[0])
        assignment.b = int(found[1])
        assignment.n = int(found[2])
        assignment.c = int(found[3])
        # assignment.cert_squarings = int(found[4])
    return assignment


def read_workfile(adir):
    workfile = os.path.join(adir, options.worktodo_file)
    tasks = readonly_list_file(workfile)
    addfile = os.path.splitext(workfile)[0] + ".add"
    add = readonly_list_file(addfile)
    if add:
        write_list_file(workfile, add, "a")
        os.remove(addfile)
        tasks += add
    if not tasks:
        return tasks
    assignments = []
    for task in tasks:
        illegal_line = False
        assignment = parse_assignment(task)
        if assignment is not None:
            if assignment.k == 1.0 and assignment.b == 2 and not is_prime(
                    assignment.n) and assignment.c == -1 and not assignment.known_factors and assignment.work_type != PRIMENET.WORK_TYPE_PMINUS1:
                logging.error(
                    "{0!r} file contained composite exponent: {1}.".format(workfile, assignment.n))
                illegal_line = True
            if assignment.work_type == PRIMENET.WORK_TYPE_PMINUS1 and assignment.B1 < 50000:
                logging.error(
                    "{0!r} file has P-1 with B1 < 50000 (exponent: {1}).".format(workfile, assignment.n))
                illegal_line = True
        else:
            illegal_line = True
        if illegal_line:
            logging.error(
                "Illegal line in {0!r} file: {1!r}".format(workfile, task))
            assignments.append(task)
        else:
            assignments.append(assignment)
    return assignments


def output_assignment(assignment):
    temp = []
    if assignment.uid:
        temp.append(assignment.uid)
    elif assignment.ra_failed:
        temp.append("N/A")

    if assignment.work_type in {
            PRIMENET.WORK_TYPE_FIRST_LL, PRIMENET.WORK_TYPE_DBLCHK}:
        test = "Test" if assignment.work_type == PRIMENET.WORK_TYPE_FIRST_LL else "DoubleCheck"
        temp += [assignment.n]
        if assignment.sieve_depth != 99.0 or assignment.pminus1ed != 1:
            temp += ["{0:.0f}".format(assignment.sieve_depth),
                     assignment.pminus1ed]
    elif assignment.work_type == PRIMENET.WORK_TYPE_PRP:
        test = "PRP" + ("DC" if assignment.prp_dblchk else "")
        temp += ["{0:.0f}".format(assignment.k),
                 assignment.b, assignment.n, assignment.c]
        if assignment.sieve_depth != 99.0 or assignment.tests_saved > 0.0 or assignment.prp_base or assignment.prp_residue_type:
            temp += ["{0:g}".format(assignment.sieve_depth),
                     "{0:g}".format(assignment.tests_saved)]
            if assignment.prp_base or assignment.prp_residue_type:
                temp += [assignment.prp_base, assignment.prp_residue_type]
        if assignment.known_factors:
            temp += ['"' + assignment.known_factors + '"']
    elif assignment.work_type == PRIMENET.WORK_TYPE_PFACTOR:
        test = "Pfactor"
        temp += ["{0:.0f}".format(assignment.k), assignment.b, assignment.n, assignment.c,
                 "{0:g}".format(assignment.sieve_depth), "{0:g}".format(assignment.tests_saved)]
    elif assignment.work_type == PRIMENET.WORK_TYPE_PMINUS1:
        test = "Pminus1"
        temp += ["{0:.0f}".format(assignment.k), assignment.b,
                 assignment.n, assignment.c, assignment.B1, assignment.B2]
        if assignment.sieve_depth > 0.0:
            temp += ["{0:.0f}".format(assignment.sieve_depth)]
        if assignment.B2_start > assignment.B1:
            temp += [assignment.B2_start]
        if assignment.known_factors:
            temp += ['"' + assignment.known_factors + '"']
    elif assignment.work_type == PRIMENET.WORK_TYPE_CERT:
        test = "Cert"
        temp += ["{0:.0f}".format(assignment.k), assignment.b,
                 assignment.n, assignment.c, assignment.cert_squarings]
    return test + "=" + ",".join(map(str, temp))


def write_workfile(adir, assignments):
    workfile = os.path.join(adir, options.worktodo_file)
    tasks = [output_assignment(task) if isinstance(
        task, Assignment) else task for task in assignments]
    write_list_file(workfile, tasks)


def assignment_to_str(assignment):
    if not assignment.n:
        buf = "{0:.0f}".format(assignment.k + assignment.c)
    elif assignment.k != 1.0:
        buf = "{0.k:.0f}*{0.b}^{0.n}{0.c:+}".format(assignment)
    elif assignment.b == 2 and assignment.c == -1:
        buf = "M{0.n}".format(assignment)
    else:
        cnt = 0
        temp_n = assignment.n
        while not temp_n & 1:
            temp_n >>= 1
            cnt += 1
        if assignment.b == 2 and temp_n == 1 and assignment.c == 1:
            buf = "F{0}".format(cnt)
        else:
            buf = "{0.b}^{0.n}{0.c:+}".format(assignment)
    return buf


resultpattern = re.compile(r"Program: E|Mlucas|CUDALucas v|gpuowl")


def mersenne_find(line, complete=True):
    """Check for result in a line of text."""
    # Pre-v19 old-style HRF-formatted result used "Program:..."; starting
    # w/v19 JSON-formatted result uses "program",
    return resultpattern.search(line)


def announce_prime_to_user(exponent, worktype):
    """Announce a newly found prime to the user."""
    while True:
        if worktype == "LL":
            print("New Mersenne Prime!!!! M{0} is prime!".format(exponent))
        else:
            print(
                "New Probable Prime!!!! {0} is a probable prime!".format(exponent))
        print("Please send e-mail to woltman@alum.mit.edu and ewmayer@aol.com.")
        beep()
        time.sleep(1)


def outputunit(number, scale=False):
    scale_base = 1000 if scale else 1024

    power = 0
    while abs(number) >= scale_base:
        power += 1
        number /= scale_base

    anumber = abs(number)
    anumber += 0.0005 if anumber < 10 else 0.005 if anumber < 100 else 0.05 if anumber < 1000 else 0.5

    if number and anumber < 1000 and power > 0:
        strm = "{0:.{prec}g}".format(number, prec=sys.float_info.dig)

        length = 5 + (number < 0)
        if len(strm) > length:
            prec = 3 if anumber < 10 else 2 if anumber < 100 else 1
            strm = "{0:.{prec}f}".format(number, prec=prec)
    else:
        strm = "{0:.0f}".format(number)

    strm += suffix_power_char[power] if power < len(
        suffix_power_char) else "(error)"

    if not scale and power > 0:
        strm += "i"

    return strm


def generate_application_str():
    if system == "Darwin":
        aplatform = "Mac OS X" + (" 64-bit" if is_64bit else "")
    else:
        aplatform = system + ("64" if is_64bit else "")
    program = PROGRAMS[0 if options.prime95 else 3 if options.cudalucas else 2 if options.gpuowl else 1]
    if options.prime95:
        return "{0},{1[name]},v{1[version]},build {1[build]}".format(
            aplatform, program)
    name = program["name"]
    version = program["version"]
    if config.has_option(section, "version"):
        name, version = config.get(section, "version").split(None, 1)
        version = version[1:] if version.startswith("v") else version
    # return "{0},{1},v{2};Python {3},{4}".format(
        # aplatform, name, version, platform.python_version(), parser.get_version())
    return "{0},{1},v{2}".format(aplatform, name, version)


def get_cpu_model():
    """Returns the CPU model name as a string."""
    output = ""
    if system == "Windows":
        output = check_output("wmic cpu get name").splitlines()[2].rstrip()
    elif system == "Darwin":
        os.environ["PATH"] += os.pathsep + "/usr/sbin"
        output = check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"]).rstrip()
    elif system == "Linux":
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    output = re.sub(r"^.*: *", "", line.rstrip(), 1)
                    break
    return output


def get_cpu_cores_threads():
    """Returns the number of CPU cores and threads on the system."""
    # threads = os.cpu_count()
    cores = threads = 0
    if system == "Windows":
        # os.environ['NUMBER_OF_PROCESSORS']
        cores, threads = check_output(
            "wmic cpu get NumberOfCores,NumberOfLogicalProcessors").splitlines()[2].split()
    elif system == "Darwin":
        os.environ["PATH"] += os.pathsep + "/usr/sbin"
        cores, threads = check_output(
            ["sysctl", "-n", "hw.physicalcpu_max", "hw.logicalcpu_max"]).splitlines()
    elif system == "Linux":
        acores = set()
        # athreads = set()
        output = check_output(["lscpu", "-ap"])
        for line in output.splitlines():
            if not line.startswith("#"):
                # CPU,Core,Socket,Node
                cpu, core = map(int, line.split(",")[:2])
                acores.add(core)
                # athreads.add(cpu)
        cores = len(acores)
        threads = os.sysconf(str("SC_NPROCESSORS_CONF"))
    if cores:
        cores = int(cores)
    if threads:
        threads = int(threads)
    return cores, threads


def get_cpu_frequency():
    """Returns the CPU frequency in MHz."""
    output = ""
    if system == "Windows":
        output = check_output("wmic cpu get MaxClockSpeed").splitlines()[
            2].rstrip()
        if output:
            output = int(output)
    elif system == "Darwin":
        os.environ["PATH"] += os.pathsep + "/usr/sbin"
        output = check_output(["sysctl", "-n", "hw.cpufrequency_max"]).rstrip()
        if output:
            output = int(output) // 1000 // 1000
    elif system == "Linux":
        freqs = []
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("cpu MHz"):
                    freqs.append(
                        float(re.sub(r"^.*: *", "", line.rstrip(), 1)))
        if freqs:
            freq = set(freqs)
            if len(freq) == 1:
                output = int(freq.pop())
    return output


def get_physical_memory():
    """Returns the total amount of physical memory in the system, in mebibytes."""
    output = ""
    if system == "Windows":
        output = check_output("wmic memphysical get MaxCapacity").splitlines()[
            2].rstrip()
        if output:
            output = int(output) // 1024
    elif system == "Darwin":
        os.environ["PATH"] += os.pathsep + "/usr/sbin"
        output = check_output(["sysctl", "-n", "hw.memsize"]).rstrip()
        if output:
            output = int(output) // 1024 // 1024
    elif system == "Linux":
        # os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    output = int(line.split()[1]) // 1024
                    break
    return output


def parse_v5_resp(r):
    """Parse the response from the server into a dict."""
    ans = {}
    for line in r.split("\n"):
        if line == "==END==":
            break
        option, _, value = line.partition("=")
        ans[option] = value.replace("\r", "\n")
    return ans


__v5salt_ = 0


def secure_v5_url(guid, args):
    k = bytearray(md5(guid.encode("utf-8")).digest())

    for i in range(16):
        k[i] ^= k[(k[i] ^ _V5_UNIQUE_TRUSTED_CLIENT_CONSTANT_ & 0xFF) %
                  16] ^ _V5_UNIQUE_TRUSTED_CLIENT_CONSTANT_ // 256

    p_v5key = md5(k).hexdigest().upper()

    global __v5salt_
    if not __v5salt_:
        random.seed()

    __v5salt_ = random.randint(0, sys.maxsize) & 0xFFFF

    args["ss"] = __v5salt_
    URL = urlencode(args) + "&" + p_v5key

    ahash = md5(URL.encode("utf-8")).hexdigest().upper()

    args["sh"] = ahash


def send_request(guid, args):
    """Send a request to the PrimeNet server."""
    try:
        if guid is not None:
            if not options.prime95:
                args["ss"] = 19191919
                args["sh"] = "ABCDABCDABCDABCDABCDABCDABCDABCD"
            else:
                secure_v5_url(guid, args)
        # logging.debug("Args: {0}".format(args))
        r = session.get(primenet_v5_burl, params=args, timeout=180)
        # logging.debug("URL: " + r.url)
        r.raise_for_status()
        result = parse_v5_resp(r.text)
        # logging.debug("RESPONSE:\n" + r.text)
        if "pnErrorResult" not in result:
            logging.error(
                "PnErrorResult value missing.  Full response was:\n" + r.text)
            return None
        if "pnErrorDetail" not in result:
            logging.error("PnErrorDetail string missing")
            return None
        rc = int(result["pnErrorResult"])
        if rc:
            resmsg = errors.get(rc, "Unknown error code")
            logging.error("PrimeNet error {0}: {1}".format(rc, resmsg))
            logging.error(result["pnErrorDetail"])
        elif result["pnErrorDetail"] != "SUCCESS":
            logging.info("PrimeNet success code with additional info:")
            logging.info(result["pnErrorDetail"])

    except Timeout:
        logging.exception("")
        return None
    except HTTPError:
        logging.exception("ERROR receiving answer to request: " + r.url)
        return None
    except ConnectionError:
        logging.exception("ERROR connecting to server for request: ")
        return None
    return result


def get_exponent(n):
    try:
        args = {"exp_lo": n, "faclim": 1, "json": 1}
        r = session.get(primenet_baseurl +
                        "report_exponent_simple/", params=args, timeout=180)
        r.raise_for_status()
        json = r.json()

    except Timeout:
        logging.exception("")
        return None
    except HTTPError:
        logging.exception("")
        return None
    except ConnectionError:
        logging.exception("")
        return None
    return json


# Adapted from Mihai Preda's script: https://github.com/preda/gpuowl/blob/d8bfa25366bef4178dbd2059e2ba2a3bf3b6e0f0/pm1/pm1.py

# Table of values of Dickman's "rho" function for argument from 2 in steps of 1/20.
rhotab = [
    0.306852819440055, 0.282765004395792, 0.260405780162154, 0.239642788276221, 0.220357137908328, 0.202441664262192, 0.185799461593866, 0.170342639724018, 0.155991263872504, 0.142672445952511,
    0.130319561832251, 0.118871574006370, 0.108272442976271, 0.0984706136794386, 0.0894185657243129, 0.0810724181216677, 0.0733915807625995, 0.0663384461579859, 0.0598781159863707, 0.0539781578442059,
    0.0486083882911316, 0.0437373330511146, 0.0393229695406371, 0.0353240987411619, 0.0317034445117801, 0.0284272153221808, 0.0254647238733285, 0.0227880556511908, 0.0203717790604077, 0.0181926910596145,
    0.0162295932432360, 0.0144630941418387, 0.0128754341866765, 0.0114503303359322, 0.0101728378150057, 0.00902922680011186, 0.00800687218838523, 0.00709415486039758, 0.00628037306181464, 0.00555566271730628,
    0.00491092564776083, 0.00433777522517762, 0.00382858617381395, 0.00337652538864193, 0.00297547478958152, 0.00261995369508530, 0.00230505051439257, 0.00202636249613307, 0.00177994246481535, 0.00156225163688919,
    0.00137011774112811, 0.00120069777918906, 0.00105144485543239, 0.000920078583646128, 0.000804558644792605, 0.000703061126353299, 0.000613957321970095, 0.000535794711233811, 0.000467279874773688, 0.000407263130174890,
    0.000354724700456040, 0.000308762228684552, 0.000268578998820779, 0.000233472107922766, 0.000202821534805516, 0.000176080503619378, 0.000152766994802780, 0.000132456257345164, 0.000114774196621564, 0.0000993915292610416,
    0.0000860186111205116, 0.0000744008568854185, 0.0000643146804615109, 0.0000555638944463892, 0.0000479765148133912, 0.0000414019237006278, 0.0000357083490382522, 0.0000307806248038908, 0.0000265182000840266, 0.0000228333689341654,
    0.0000196496963539553, 0.0000169006186225834, 0.0000145282003166539, 0.0000124820385512393, 0.0000107183044508680, 9.19890566611241e-6, 7.89075437420041e-6, 6.76512728089460e-6, 5.79710594495074e-6, 4.96508729255373e-6,
    4.25035551717139e-6, 3.63670770345000e-6, 3.11012649979137e-6, 2.65849401629250e-6, 2.27134186228307e-6, 1.93963287719169e-6, 1.65557066379923e-6, 1.41243351587104e-6, 1.20442975270958e-6, 1.02657183986121e-6,
    8.74566995329392e-7, 7.44722260394541e-7, 6.33862255545582e-7, 5.39258025342825e-7, 4.58565512804405e-7, 3.89772368391109e-7, 3.31151972577348e-7, 2.81223703587451e-7, 2.38718612981323e-7, 2.02549784558224e-7,
    1.71786749203399e-7, 1.45633412099219e-7, 1.23409021080502e-7, 1.04531767460094e-7, 8.85046647687321e-8, 7.49033977199179e-8, 6.33658743306062e-8, 5.35832493603539e-8, 4.52922178102003e-8, 3.82684037781748e-8,
    3.23206930422610e-8, 2.72863777994286e-8, 2.30269994373198e-8, 1.94247904820595e-8, 1.63796304411581e-8, 1.38064422807221e-8, 1.16329666668818e-8, 9.79786000820215e-9, 8.24906997200364e-9, 6.94244869879648e-9,
    5.84056956293623e-9, 4.91171815795476e-9, 4.12903233557698e-9, 3.46976969515950e-9, 2.91468398787199e-9, 2.44749453802384e-9, 2.05443505293307e-9, 1.72387014435469e-9, 1.44596956306737e-9, 1.21243159178189e-9,
    1.01624828273784e-9, 8.51506293255724e-10, 7.13217989231916e-10, 5.97178273686798e-10, 4.99843271868294e-10, 4.18227580146182e-10, 3.49817276438660e-10, 2.92496307733140e-10, 2.44484226227652e-10, 2.04283548915435e-10,
    1.70635273863534e-10, 1.42481306624186e-10, 1.18932737801671e-10, 9.92430725748863e-11, 8.27856490334434e-11, 6.90345980053579e-11, 5.75487956079478e-11, 4.79583435743883e-11, 3.99531836601083e-11, 3.32735129630055e-11,
    2.77017183772596e-11, 2.30555919904645e-11, 1.91826261797451e-11, 1.59552184492373e-11, 1.32666425229607e-11, 1.10276645918872e-11, 9.16370253824348e-12, 7.61244195636034e-12, 6.32183630823821e-12, 5.24842997441282e-12,
    4.35595260905192e-12, 3.61414135533970e-12, 2.99775435412426e-12, 2.48574478117179e-12, 2.06056954190735e-12, 1.70761087761789e-12, 1.41469261268532e-12, 1.17167569925493e-12, 9.70120179176324e-13, 8.03002755355921e-13,
    6.64480907032201e-13, 5.49695947730361e-13, 4.54608654601190e-13, 3.75862130571052e-13, 3.10667427553834e-13, 2.56708186340823e-13, 2.12061158957008e-13, 1.75129990979628e-13, 1.44590070306053e-13, 1.19342608376890e-13,
    9.84764210448520e-14, 8.12361284968988e-14, 6.69957047626884e-14, 5.52364839983536e-14, 4.55288784872365e-14, 3.75171868260434e-14, 3.09069739955730e-14, 2.54545912496319e-14, 2.09584757642051e-14, 1.72519300955857e-14,
    1.41971316501794e-14, 1.16801642038076e-14, 9.60689839298851e-15, 7.89957718055663e-15, 6.49398653148027e-15, 5.33711172323687e-15, 4.38519652833446e-15, 3.60213650413600e-15, 2.95814927457727e-15, 2.42867438017647e-15,
    1.99346333303212e-15, 1.63582721456795e-15, 1.34201472284939e-15, 1.10069820297832e-15, 9.02549036511458e-16, 7.39886955899583e-16, 6.06390497499970e-16, 4.96858003320228e-16, 4.07010403543137e-16, 3.33328522514641e-16,
    2.72918903047290e-16, 2.23403181509686e-16, 1.82826905742816e-16, 1.49584399704446e-16, 1.22356868095946e-16, 1.00061422004550e-16, 8.18091101788785e-17, 6.68703743742468e-17, 5.46466232309370e-17, 4.46468473170557e-17,
    3.64683865173660e-17, 2.97811167122010e-17, 2.43144513286369e-17, 1.98466595514452e-17, 1.61960906400940e-17, 1.32139661280568e-17, 1.07784613453433e-17, 8.78984690826589e-18, 7.16650138491662e-18, 5.84163977794677e-18,
    4.76063001400521e-18, 3.87879232126172e-18, 3.15959506343337e-18, 2.57317598320038e-18, 2.09513046990837e-18, 1.70551888483764e-18, 1.38805354722395e-18, 1.12943303162933e-18, 9.18797221060242e-19, 7.47281322095490e-19,
    6.07650960951011e-19, 4.94003693444398e-19, 4.01524901266115e-19, 3.26288213964971e-19, 2.65092374707276e-19, 2.15327927385602e-19, 1.74868299982827e-19, 1.41980841083036e-19, 1.15254171584394e-19, 9.35388736783942e-20,
    7.58990800429806e-20, 6.15729693405857e-20, 4.99405370840484e-20, 4.04973081615272e-20, 3.28329006413784e-20, 2.66135496324475e-20, 2.15678629328980e-20, 1.74752135068077e-20, 1.41562828504629e-20, 1.14653584509271e-20,
    9.28406140589761e-21, 7.51623982263034e-21, 6.08381226695129e-21, 4.92338527497562e-21, 3.98350139454904e-21, 3.22240072043320e-21, 2.60620051521272e-21, 2.10741515728752e-21, 1.70375305656048e-21, 1.37713892323882e-21,
    2.2354265870871718e-27]


def rho(x):
    """Dickman's "rho" function."""
    if x <= 1:
        return 1
    if x < 2:
        return 1 - math.log(x)
    x = (x - 2) * 20
    pos = int(x)

    return rhotab[-1] if pos + 1 >= len(rhotab) else rhotab[pos] + (
        x - pos) * (rhotab[pos + 1] - rhotab[pos])


def integral(a, b, f, STEPS=20):
    """Computes the integral of f(x) from a to b."""
    w = b - a
    # assert(w >= 0)
    if not w:
        return 0
    step = w / STEPS
    return step * sum(f(a + step * (0.5 + i)) for i in range(STEPS))


def p_first_stage(alpha):
    """Probability of first stage success."""
    return rho(alpha)


def p_second_stage(alpha, beta):
    """Probability of second stage success."""
    return integral(alpha - beta, alpha - 1, lambda t: rho(t) / (alpha - t))


def primepi(n):
    """Approximation of the number of primes <= n."""
    return n / (math.log(n) - 1.06)


def n_primes_between(B1, B2):
    """Returns the number of primes between B1 and B2, inclusive."""
    # assert(B2 >= B1)
    return primepi(B2) - primepi(B1)


def work_for_bounds(B1, B2, factorB1=1.2, factorB2=1.35):
    """Returns work for stage-1, stage-2 in the negative (no factor found) case."""
    return (B1 * 1.442 * factorB1, n_primes_between(B1, B2) * 0.85 * factorB2)


# steps of approx 10%
nice_step = [i for j in (range(10, 20), range(20, 40, 2), range(
    40, 80, 5), range(80, 100, 10)) for i in j]


def next_nice_number(value):
    """Use nice round values for bounds."""
    ret = 1
    while value >= nice_step[-1]:
        value //= 10
        ret *= 10
    for n in nice_step:
        if n > value:
            return n * ret
    return None


def pm1(exponent, factoredTo, B1, B2):
    """Returns the probability of PM1(B1,B2) success for a finding a smooth factor using B1, B2 and already TFed to factoredUpTo."""
    takeAwayBits = log2(exponent) + 1

    SLICE_WIDTH = 0.25
    MIDDLE_SHIFT = log2(1 + 2**SLICE_WIDTH) - 1

    B2 = max(B1, B2)
    bitsB1 = log2(B1)
    bitsB2 = log2(B2)

    alpha = (factoredTo + MIDDLE_SHIFT - takeAwayBits) / bitsB1
    alphaStep = SLICE_WIDTH / bitsB1
    beta = bitsB2 / bitsB1

    sum1 = 0
    sum2 = 0
    invSliceProb = factoredTo / SLICE_WIDTH + 0.5
    p = 1

    while p >= 1e-8:
        p1 = p_first_stage(alpha) / invSliceProb
        p2 = p_second_stage(alpha, beta) / invSliceProb
        sum1 += p1
        sum2 += p2
        p = p1 + p2
        alpha += alphaStep
        invSliceProb += 1

    return (-expm1(-sum1), -expm1(-sum2))


def gain(exponent, factoredTo, B1, B2):
    """Returns tuple (benefit, work) expressed as a ratio of one PRP test."""
    (p1, p2) = pm1(exponent, factoredTo, B1, B2)
    (w1, w2) = work_for_bounds(B1, B2)
    p = p1 + p2
    w = (w1 + (1 - p1 - p2 / 4) * w2) * (1 / exponent)
    return (p, w)


def walk(exponent, factoredTo):
    # B1 = next_nice_number(int(exponent / 1000))
    # B2 = next_nice_number(int(exponent / 100))

    # Changes by James Heinrich for mersenne.ca
    B1mult = (60 - log2(exponent)) / 10000
    B1 = next_nice_number(int(B1mult * exponent))

    B2mult = 4 + (log2(exponent) - 20) * 8
    B2 = next_nice_number(int(B1 * B2mult))
    # End of changes by James Heinrich

    smallB1 = smallB2 = 0
    midB1 = midB2 = 0

    (p, w) = gain(exponent, factoredTo, B1, B2)

    while True:
        stepB1 = next_nice_number(B1) - B1
        stepB2 = next_nice_number(B2) - B2
        (p1, w1) = gain(exponent, factoredTo, B1 + stepB1, B2)
        (p2, w2) = gain(exponent, factoredTo, B1, B2 + stepB2)

        # assert(w1 > w and w2 > w and p1 >= p and p2 >= p)
        r1 = (p1 - p) / (w1 - w)
        r2 = (p2 - p) / (w2 - w)

        if r1 < 1 and r2 < 1 and not smallB1:
            smallB1 = B1
            smallB2 = B2

        if r1 < .5 and r2 < .5 and not midB1:
            midB1 = B1
            midB2 = B2

        if r1 < 1 and r2 < 1 and p1 <= w1 and p2 <= w2:
            break

        if r1 > r2:
            B1 += stepB1
            p = p1
            w = w1
        else:
            B2 += stepB2
            p = p2
            w = w2

    if not smallB1:
        if midB1:
            smallB1 = midB1
            smallB2 = midB2
        else:
            smallB1 = B1
            smallB2 = B2

    if not midB1:
        midB1 = B1
        midB2 = B2

    return ((smallB1, smallB2), (midB1, midB2), (B1, B2))


# End of Mihai Preda's script


def parse_stat_file(adir, p, last_time):
    """Parse the stat file for the progress of the assignment."""
    # Mlucas
    modified = True
    statfile = os.path.join(adir, "p{0}.stat".format(p))
    if not os.path.exists(statfile):
        logging.debug("stat file {0!r} does not exist".format(statfile))
        return 0, None, None, modified, 0, 0
    if last_time is not None:
        mtime = os.path.getmtime(statfile)
        if last_time >= mtime:
            logging.info("stat file {0!r} has not been modified since the last progress update ({1:%c})".format(
                statfile, datetime.fromtimestamp(mtime)))
            modified = False

    w = readonly_list_file(statfile)  # appended line by line, no lock needed
    found = 0
    regex = re.compile(
        r"(Iter#|S1|S2)(?: bit| at q)? = ([0-9]+) \[ ?([0-9]+\.[0-9]+)% complete\] .*\[ *([0-9]+\.[0-9]+) (m?sec)/iter\]")
    fft_regex = re.compile(r"FFT length [0-9]{3,}K = ([0-9]{6,})")
    s2_regex = re.compile(r"Stage 2 q0 = ([0-9]+)")
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
            s2 = int((iteration - int(s2_res.group(1))) / (percent / 100) / 20)
            iteration = int(s2 * (percent / 100))
        elif fft_res and not fftlen:
            fftlen = int(fft_res.group(1))
        if found == 5 and fftlen:
            break
    if not found:
        # iteration is 0, but don't know the estimated speed yet
        return 0, None, fftlen, modified, bits, s2
    # take the median of the last grepped lines
    msec_per_iter = median_low(list_msec_per_iter)
    return iteration, msec_per_iter, fftlen, modified, bits, s2


def parse_cuda_output_file(adir, p, last_time):
    """Parse the CUDALucas output file for the progress of the assignment."""
    # CUDALucas
    modified = True
    # appended line by line, no lock needed
    gpu = os.path.join(adir, options.cudalucas)
    if not os.path.exists(gpu):
        logging.debug("CUDALucas file {0!r} does not exist".format(gpu))
        return 0, None, None, modified
    if last_time is not None:
        mtime = os.path.getmtime(gpu)
        if last_time >= mtime:
            logging.info("CUDALucas file {0!r} has not been modified since the last progress update ({1:%c})".format(
                gpu, datetime.fromtimestamp(mtime)))
            modified = False

    w = readonly_list_file(gpu)
    found = 0
    num_regex = re.compile(r"\bM([0-9]{7,})\b")
    iter_regex = re.compile(r"\b[0-9]{5,}\b")
    ms_per_regex = re.compile(r"\b[0-9]+\.[0-9]{1,5}\b")
    eta_regex = re.compile(
        r"\b(?:(?:([0-9]+):)?([0-9]{1,2}):)?([0-9]{1,2}):([0-9]{2})\b")
    fft_regex = re.compile(r"\b([0-9]{3,})K\b")
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
                if not found:
                    logging.debug(
                        "Looking for the exponent {0}, but found {1}".format(p, num_res[0]))
                break
            found += 1
            # keep the last iteration to compute the percent of progress
            if found == 1:
                iteration = int(iter_res[0])
                eta = eta_res[1]
                time_left = int(eta[3]) + int(eta[2]) * 60
                if eta[1]:
                    time_left += int(eta[1]) * 60 * 60
                if eta[0]:
                    time_left += int(eta[0]) * 60 * 60 * 24
                avg_msec_per_iter = time_left * 1000 / (p - iteration)
                fftlen = int(fft_res[0]) * 1024  # << 10
            elif int(iter_res[0]) > iteration:
                break
            list_msec_per_iter.append(float(ms_res[1]))
            if found == 5:
                break
    if not found:
        # iteration is 0, but don't know the estimated speed yet
        return 0, None, fftlen, modified
    # take the median of the last grepped lines
    msec_per_iter = median_low(list_msec_per_iter)
    logging.debug("Current {0:.6n} msec/iter estimation, Average {1:.6n} msec/iter".format(
        msec_per_iter, avg_msec_per_iter))
    return iteration, avg_msec_per_iter, fftlen, modified


def parse_gpu_log_file(adir, p, last_time):
    """Parse the gpuowl log file for the progress of the assignment."""
    # GpuOwl
    modified = True
    # appended line by line, no lock needed
    gpuowl = os.path.join(adir, "gpuowl.log")
    if not os.path.exists(gpuowl):
        logging.debug("Log file {0!r} does not exist".format(gpuowl))
        return 0, None, None, modified, 0, 0
    if last_time is not None:
        mtime = os.path.getmtime(gpuowl)
        if last_time >= mtime:
            logging.info("Log file {0!r} has not been modified since the last progress update ({1:%c})".format(
                gpuowl, datetime.fromtimestamp(mtime)))
            modified = False

    w = readonly_list_file(gpuowl)
    found = 0
    regex = re.compile(r"([0-9]{7,}) (LL|P1|OK|EE)? +([0-9]{5,})")
    us_per_regex = re.compile(r"\b([0-9]+) us/it;?\b")
    fft_regex = re.compile(r"\b[0-9]{7,} FFT: ([0-9]+(?:\.[0-9]+)?[KM])\b")
    bits_regex = re.compile(
        r"\b[0-9]{7,} P1(?: B1=[0-9]+, B2=[0-9]+;|\([0-9]+(?:\.[0-9])?M?\)) ([0-9]+) bits;?\b")
    blocks_regex = re.compile(
        r"[0-9]{7,} P2\([0-9]+(?:\.[0-9])?M?,[0-9]+(?:\.[0-9])?M?\) ([0-9]+) blocks: ([0-9]+) - ([0-9]+);")
    p1_regex = re.compile(r"\| P1\([0-9]+(?:\.[0-9])?M?\)")
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
            if not found:
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
                p1 = res.group(2) == "P1"
            elif int(res.group(3)) > iteration:
                break
            if not p1 and not (p2 or buffs):
                p1_res = re.findall(p1_regex, line)
                p1 = res.group(2) == "OK" and bool(p1_res)
            if len(list_usec_per_iter) < 5:
                list_usec_per_iter.append(int(us_res[0]))
        elif p2 and blocks_res:
            if not buffs:
                buffs = int(blocks_res.group(1))
                iteration -= int(blocks_res.group(2))
        elif p1 and bits_res:
            if not bits:
                bits = int(bits_res[0])
                iteration = min(iteration, bits)
        elif fft_res and not fftlen:
            unit = fft_res[0][-1:]
            fftlen = int(float(
                fft_res[0][: -1]) * (1024 if unit == "K" else 1024 * 1024 if unit == "M" else 1))
        if (buffs or (found == 20 and not p2 and (not p1 or bits))) and fftlen:
            break
    if not found:
        # iteration is 0, but don't know the estimated speed yet
        return 0, None, fftlen, modified, bits, buffs
    # take the median of the last grepped lines
    msec_per_iter = median_low(list_usec_per_iter) / \
        1000 if list_usec_per_iter else None
    return iteration, msec_per_iter, fftlen, modified, bits, buffs


def get_progress_assignment(adir, assignment, last_time):
    """Get the progress of an assignment."""
    if not assignment:
        return None
    # P-1 Stage 1 bits
    bits = 0
    # P-1 Stage 2 location/buffers/blocks
    s2 = 0
    if options.gpuowl:  # GpuOwl
        result = parse_gpu_log_file(adir, assignment.n, last_time)
    elif options.cudalucas:  # CUDALucas
        result = parse_cuda_output_file(
            adir, assignment.n, last_time) + (bits, s2)
    else:  # Mlucas
        result = parse_stat_file(adir, assignment.n, last_time)
    return result


def compute_progress(assignment, iteration, msec_per_iter, p, bits, s2):
    """Computes the progress of a given assignment."""
    percent = iteration / (s2 if s2 else bits if bits else assignment.n if assignment.work_type ==
                           PRIMENET.WORK_TYPE_PRP else assignment.n - 2)
    if msec_per_iter is None:
        return percent, None, msec_per_iter
    if assignment.n != p:
        msec_per_iter *= assignment.n * \
            log2(assignment.n) * log2(log2(assignment.n)) / \
            (p * log2(p) * log2(log2(p)))
    if bits:
        time_left = msec_per_iter * (bits - iteration)
        # 1.5 suggested by EWM for Mlucas v20.0 and 1.13-1.275 for v20.1
        time_left += msec_per_iter * bits * 1.2
        if assignment.work_type in {PRIMENET.WORK_TYPE_FIRST_LL,
                                    PRIMENET.WORK_TYPE_DBLCHK, PRIMENET.WORK_TYPE_PRP}:
            time_left += msec_per_iter * assignment.n
    elif s2:
        time_left = msec_per_iter * \
            (s2 - iteration) if not options.gpuowl else options.timeout
        if assignment.work_type in {PRIMENET.WORK_TYPE_FIRST_LL,
                                    PRIMENET.WORK_TYPE_DBLCHK, PRIMENET.WORK_TYPE_PRP}:
            time_left += msec_per_iter * assignment.n
    else:
        time_left = msec_per_iter * ((assignment.n if assignment.work_type ==
                                     PRIMENET.WORK_TYPE_PRP else assignment.n - 2) - iteration)
    rolling_average = 1000
    if config.has_option(section, "RollingAverage"):
        rolling_average = config.getint(section, "RollingAverage")
    time_left *= (24 / options.cpu_hours) * (1000 / rolling_average)
    return percent, time_left / 1000, msec_per_iter


def output_status(dirs):
    logging.info(
        "Below is a report on the work you have queued and any expected completion dates.")
    ll_and_prp_cnt = 0
    prob = 0.0
    for i, adir in enumerate(dirs):
        if options.status and options.num_worker_threads > 1:
            logging.info("[Worker #{0:n}]".format(i + 1))
        tasks = read_workfile(adir)
        if not tasks:
            logging.info("No work queued up.")
            continue
        assignments = OrderedDict(((assignment.uid, assignment.n), assignment)
                                  for assignment in tasks if isinstance(assignment, Assignment)).values()
        msec_per_iter = p = None
        if config.has_option(section, "msec_per_iter") and config.has_option(
                section, "exponent"):
            msec_per_iter = config.getfloat(section, "msec_per_iter")
            p = config.getint(section, "exponent")
        cur_time_left = 0
        mersennes = True
        now = datetime.now()
        for assignment in assignments:
            iteration, _, _, _, bits, s2 = get_progress_assignment(
                adir, assignment, None)
            if not assignment:
                continue
            _, time_left, _ = compute_progress(
                assignment, iteration, msec_per_iter, p, bits, s2)
            bits = int(assignment.sieve_depth)
            bits = max(bits, 32)
            all_and_prp_cnt = False
            aprob = 0.0
            if assignment.work_type == PRIMENET.WORK_TYPE_FIRST_LL:
                work_type_str = "Lucas-Lehmer test"
                all_and_prp_cnt = True
                aprob += (bits - 1) * 1.733 * (1.04 if assignment.pminus1ed else 1.0) / (
                    log2(assignment.k) + log2(assignment.b) * assignment.n)
            elif assignment.work_type == PRIMENET.WORK_TYPE_DBLCHK:
                work_type_str = "Double-check"
                all_and_prp_cnt = True
                aprob += (bits - 1) * 1.733 * ERROR_RATE * (1.04 if assignment.pminus1ed else 1.0) / (
                    log2(assignment.k) + log2(assignment.b) * assignment.n)
            elif assignment.work_type == PRIMENET.WORK_TYPE_PRP:
                all_and_prp_cnt = True
                if not assignment.prp_dblchk:
                    work_type_str = "PRP"
                    aprob += (bits - 1) * 1.733 * (1.04 if assignment.pminus1ed else 1.0) / (
                        log2(assignment.k) + log2(assignment.b) * assignment.n)
                else:
                    work_type_str = "PRPDC"
                    aprob += (bits - 1) * 1.733 * PRP_ERROR_RATE * (1.04 if assignment.pminus1ed else 1.0) / (
                        log2(assignment.k) + log2(assignment.b) * assignment.n)
            elif assignment.work_type == PRIMENET.WORK_TYPE_PMINUS1:
                work_type_str = "P-1 B1={0:.0f}".format(assignment.B1)
            elif assignment.work_type == PRIMENET.WORK_TYPE_PFACTOR:
                work_type_str = "P-1"
            elif assignment.work_type == PRIMENET.WORK_TYPE_CERT:
                work_type_str = "Certify"
            prob += aprob
            if assignment.k != 1.0 or assignment.b != 2 or assignment.c != -1 or assignment.known_factors is not None:
                amersennes = mersennes = False
            else:
                amersennes = True
            if time_left is None:
                logging.info("{0}, {1}, Finish cannot be estimated".format(
                    assignment_to_str(assignment), work_type_str))
            else:
                cur_time_left += time_left
                time_left = timedelta(seconds=cur_time_left)
                logging.info("{0}, {1}, {2} ({3:%c})".format(
                    assignment_to_str(assignment), work_type_str, time_left, now + time_left))
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


def checksum_md5(filename):
    """Calculates the MD5 checksum of a file."""
    amd5 = md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(128 * amd5.block_size), b""):
            amd5.update(chunk)
    return amd5.hexdigest()


def upload_proof(filename):
    """Upload a file to the PrimeNet server."""
    try:
        with open(filename, "rb") as f:
            header = f.readline().rstrip()
            if header != b"PRP PROOF":
                return False
            header, _, version = f.readline().rstrip().partition(b"=")
            if header != b"VERSION" or int(version) not in {1, 2}:
                logging.error("Error getting version number from proof header")
                return False
            header, _, hashlen = f.readline().rstrip().partition(b"=")
            if header != b"HASHSIZE" or not 32 <= int(hashlen) <= 64:
                logging.error("Error getting hash size from proof header")
                return False
            header, _, power = f.readline().rstrip().partition(b"=")
            if header != b"POWER" or not 0 < int(power) < 16:
                logging.error("Error getting power from proof header")
                return False
            header = f.readline().rstrip()
            if header.startswith(b"x"):
                header = f.readline().rstrip()
            if header.startswith(b"BASE="):
                header = f.readline().rstrip()
            header, _, number = header.partition(b"=")
            if header != b"NUMBER" or not number.startswith(b"M"):
                logging.error("Error getting number from proof header")
                return False
    except (IOError, OSError):
        logging.error("Cannot open proof file {0!r}".format(filename))
        return False
    exponent = int(number[1:])
    logging.info("Proof file exponent is {0}".format(exponent))
    fileSize = os.path.getsize(filename)
    logging.info("Filesize of {0!r} is {1}B ({2}B)".format(
        filename, outputunit(fileSize, False), outputunit(fileSize, True)))
    fileHash = checksum_md5(filename)
    logging.info("MD5 of {0!r} is {1}".format(filename, fileHash))

    while True:
        args = {"UserID": options.user_id,
                "Exponent": exponent,
                "FileSize": fileSize,
                "FileMD5": fileHash}
        r = session.get(primenet_baseurl + "proof_upload/",
                        params=args, timeout=180)
        json = r.json()
        if "error_status" in json:
            if json["error_status"] == 409:
                logging.error("Proof {0!r} already uploaded".format(filename))
                logging.error(str(json))
                return True
            logging.error(
                "Unexpected error during {0!r} upload".format(filename))
            logging.error(str(json))
            return False
        r.raise_for_status()
        if "URLToUse" not in json:
            logging.error(
                "For proof {0!r}, server response missing URLToUse:".format(filename))
            logging.error(str(json))
            return False
        if "need" not in json:
            logging.error(
                "For proof {0!r}, server response missing need list:".format(filename))
            logging.error(str(json))
            return False

        origUrl = json["URLToUse"]
        baseUrl = "https" + \
            origUrl[4:] if origUrl.startswith("http:") else origUrl
        pos, end = next((int(a), b) for a, b in json["need"].items())
        if pos > end or end >= fileSize:
            logging.error(
                "For proof {0!r}, need list entry bad:".format(filename))
            logging.error(str(json))
            return False

        if pos:
            logging.info("Resuming from offset {0:n}".format(pos))

        with open(filename, "rb") as f:
            while pos < end:
                f.seek(pos)
                size = min(end - pos + 1, 5 * 1024 * 1024)
                chunk = f.read(size)
                args = {
                    "FileMD5": fileHash,
                    "DataOffset": pos,
                    "DataSize": len(chunk),
                    "DataMD5": md5(chunk).hexdigest()}
                response = session.post(baseUrl, params=args, files={
                                        "Data": (None, chunk)}, timeout=180)
                json = response.json()
                if "error_status" in json:
                    logging.error(
                        "Unexpected error during {0!r} upload".format(filename))
                    logging.error(str(json))
                    return False
                response.raise_for_status()
                if "FileUploaded" in json:
                    logging.info(
                        "Proof file {0!r} successfully uploaded".format(filename))
                    return True
                if "need" not in json:
                    logging.error(
                        "For proof {0!r}, no entries in need list:".format(filename))
                    logging.error(str(json))
                    return False
                start, end = next((int(a), b) for a, b in json["need"].items())
                if start <= pos:
                    logging.error(
                        "For proof {0!r}, sending data did not advance need list:".format(filename))
                    logging.error(str(json))
                    return False
                pos = start
                if pos > end or end >= fileSize:
                    logging.error(
                        "For proof {0!r}, need list entry bad:".format(filename))
                    logging.error(str(json))
                    return False


def upload_proofs(adir):
    """Uploads the proof file in the given directory to the server."""
    if config.has_option(section, "ProofUploads") and not config.getboolean(
            section, "ProofUploads"):
        return
    proof = os.path.join(adir, "proof")
    if not os.path.exists(proof) or not os.path.isdir(proof):
        logging.debug("Proof directory {0!r} does not exist".format(proof))
        return
    entries = os.listdir(proof)
    if not entries:
        logging.debug("No proof files to upload.")
        return
    if options.archive_dir:
        archive = os.path.join(adir, options.archive_dir)
        if not os.path.exists(archive):
            os.makedirs(archive)
    for entry in entries:
        if entry.endswith(".proof"):
            start_time = timeit.default_timer()
            filename = os.path.join(proof, entry)
            if upload_proof(filename):
                end_time = timeit.default_timer()
                logging.debug("Uploaded in {0}".format(
                    timedelta(seconds=end_time - start_time)))
                if options.archive_dir:
                    shutil.move(filename, os.path.join(archive, entry))
                else:
                    os.remove(filename)


def aupload_proofs(dirs):
    """Uploads any proof files found in the given directory."""
    for adir in dirs:
        upload_proofs(adir)


# TODO -- have people set their own program options for commented out portions
def program_options(first_time=False, retry_count=0):
    """Sets the program options on the PrimeNet server."""
    if retry_count >= 5:
        logging.info("Retry count exceeded.")
        return None
    guid = get_guid(config)
    args = primenet_v5_bargs.copy()
    args["t"] = "po"
    args["g"] = guid
    # no value updates all cpu threads with given worktype
    args["c"] = ""  # cpu_num
    if first_time:
        args["w"] = work_preference
        args["nw"] = options.num_worker_threads
        # args["Priority"] = 1
        args["DaysOfWork"] = int(round(options.days_of_work))
        args["DayMemory"] = options.day_night_memory
        args["NightMemory"] = options.day_night_memory
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
        if rc == PRIMENET.ERROR_OK:
            pass
        else:
            if rc == PRIMENET.ERROR_UNREGISTERED_CPU:
                register_instance()
                retry = True
            elif rc == PRIMENET.ERROR_STALE_CPU_INFO:
                register_instance(guid)
                retry = True
            if not retry:
                parser.error(
                    "Error while setting program options on mersenne.org")
    if retry:
        return program_options(first_time, retry_count + 1)
    if "w" in result:
        w = int(result["w"])
        if w not in supported:
            logging.error("Unsupported worktype = {0} for {1}".format(
                w, PROGRAM["name"]))
            sys.exit(1)
        config.set(section, "WorkPreference", result["w"])
    if "nw" in result:
        config.set(section, "WorkerThreads", result["nw"])
    if "Priority" in result:
        config.set(section, "Priority", result["Priority"])
    if "DaysOfWork" in result:
        config.set(section, "DaysOfWork", result["DaysOfWork"])
    if "DayMemory" in result and "NightMemory" in result:
        config.set(section, "Memory", str(
            max(int(result[x]) for x in ("DayMemory", "NightMemory"))))
    if "RunOnBattery" in result:
        config.set(section, "RunOnBattery", result["RunOnBattery"])
    # if not config.has_option(section, "first_time"):
        # config.set(section, "first_time", "false")
    if first_time:
        config.set(section, "SrvrP00", str(config.getint(
            section, "SrvrP00") + 1 if config.has_option(section, "SrvrP00") else 0))
    else:
        config.set(section, "SrvrP00", result["od"])
    return None


def register_instance(guid=None):
    """Register the computer with the PrimeNet server."""
    # register the instance to server, guid is the instance identifier
    hardware_id = md5((options.cpu_brand + str(uuid.getnode())
                       ).encode("utf-8")).hexdigest()  # similar as MPrime
    if config.has_option(section, "HardwareGUID"):
        hardware_id = config.get(section, "HardwareGUID")
    else:
        config.set(section, "HardwareGUID", hardware_id)
    args = primenet_v5_bargs.copy()
    args["t"] = "uc"					# update compute command
    if guid is None:
        guid = create_new_guid()
    args["g"] = guid
    args["hg"] = hardware_id			# 32 hex char (128 bits)
    args["wg"] = ""						# only filled on Windows by MPrime
    args["a"] = generate_application_str()
    if config.has_option(section, "sw_version"):
        args["a"] = config.get(section, "sw_version")
    args["c"] = options.cpu_brand  # CPU model (len between 8 and 64)
    args["f"] = options.cpu_features  # CPU option (like asimd, max len 64)
    args["L1"] = options.cpu_l1_cache_size				# L1 cache size in KBytes
    args["L2"] = options.cpu_l2_cache_size				# L2 cache size in KBytes
    # if smaller or equal to 256,
    # server refuses to gives LL assignment
    args["np"] = options.num_cores				# number of cores
    args["hp"] = options.cpu_hyperthreads				# number of hyperthreading cores
    args["m"] = options.memory			# number of megabytes of physical memory
    args["s"] = options.cpu_speed		# CPU frequency
    args["h"] = options.cpu_hours
    args["r"] = 0						# pretend to run at 100%
    if config.has_option(section, "RollingAverage"):
        args["r"] = config.get(section, "RollingAverage")
    if options.cpu_l3_cache_size:
        args["L3"] = options.cpu_l3_cache_size
    if options.user_id:
        args["u"] = options.user_id		#
    if options.computer_id:
        args["cn"] = options.computer_id  # truncate to 20 char max
    logging.info("Updating computer information on the server")
    result = send_request(guid, args)
    if result is None:
        parser.error("Error while registering on mersenne.org")
    else:
        rc = int(result["pnErrorResult"])
        if rc == PRIMENET.ERROR_OK:
            pass
        else:
            parser.error("Error while registering on mersenne.org")
    # Save program options in case they are changed by the PrimeNet server.
    config.set(section, "username", result["u"])
    config.set(section, "ComputerID", result["cn"])
    config.set(section, "user_name", result["un"])
    options_counter = int(result["od"])
    guid = result["g"]
    config_write(config, guid)
    # if options_counter == 1:
    # program_options()
    program_options(True)
    if options_counter > config.getint(section, "SrvrP00"):
        program_options()
    merge_config_and_options(config, options)
    config_write(config)
    logging.info("GUID {guid} correctly registered with the following features:".format(
        guid=guid))
    logging.info("Username: {0}".format(options.user_id))
    logging.info("Computer name: {0}".format(options.computer_id))
    logging.info("CPU model: {0}".format(options.cpu_brand))
    logging.info("CPU features: {0}".format(options.cpu_features))
    logging.info("CPU L1 Cache size: {0:n} KIB".format(
        options.cpu_l1_cache_size))
    logging.info("CPU L2 Cache size: {0:n} KiB".format(
        options.cpu_l2_cache_size))
    logging.info("CPU cores: {0:n}".format(options.num_cores))
    logging.info("CPU threads per core: {0:n}".format(
        options.cpu_hyperthreads))
    logging.info("CPU frequency/speed: {0:n} MHz".format(options.cpu_speed))
    logging.info("Total RAM: {0:n} MiB".format(options.memory))
    logging.info("To change these values, please rerun the script with different options or edit the {0!r} file".format(
        options.localfile))
    logging.info("You can see the result in this page:")
    logging.info(
        "https://www.mersenne.org/editcpu/?g={guid}".format(guid=guid))


def assignment_unreserve(assignment, retry_count=0):
    """Unreserves an assignment from the PrimeNet server."""
    guid = get_guid(config)
    if guid is None:
        logging.error("Cannot unreserve, the registration is not done")
        return False
    if not assignment or not assignment.uid:
        return True
    if retry_count >= 5:
        logging.info("Retry count exceeded.")
        return False
    args = primenet_v5_bargs.copy()
    args["t"] = "au"
    args["g"] = guid
    args["k"] = assignment.uid
    retry = False
    logging.info("Unreserving {0}".format(assignment_to_str(assignment)))
    result = send_request(guid, args)
    if result is None:
        retry = True
    else:
        rc = int(result["pnErrorResult"])
        if rc == PRIMENET.ERROR_OK:
            return True
        elif rc == PRIMENET.ERROR_INVALID_ASSIGNMENT_KEY:
            return True
        elif rc == PRIMENET.ERROR_UNREGISTERED_CPU:
            register_instance()
            retry = True
    if retry:
        return assignment_unreserve(assignment, retry_count + 1)
    return False


def unreserve(dirs, p):
    """Unreserve a specific exponent from the workfile."""
    for adir in dirs:
        tasks = read_workfile(adir)
        found = changed = False
        for assignment in tasks:
            if isinstance(assignment, Assignment) and assignment.n == p:
                if assignment_unreserve(assignment):
                    tasks = (task for task in tasks if not isinstance(task, Assignment) or (
                        task.uid != assignment.uid if assignment.uid else task.n != assignment.n))
                    changed = True
                found = True
                break
        if found:
            if changed:
                write_workfile(adir, tasks)
            break
    else:
        logging.error("Error unreserving exponent: {0} not found in workfile{1}".format(
            p, "s" if len(dirs) > 1 else ""))


def unreserve_all(dirs):
    """Unreserves all assignments in the given directories."""
    logging.info("Quitting GIMPS immediately.")
    for i, adir in enumerate(dirs):
        if options.dirs:
            logging.info("[Worker #{0:n}]".format(i + 1))
        tasks = read_workfile(adir)
        assignments = OrderedDict(((assignment.uid, assignment.n), assignment)
                                  for assignment in tasks if isinstance(assignment, Assignment)).values()
        changed = False
        for assignment in assignments:
            if assignment_unreserve(assignment):
                tasks = [task for task in tasks if not isinstance(task, Assignment) or (
                    task.uid != assignment.uid if assignment.uid else task.n != assignment.n)]
                changed = True
        if changed:
            write_workfile(adir, tasks)


def update_assignment(assignment, task):
    changed = False
    if assignment.work_type == PRIMENET.WORK_TYPE_PRP and (options.convert_prp_to_ll or (
            not assignment.prp_dblchk and int(options.work_preference) in option_dict)):
        logging.info("Converting from PRP to LL")
        assignment.work_type = PRIMENET.WORK_TYPE_DBLCHK if assignment.prp_dblchk else PRIMENET.WORK_TYPE_FIRST_LL
        assignment.pminus1ed = int(not assignment.tests_saved)
        changed = True
    if assignment.work_type in {PRIMENET.WORK_TYPE_FIRST_LL,
                                PRIMENET.WORK_TYPE_DBLCHK} and options.convert_ll_to_prp:
        logging.info("Converting from LL to PRP")
        assignment.tests_saved = float(not assignment.pminus1ed)
        assignment.prp_dblchk = assignment.work_type == PRIMENET.WORK_TYPE_DBLCHK
        assignment.work_type = PRIMENET.WORK_TYPE_PRP
        changed = True
    if options.tests_saved is not None and assignment.work_type in {
            PRIMENET.WORK_TYPE_FIRST_LL, PRIMENET.WORK_TYPE_DBLCHK, PRIMENET.WORK_TYPE_PRP}:
        redo = False
        tests_saved = float(options.tests_saved)
        if tests_saved and options.pm1_multiplier is not None and ((assignment.work_type in {PRIMENET.WORK_TYPE_FIRST_LL, PRIMENET.WORK_TYPE_DBLCHK} and assignment.pminus1ed) or (
                assignment.work_type == PRIMENET.WORK_TYPE_PRP and not assignment.tests_saved)):
            json = get_exponent(assignment.n)
            if json is not None:
                result = json["results"][0]
                bound1 = result["Pm1_bound1"]
                bound2 = result["Pm1_bound2"]
                if result["exponent"] == assignment.n and bound1 and bound2:
                    logging.debug(
                        "Existing bounds are B1={0:n}, B2={1:n}".format(bound1, bound2))
                    prob1, prob2 = pm1(
                        assignment.n, assignment.sieve_depth, bound1, bound2)
                    logging.debug(
                        "Chance of finding a factor was an estimated {0:%} ({1:.3%} + {2:.3%})".format(prob1 + prob2, prob1, prob2))
                    _, (midB1, midB2), _ = walk(
                        assignment.n, assignment.sieve_depth)
                    logging.debug(
                        "Optimal bounds are B1={0:n}, B2={1:n}".format(midB1, midB2))
                    p1, p2 = pm1(
                        assignment.n, assignment.sieve_depth, midB1, midB2)
                    logging.debug("Chance of finding a factor is an estimated {0:%} ({1:.3%} + {2:.3%}) or a difference of {3:%} ({4:.3%} + {5:.3%})".format(
                        p1 + p2, p1, p2, p1 + p2 - (prob1 + prob2), p1 - prob1, p2 - prob2))
                    pm1_multiplier = float(options.pm1_multiplier)
                    if bound2 < midB2 * pm1_multiplier:
                        logging.info(
                            "Existing B2={0:n} < {1:n}, redoing P-1".format(bound2, midB2 * pm1_multiplier))
                        redo = True
        else:
            redo = True
        if redo:
            if assignment.work_type in {
                    PRIMENET.WORK_TYPE_FIRST_LL, PRIMENET.WORK_TYPE_DBLCHK}:
                assignment.pminus1ed = int(not tests_saved)
            elif assignment.work_type == PRIMENET.WORK_TYPE_PRP:
                assignment.tests_saved = tests_saved
            changed = True
    if changed:
        logging.debug("Original assignment: {0!r}".format(task))
        task = output_assignment(assignment)
    logging.debug("New assignment: {0!r}".format(task))
    return assignment, task


def get_assignment(cpu_num, assignment_num=None, retry_count=0):
    """Get an assignment from the server."""
    if retry_count >= 5:
        logging.info("Retry count exceeded.")
        return None
    guid = get_guid(config)
    args = primenet_v5_bargs.copy()
    args["t"] = "ga"			# transaction type
    args["g"] = guid
    args["c"] = cpu_num
    args["a"] = "" if assignment_num is None else assignment_num
    if assignment_num is None:
        if options.min_exp:
            args["min"] = options.min_exp
        if options.max_exp:
            args["max"] = options.max_exp
    logging.debug("Fetching using v5 API")
    supported = frozenset([PRIMENET.WORK_TYPE_FIRST_LL, PRIMENET.WORK_TYPE_DBLCHK,
                          PRIMENET.WORK_TYPE_PRP] + ([PRIMENET.WORK_TYPE_PFACTOR] if not options.cudalucas else []))
    retry = False
    if assignment_num != 0:
        logging.info("Getting assignment from server")
    r = send_request(guid, args)
    if r is None:
        retry = True
    else:
        rc = int(r["pnErrorResult"])
        if rc == PRIMENET.ERROR_OK:
            pass
        else:
            if rc == PRIMENET.ERROR_UNREGISTERED_CPU:
                register_instance()
                retry = True
            elif rc == PRIMENET.ERROR_STALE_CPU_INFO:
                register_instance(guid)
                retry = True
            elif rc == PRIMENET.ERROR_CPU_CONFIGURATION_MISMATCH:
                register_instance(guid)
                retry = True
            if not retry:
                return None
    if retry:
        return get_assignment(cpu_num, assignment_num, retry_count + 1)
    if assignment_num == 0:
        return int(r["a"])
    assignment = Assignment(int(r["w"]))
    assignment.uid = r["k"]
    assignment.n = int(r["n"])
    if assignment.n < 15000000 and assignment.work_type in {
            PRIMENET.WORK_TYPE_FACTOR, PRIMENET.WORK_TYPE_PFACTOR, PRIMENET.WORK_TYPE_FIRST_LL, PRIMENET.WORK_TYPE_DBLCHK}:
        logging.error("Server sent bad exponent: {0}.".format(assignment.n))
        return None
    if assignment.work_type not in supported:
        logging.error("Returned assignment from server is not a supported worktype {0} for {1}.".format(
            assignment.work_type, PROGRAM["name"]))
        # TODO: Unreserve assignment
        # assignment_unreserve()
        # return None
    if assignment.work_type == PRIMENET.WORK_TYPE_FIRST_LL:
        work_type_str = "LL"
        assignment.sieve_depth = float(r["sf"])
        assignment.pminus1ed = int(r["p1"])
        if options.gpuowl:  # GpuOwl
            logging.warning(
                "First time LL tests are not supported with the latest versions of GpuOwl")
    elif assignment.work_type == PRIMENET.WORK_TYPE_DBLCHK:
        work_type_str = "Double check"
        assignment.sieve_depth = float(r["sf"])
        assignment.pminus1ed = int(r["p1"])
        if options.gpuowl:  # GpuOwl
            logging.warning(
                "Double check LL tests are not supported with the latest versions of GpuOwl")
    elif assignment.work_type == PRIMENET.WORK_TYPE_PRP:
        assignment.prp_dblchk = "dc" in r
        work_type_str = "PRPDC" if assignment.prp_dblchk else "PRP"
        assignment.k = float(r["A"])
        assignment.b = int(r["b"])
        assignment.c = int(r["c"])
        if "sf" in r and "saved" in r:
            assignment.sieve_depth = float(r["sf"])
            assignment.tests_saved = float(r["saved"])
            if "base" in r and "rt" in r:
                assignment.prp_base = int(r["base"])
                assignment.prp_residue_type = int(r["rt"])
                # Mlucas
                if not (options.cudalucas or options.gpuowl) and (
                        assignment.prp_base != 3 or assignment.prp_residue_type not in (1, 5)):
                    logging.error(
                        "PRP base is not 3 or residue type is not 1 or 5")
                    # TODO: Unreserve assignment
                    # assignment_unreserve()
        if "kf" in r:
            assignment.known_factors = r["kf"]
    elif assignment.work_type == PRIMENET.WORK_TYPE_PFACTOR:
        work_type_str = "P-1"
        assignment.k = float(r["A"])
        assignment.b = int(r["b"])
        assignment.c = int(r["c"])
        assignment.sieve_depth = float(r["sf"])
        assignment.tests_saved = float(r["saved"])
    elif assignment.work_type == PRIMENET.WORK_TYPE_PMINUS1:
        work_type_str = "P-1"
        assignment.k = float(r["A"])
        assignment.b = int(r["b"])
        assignment.c = int(r["c"])
        assignment.B1 = int(r["B1"])
        assignment.B2 = int(r["B2"])
    elif assignment.work_type == PRIMENET.WORK_TYPE_CERT:
        work_type_str = "CERT"
        assignment.k = float(r["A"])
        assignment.b = int(r["b"])
        assignment.c = int(r["c"])
        # assignment.cert_squarings = int(r['ns'])
    else:
        logging.error("Received unknown worktype: {0}.".format(
            assignment.work_type))
        sys.exit(1)
    logging.info("Got assignment {0}: {1} {2}".format(
        assignment.uid, work_type_str, assignment_to_str(assignment)))
    return assignment


def recover_assignments(dirs):
    if guid is None:
        logging.error(
            "Cannot recover assignments, the registration is not done")
        return
    for i, adir in enumerate(dirs):
        if options.dirs:
            logging.info("[Worker #{0:n}]".format(i + 1))
        cpu_num = i if options.dirs else options.cpu
        num_to_get = get_assignment(cpu_num, 0)
        if num_to_get is None:
            logging.error(
                "Unable to determine the number of assignments to recover")
            return
        logging.info("Recovering {0:n} assignment{1}".format(
            num_to_get, "s" if num_to_get > 1 else ""))
        tests = []
        for j in range(1, num_to_get + 1):
            test = get_assignment(cpu_num, j)
            if test is None:
                return
            task = output_assignment(test)
            test, _ = update_assignment(test, task)
            tests.append(test)
        write_workfile(adir, tests)


def primenet_fetch(cpu_num, num_to_get):
    """Get a number of assignments from the PrimeNet server."""
    if options.password and not primenet_login:
        return []
    # As of early 2018, here is the full list of assignment-type codes supported by the Primenet server; Mlucas
    # v20 (and thus this script) supports only the subset of these indicated by an asterisk in the left column.
    # Supported assignment types may be specified via either their PrimeNet number code or the listed Mnemonic:
    # 			Worktype:
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

    # Get assignment (Loarer's way)
    if options.password:
        try:
            assignment = OrderedDict((
                ("cores", options.num_worker_threads),
                ("num_to_get", num_to_get),
                ("pref", work_preference),
                ("exp_lo", options.min_exp if options.min_exp else ""),
                ("exp_hi", options.max_exp if options.max_exp else ""),
                ("B1", "Get Assignments")
            ))
            logging.debug("Fetching using manual assignments")
            r = session.post(primenet_baseurl +
                             "manual_assignment/", data=assignment)
            r.raise_for_status()
            res = r.text
            BEGIN_MARK = "<!--BEGIN_ASSIGNMENTS_BLOCK-->"
            begin = res.find(BEGIN_MARK)
            if begin >= 0:
                begin += len(BEGIN_MARK)
                end = res.find("<!--END_ASSIGNMENTS_BLOCK-->", begin)
                if end >= 0:
                    tests = []
                    for task in res[begin:end].splitlines():
                        test = parse_assignment(task)
                        if test is None:
                            logging.error(
                                "Invalid assignment {0!r}".format(task))
                            tests.append(task)
                        else:
                            tests.append(test)

                    return tests
            return []
        except HTTPError:
            logging.exception("")
            return []
        except ConnectionError:
            logging.exception("URL open error at primenet_fetch")
            return []

    # Get assignment using v5 API
    else:
        tests = []
        for _ in range(num_to_get):
            test = get_assignment(cpu_num)
            if test is None:
                break
            tests.append(test)

        return tests


def get_assignments(adir, cpu_num, progress, tasks):
    """Get new assignments from the PrimeNet server."""
    if config.has_option(section, "NoMoreWork") and config.getboolean(
            section, "NoMoreWork"):
        return []
    workfile = os.path.join(adir, options.worktodo_file)
    assignments = OrderedDict(((assignment.uid, assignment.n), assignment)
                              for assignment in tasks if isinstance(assignment, Assignment)).values()
    percent = time_left = None
    if progress is not None:
        percent, time_left, _, _ = progress  # unpack update_progress output
    num_cache = options.num_cache + 1
    if options.password:
        num_cache += 1
    num_existing = len(assignments)
    num_cache = max(num_existing, num_cache)
    if time_left is not None:
        time_left = timedelta(seconds=time_left)
        days_work = timedelta(days=options.days_of_work)
        if time_left <= days_work:
            num_cache += 1
            logging.debug("Time left is {0} and smaller than days_of_work ({1}), so num_cache is increased by one to {2:n}".format(
                time_left, days_work, num_cache))
    amax = config.getint(section, "MaxExponents") if config.has_option(
        section, "MaxExponents") else 15
    num_cache = min(num_cache, amax)
    num_to_get = num_cache - num_existing

    if num_to_get <= 0:
        logging.debug("{0:n} ≥ {1:n} assignments already in {2!r}, not getting new work".format(
            num_existing, num_cache, workfile))
        return []
    logging.debug("Found {0:n} < {1:n} assignments in {2!r}, getting {3:n} new assignment{4}".format(
        num_existing, num_cache, workfile, num_to_get, "s" if num_to_get > 1 else ""))

    assignments = primenet_fetch(cpu_num, num_to_get)
    new_tasks = []
    num_fetched = len(assignments)
    if assignments:
        logging.debug("Fetched {0:n} assignment{1}:".format(
            num_fetched, "s" if num_fetched > 1 else ""))
        for i, assignment in enumerate(assignments):
            new_task = output_assignment(assignment)
            assignment, new_task = update_assignment(assignment, new_task)
            assignments[i] = assignment
            new_tasks.append(new_task)
        tasks += assignments
    write_list_file(workfile, new_tasks, "a")
    output_status([adir])
    if num_fetched < num_to_get:
        logging.error("Failed to get requested number of new assignments, {0:n} requested, {1:n} successfully retrieved".format(
            num_to_get, num_fetched))
    return assignments


def register_assignment(cpu_num, assignment, retry_count=0):
    """Register an assignment with the PrimeNet server."""
    if retry_count >= 5:
        logging.info("Retry count exceeded.")
        return None
    guid = get_guid(config)
    args = primenet_v5_bargs.copy()
    args["t"] = "ra"
    args["g"] = guid
    args["c"] = cpu_num
    args["w"] = assignment.work_type
    args["n"] = assignment.n
    if assignment.work_type in {
            PRIMENET.WORK_TYPE_FIRST_LL, PRIMENET.WORK_TYPE_DBLCHK}:
        work_type_str = "LL" if assignment.work_type == PRIMENET.WORK_TYPE_FIRST_LL else "Double check"
        args["sf"] = assignment.sieve_depth
        args["p1"] = assignment.pminus1ed
    elif assignment.work_type == PRIMENET.WORK_TYPE_PRP:
        work_type_str = "PRP"
        args["A"] = "{0:.0f}".format(assignment.k)
        args["b"] = assignment.b
        args["C"] = assignment.c
        args["sf"] = assignment.sieve_depth
        args["saved"] = assignment.tests_saved
    elif assignment.work_type == PRIMENET.WORK_TYPE_PFACTOR:
        work_type_str = "P-1"
        args["A"] = "{0:.0f}".format(assignment.k)
        args["b"] = assignment.b
        args["C"] = assignment.c
        args["sf"] = assignment.sieve_depth
        args["saved"] = assignment.tests_saved
    elif assignment.work_type == PRIMENET.WORK_TYPE_PMINUS1:
        work_type_str = "P-1"
        args["A"] = "{0:.0f}".format(assignment.k)
        args["b"] = assignment.b
        args["C"] = assignment.c
        args["B1"] = "{0:.0f}".format(assignment.B1)
        if assignment.B2:
            args["B2"] = "{0:.0f}".format(assignment.B2)
    # elif assignment.work_type == PRIMENET.WORK_TYPE_CERT:
    retry = False
    logging.info("Registering assignment: {0} {1}".format(
        work_type_str, assignment_to_str(assignment)))
    result = send_request(guid, args)
    if result is None:
        retry = True
    else:
        rc = int(result["pnErrorResult"])
        if rc == PRIMENET.ERROR_OK:
            assignment.uid = result["k"]
            logging.info(
                "Assignment registered as: {0}".format(assignment.uid))
            return assignment
        elif rc == PRIMENET.ERROR_NO_ASSIGNMENT:
            pass
        elif rc == PRIMENET.ERROR_INVALID_ASSIGNMENT_TYPE:
            pass
        elif rc == PRIMENET.ERROR_INVALID_PARAMETER:
            pass
        elif rc == PRIMENET.ERROR_UNREGISTERED_CPU:
            register_instance()
            retry = True
        elif rc == PRIMENET.ERROR_STALE_CPU_INFO:
            register_instance(guid)
            retry = True
    if retry:
        return register_assignment(cpu_num, assignment, retry_count + 1)
    return None


def register_assignments(adir, cpu_num, tasks):
    registered_assignment = False
    changed = False
    for i, assignment in enumerate(tasks):
        if isinstance(assignment, Assignment):
            if not assignment.uid and not assignment.ra_failed:
                registered = register_assignment(cpu_num, assignment)
                if registered:
                    assignment = registered
                    registered_assignment = True
                else:
                    assignment.ra_failed = True
                task = output_assignment(assignment)
                assignment, _ = update_assignment(assignment, task)
                tasks[i] = assignment
                changed = True
    if changed:
        write_workfile(adir, tasks)
    return registered_assignment


def send_progress(cpu_num, assignment, percent, stage,
                  time_left, now, fftlen, retry_count=0):
    """Sends the expected completion date for a given assignment to the server."""
    guid = get_guid(config)
    if guid is None:
        logging.error("Cannot update, the registration is not done")
        return None
    if not assignment.uid:
        return None
    if retry_count >= 5:
        logging.info("Retry count exceeded.")
        return None
    # Assignment Progress fields:
    # g= the machine's GUID (32 chars, assigned by Primenet on 1st-contact from a given machine, stored in 'guid=' entry of local.ini file of rundir)
    args = primenet_v5_bargs.copy()
    args["t"] = "ap"  # update compute command
    args["g"] = guid
    # k= the assignment ID (32 chars, follows '=' in Primenet-generated workfile entries)
    args["k"] = assignment.uid
    # p= progress in %-done, 4-char format = xy.z
    args["p"] = "{0:.4f}".format(percent * 100)
    # d= when the client is expected to check in again (in seconds ... )
    args["d"] = options.hours_between_checkins * 60 * 60
    # e= the ETA of completion in seconds, if unknown, just put 1 week
    args["e"] = int(time_left) if time_left is not None else 7 * 24 * 60 * 60
    # c= the worker thread of the machine
    args["c"] = cpu_num
    # stage= LL in this case, although an LL test may be doing TF or P-1 work
    # first so it's possible to be something besides LL
    if stage:
        args["stage"] = stage
    if fftlen:
        args["fftlen"] = fftlen
    retry = False
    delta = timedelta(seconds=time_left)
    logging.info("Sending expected completion date for {0}: {1} ({2:%c})".format(
        assignment_to_str(assignment), delta, now + delta))
    result = send_request(guid, args)
    if result is None:
        # Try again
        retry = True
    else:
        rc = int(result["pnErrorResult"])
        if rc == PRIMENET.ERROR_OK:
            logging.debug("Update correctly sent to server")
        elif rc == PRIMENET.ERROR_INVALID_ASSIGNMENT_KEY:
            # TODO: Delete assignment from workfile
            pass
        elif rc == PRIMENET.ERROR_WORK_NO_LONGER_NEEDED:
            # TODO: Delete assignment from workfile
            pass
        elif rc == PRIMENET.ERROR_UNREGISTERED_CPU:
            register_instance()
            retry = True
        elif rc == PRIMENET.ERROR_STALE_CPU_INFO:
            register_instance(guid)
            retry = True
        elif rc == PRIMENET.ERROR_SERVER_BUSY:
            retry = True
    if retry:
        return send_progress(cpu_num, assignment, percent,
                             stage, time_left, now, fftlen, retry_count + 1)
    return None


def update_progress(cpu_num, assignment, progress,
                    msec_per_iter, p, now, cur_time_left, checkin):
    """Update the progress of a given assignment."""
    if not assignment:
        return None
    iteration, _, fftlen, _, bits, s2 = progress
    percent, time_left, msec_per_iter = compute_progress(
        assignment, iteration, msec_per_iter, p, bits, s2)
    logging.debug("{0} is {1:.4%} done ({2:n} / {3:n})".format(assignment.n, percent, iteration,
                  s2 if s2 else bits if bits else assignment.n if assignment.work_type == PRIMENET.WORK_TYPE_PRP else assignment.n - 2))
    stage = None
    if percent > 0:
        if bits:
            stage = "S1"
        elif s2:
            stage = "S2"
        elif assignment.work_type in {PRIMENET.WORK_TYPE_FIRST_LL, PRIMENET.WORK_TYPE_DBLCHK}:
            stage = "LL"
        elif assignment.work_type == PRIMENET.WORK_TYPE_PRP:
            stage = "PRP"
        elif assignment.work_type == PRIMENET.WORK_TYPE_CERT:
            stage = "CERT"
    if time_left is None:
        cur_time_left += 7 * 24 * 60 * 60
        logging.debug("Finish cannot be estimated")
    else:
        cur_time_left += time_left
        delta = timedelta(seconds=cur_time_left)
        logging.debug(
            "Finish estimated in {0} (used {1:.4n} msec/iter estimation)".format(delta, msec_per_iter))
    if checkin:
        send_progress(cpu_num, assignment, percent,
                      stage, cur_time_left, now, fftlen)
    return percent, cur_time_left


def update_progress_all(adir, cpu_num, last_time,
                        tasks, progress, checkin=True):
    """Update the progress of all the assignments in the workfile."""
    if not tasks:
        return None  # don't update if no worktodo
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
    if progress is None:
        assignments = iter(OrderedDict(((assignment.uid, assignment.n), assignment)
                           for assignment in tasks if isinstance(assignment, Assignment)).values())
        assignment = next(assignments, None)
        if assignment is None:
            return None
        result = get_progress_assignment(adir, assignment, last_time)
        _, msec_per_iter, _, modified, _, _ = result
        checkin = checkin and modified
        p = assignment.n
        if msec_per_iter is not None:
            config.set(section, "msec_per_iter",
                       "{0:.4f}".format(msec_per_iter))
            config.set(section, "exponent", str(p))
        elif config.has_option(section, "msec_per_iter") and config.has_option(section, "exponent"):
            # If not speed available, get it from the local.ini file
            msec_per_iter = config.getfloat(section, "msec_per_iter")
            p = config.getint(section, "exponent")
        # Do the other assignment accumulating the time_lefts
        cur_time_left = 0
        percent, cur_time_left = update_progress(
            cpu_num, assignment, result, msec_per_iter, p, now, cur_time_left, checkin)
    else:
        assignments = tasks
        percent, cur_time_left, msec_per_iter, p = progress

    for assignment in assignments:
        result = get_progress_assignment(adir, assignment, None)
        percent, cur_time_left = update_progress(
            cpu_num, assignment, result, msec_per_iter, p, now, cur_time_left, checkin)
    return percent, cur_time_left, msec_per_iter, p


def cuda_result_to_json(resultsfile, sendline):
    # CUDALucas

    # sendline example: 'M( 108928711 )C, 0x810d83b6917d846c, offset = 106008371, n = 6272K, CUDALucas v2.06, AID: 02E4F2B14BB23E2E4B95FC138FC715A8'
    # sendline example: 'M( 108928711 )P, offset = 106008371, n = 6272K, CUDALucas v2.06, AID: 02E4F2B14BB23E2E4B95FC138FC715A8'
    ar = {}
    regex = re.compile(
        r"^M\( ([0-9]{7,}) \)(P|C, (0x[0-9a-f]{16})), offset = ([0-9]+), n = ([0-9]{3,})K, (CUDALucas v[^\s,]+)(?:, AID: ([0-9A-F]{32}))?$")
    res = regex.search(sendline)
    if not res:
        logging.error("Unable to parse entry in {0!r}: {1}".format(
            resultsfile, sendline))
        return None

    if res.group(7):
        ar["aid"] = res.group(7)
    ar["worktype"] = "LL"  # CUDALucas only does LL tests
    ar["status"] = res.group(2)[0]
    ar["exponent"] = int(res.group(1))

    if res.group(2).startswith("C"):
        ar["res64"] = res.group(3)[2:]
    ar["shift-count"] = res.group(4)
    ar["fft-length"] = int(res.group(5)) * 1024  # << 10
    ar["program"] = program = {}
    program["name"], program["version"] = res.group(6).split(None, 1)
    ar["result"] = sendline
    return ar


def report_result(sendline, ar, tasks, retry_count=0):
    """Submit one result line using v5 API, will be attributed to the computed identified by guid."""
    """Return False if the submission should be retried"""
    if retry_count >= 5:
        logging.info("Retry count exceeded.")
        return False
    guid = get_guid(config)
    # JSON is required because assignment_id is necessary in that case
    # and it is not present in old output format.
    logging.debug("Submitting using v5 API")
    logging.debug("Sending result: {0!r}".format(sendline))
    program = ar["program"]
    aprogram = " ".join(program.values())
    logging.debug("Program: {0}".format(aprogram))
    config.set(section, "program", aprogram)

    ar["script"] = {
        "name": os.path.basename(sys.argv[0]),
        "version": VERSION, "interpreter": "Python",
        "interpreter-version": platform.python_version()}

    assignment_uid = ar.get("aid", 0)
    exponent = int(ar["exponent"])
    worktype = ar["worktype"]
    if worktype == "LL":
        if ar["status"] == "P":
            result_type = PRIMENET.AR_LL_PRIME
        else:  # elif ar['status'] == 'C':
            result_type = PRIMENET.AR_LL_RESULT
    elif worktype.startswith("PRP"):
        if ar["status"] == "P":
            result_type = PRIMENET.AR_PRP_PRIME
        else:  # elif ar['status'] == 'C':
            result_type = PRIMENET.AR_PRP_RESULT
    elif worktype == "PM1":
        if ar["status"] == "F":
            result_type = PRIMENET.AR_P1_FACTOR
        else:  # elif ar['status'] == 'NF':
            result_type = PRIMENET.AR_P1_NOFACTOR
    else:
        logging.error("Unsupported worktype {0}".format(worktype))
        return False
    if result_type in {PRIMENET.AR_LL_PRIME, PRIMENET.AR_PRP_PRIME}:
        if not (config.has_option(section, "SilentVictory") and config.getboolean(
                section, "SilentVictory")) and not is_known_mersenne_prime(exponent):
            thread = threading.Thread(target=announce_prime_to_user, args=(
                exponent, worktype), daemon=True)
            thread.start()
        # Backup notification
        r = requests.post("https://maker.ifttt.com/trigger/result_submitted/with/key/cIhVJKbcWgabfVaLuRjVsR",
                          json={"value1": config.get(section, "user_name"), "value2": sendline}, timeout=180)
        logging.debug(r.text)
        if options.no_report_100m and digits(exponent) >= 100000000:
            return True
    user = ar.get("user", options.user_id)
    computer = ar.get("computer", options.computer_id)
    buf = "" if not user else "UID: {0}, ".format(
        user) if not computer else "UID: {0}/{1}, ".format(user, computer)
    port = program.get("port", PORT)
    args = primenet_v5_bargs.copy()
    args["t"] = "ar"								# assignment result
    args["g"] = guid
    args["k"] = assignment_uid			# assignment id
    # message is the complete JSON string
    args["m"] = json.dumps(ar, ensure_ascii=False)
    args["r"] = result_type							# result type
    args["n"] = exponent
    if result_type in {PRIMENET.AR_LL_RESULT, PRIMENET.AR_LL_PRIME}:
        args["d"] = 1
        error_count = ar["error-code"] if "error-code" in ar else "0" * 8
        if result_type == PRIMENET.AR_LL_RESULT:
            buf += "M{0} is not prime. Res64: {1}. Wh{2}: -,{3},{4}".format(
                exponent, ar["res64"], port, ar["shift-count"], error_count)
            args["rd"] = ar["res64"].strip().zfill(16)
        else:
            buf += "M{0} is prime! Wh{1}: -,{2}".format(
                exponent, port, error_count)
        args["sc"] = ar["shift-count"]
        args["ec"] = error_count
    elif result_type in {PRIMENET.AR_PRP_RESULT, PRIMENET.AR_PRP_PRIME}:
        args["d"] = 1
        args.update((("A", 1), ("b", 2), ("c", -1)))
        prp_base = int(worktype[4:])
        if result_type == PRIMENET.AR_PRP_RESULT:
            residue_type = ar["residue-type"]
            buf += "M{0} is not prime.  {1}{2}RES64: {3}.".format(exponent, "Base-{0} ".format(
                prp_base) if prp_base != 3 else "", "Type-{0} ".format(residue_type) if residue_type != 1 else "", ar["res64"])
            args["rd"] = ar["res64"].strip().zfill(16)
            args["rt"] = residue_type
        else:
            buf += "M{0} is a probable prime{1}!".format(
                exponent, " ({0}-PRP)".format(prp_base) if prp_base != 3 else "")
        error_count = ar["error-code"] if "error-code" in ar else "0" * 8
        buf += " Wh{0}: -,{1}{2}".format(port, "{0},".format(
            ar["shift-count"]) if "known-factors" in ar else "", error_count)
        args["ec"] = error_count
        if "known-factors" in ar:
            args["nkf"] = len(ar["known-factors"])
        args["base"] = prp_base  # worktype == PRP-base
        if "shift-count" in ar:
            args["sc"] = ar["shift-count"]
        # 1 if Gerbicz error checking used in PRP test
        args["gbz"] = 1
        if "proof" in ar:
            args["pp"] = ar["proof"]["power"]
            args["ph"] = ar["proof"]["md5"]
    elif result_type in {PRIMENET.AR_P1_FACTOR, PRIMENET.AR_P1_NOFACTOR}:
        args["d"] = 1 if result_type == PRIMENET.AR_P1_FACTOR or not any(
            task.n == exponent for task in tasks if isinstance(task, Assignment)) else 0
        args.update((("A", 1), ("b", 2), ("c", -1)))
        args["B1"] = ar["B1"]
        if "B2" in ar:
            args["B2"] = ar["B2"]
        if result_type == PRIMENET.AR_P1_FACTOR:
            factor = int(ar["factors"][0])
            buf += "M{0} has a factor: {1} (P-1, B1={2}{3})".format(
                exponent, factor, ar["B1"], ", B2={0}".format(ar["B2"]) if "B2" in ar else "")
            args["f"] = factor
            n = (1 << exponent) - 1
            for factor in ar["factors"]:
                if n % int(factor):
                    logging.warning(
                        "Bad factor for {0} found: {1}".format(exponent, factor))
        else:
            buf += "M{0} completed P-1, B1={1}{2}, Wh{3}: -".format(
                exponent, ar["B1"], ", B2={0}".format(ar["B2"]) if "B2" in ar else "", port)
    # elif result_type == PRIMENET.AR_CERT:
    if "fft-length" in ar:
        args["fftlen"] = ar["fft-length"]
    if assignment_uid:
        buf += ", AID: {0}".format(assignment_uid)
    logging.info("Sending result to server: {0}".format(buf))
    result = send_request(guid, args)
    if result is None:
        pass
        # if this happens, the submission can be retried
        # since no answer has been received from the server
        # return False
    else:
        rc = int(result["pnErrorResult"])
        if rc == PRIMENET.ERROR_OK:
            logging.debug("Result correctly send to server")
            return True
        elif rc == PRIMENET.ERROR_UNREGISTERED_CPU:
            # should register again and retry
            register_instance()
            # return False
        elif rc == PRIMENET.ERROR_STALE_CPU_INFO:
            register_instance(guid)
        # In all other error case, the submission must not be retried
        elif rc == PRIMENET.ERROR_INVALID_ASSIGNMENT_KEY:
            # TODO: Delete assignment from workfile if it is not done
            return True
        elif rc == PRIMENET.ERROR_WORK_NO_LONGER_NEEDED:
            # TODO: Delete assignment from workfile if it is not done
            return True
        elif rc == PRIMENET.ERROR_NO_ASSIGNMENT:
            # TODO: Delete assignment from workfile if it is not done
            return True
        elif rc == PRIMENET.ERROR_INVALID_RESULT_TYPE:
            return True
        elif rc == PRIMENET.ERROR_INVALID_PARAMETER:
            logging.error(
                "INVALID PARAMETER: This may be a bug in the script, please create an issue: https://github.com/tdulcet/Distributed-Computing-Scripts/issues")
            return False

    return report_result(sendline, ar, tasks, retry_count + 1)


def submit_one_line_manually(sendline):
    """Submit results using manual testing, will be attributed to "Manual Testing" in mersenne.org."""
    logging.debug("Submitting using manual results")
    logging.info("Sending result: {0!r}".format(sendline))
    try:
        r = session.post(primenet_baseurl +
                         "manual_result/default.php", data={"data": sendline})
        r.raise_for_status()
        res_str = r.text
        if "Error code" in res_str:
            ibeg = res_str.find("Error code")
            iend = res_str.find("</div>", ibeg)
            logging.error(
                "Submission failed: '{0}'".format(res_str[ibeg:iend]))
            if res_str[ibeg:iend].startswith("Error code: 40"):
                logging.error("Already sent, will not retry")
        elif "Accepted" in res_str:
            begin = res_str.find("CPU credit is")
            end = res_str.find("</div>", begin)
            if begin >= 0 and end >= 0:
                logging.info(res_str[begin:end])
        else:
            logging.error(
                "Submission of results line {0!r} failed for reasons unknown - please try manual resubmission.".format(sendline))
    except HTTPError:
        logging.exception("")
        return False
    except ConnectionError:
        logging.exception("URL open ERROR")
        return False
    return True  # EWM: Append entire results_send rather than just sent to avoid resubmitting
    # bad results (e.g. previously-submitted duplicates) every time the script
    # executes.


def submit_one_line(resultsfile, sendline, assignments):
    """Submits a result to the server."""
    if not options.cudalucas:  # Mlucas or GpuOwl
        try:
            ar = json.loads(sendline)
            is_json = True
        except json.decoder.JSONDecodeError:
            logging.exception(
                "Unable to decode entry in {0!r}: {1}".format(resultsfile, sendline))
            # Mlucas
            if not options.gpuowl and "Program: E" in sendline:
                logging.info("Please upgrade to Mlucas v19 or greater.")
            # GpuOwl
            if options.gpuowl and "gpuowl v" in sendline:
                logging.info("Please upgrade to GpuOwl v0.7 or greater.")
            is_json = False
    else:  # CUDALucas
        ar = cuda_result_to_json(resultsfile, sendline)

    guid = get_guid(config)
    if guid is not None and (options.cudalucas or is_json) and ar is not None:
        # If registered and the ar object was returned successfully, submit using the v5 API
        # The result will be attributed to the registered computer
        # If registered and the line is a JSON, submit using the v5 API
        # The result will be attributed to the registered computer
        sent = report_result(sendline, ar, assignments)
    else:
        # The result will be attributed to "Manual testing"
        sent = submit_one_line_manually(sendline)
    return sent


def submit_work(adir, tasks):
    """Submits the results file to PrimeNet."""
    # A cumulative backup
    sentfile = os.path.join(adir, "results_sent.txt")
    results_sent = frozenset(readonly_list_file(sentfile))
    # Only submit completed work, i.e. the exponent must not exist in worktodo file any more
    # appended line by line, no lock needed
    resultsfile = os.path.join(adir, options.results_file)
    results = readonly_list_file(resultsfile)
    # EWM: Note that readonly_list_file does not need the file(s) to exist - nonexistent files simply yield 0-length rs-array entries.
    # remove nonsubmittable lines from list of possibles
    results = filter(mersenne_find, results)

    # if a line was previously submitted, discard
    results_send = [line for line in results if line not in results_sent]

    # Only for new results, to be appended to results_sent
    sent = []

    length = len(results_send)
    if not length:
        logging.debug("No new results in {0!r}.".format(resultsfile))
        return
    logging.debug("Found {0:n} new result{1} to report in {2!r}".format(
        length, "s" if length > 1 else "", resultsfile))
    # EWM: Switch to one-result-line-at-a-time submission to support
    # error-message-on-submit handling:
    for sendline in results_send:
        # case where password is entered (not needed in v5 API since we have a key)
        if options.password:
            is_sent = submit_one_line_manually(sendline)
        else:
            is_sent = submit_one_line(resultsfile, sendline, tasks)
        if is_sent:
            sent.append(sendline)
    write_list_file(sentfile, sent, "a")


def ping_server(ping_type=1):
    guid = get_guid(config)
    args = primenet_v5_bargs.copy()
    args["t"] = "ps"
    args["q"] = ping_type
    logging.info("Contacting PrimeNet Server.")
    result = send_request(guid, args)
    if result is None:
        pass
    else:
        rc = int(result["pnErrorResult"])
        if rc == PRIMENET.ERROR_OK:
            return result["r"]
    return None

#######################################################################################################
#
# Start main program here
#
#######################################################################################################


parser = optparse.OptionParser(version="%prog " + VERSION, description="""This program will automatically get assignments, report assignment results, upload proof files and optionally register assignments and report assignment progress to PrimeNet for the GpuOwl, CUDALucas and Mlucas GIMPS programs. It also saves its configuration to a “local.ini” file by default, so it is only necessary to give most of the arguments once.
The first time it is run, if a password is NOT provided, it will register the current GpuOwl/CUDALucas/Mlucas instance with PrimeNet (see the Registering Options below).
Then, it will report assignment results, get assignments and upload any proof files to PrimeNet on the --timeout interval, or only once if --timeout is 0. If registered, it will additionally report the progress on the --checkin interval.
"""
                               )

# options not saved to local.ini
parser.add_option("-d", "--debug", action="count", dest="debug", default=0,
                  help="Output detailed information. Provide multiple times for even more verbose output.")
parser.add_option("-w", "--workdir", dest="workdir", default=".",
                  help="Working directory with the local file from this program, Default: %default (current directory)")
parser.add_option("-D", "--dir", action="append", dest="dirs",
                  help="Directories with the work and results files from the GIMPS program. Provide once for each worker thread. It automatically sets the --cpu-num option for each directory.")

# all other options are saved to local.ini
parser.add_option("-i", "--workfile", dest="worktodo_file",
                  default="worktodo.ini", help="Work file filename, Default: “%default”")
parser.add_option("-r", "--resultsfile", dest="results_file",
                  default="results.txt", help="Results file filename, Default: “%default”")
parser.add_option("-L", "--logfile", dest="logfile",
                  default="primenet.log", help="Log file filename, Default: “%default”")
parser.add_option("-l", "--localfile", dest="localfile", default="local.ini",
                  help="Local configuration file filename, Default: “%default”")
parser.add_option("--archive-proofs", dest="archive_dir",
                  help="Directory to archive PRP proof files after upload, Default: %default")
parser.add_option("-u", "--username", dest="user_id",
                  help="GIMPS/PrimeNet User ID. Create a GIMPS/PrimeNet account: https://www.mersenne.org/update/. If you do not want a PrimeNet account, you can use ANONYMOUS.")
parser.add_option("-p", "--password", dest="password",
                  help="Optional GIMPS/PrimeNet Password. Deprecated and not recommended. Only provide if you want to do manual testing and not report the progress. This was the default behavior for old versions of this script.")

# -t is reserved for timeout, instead use -T for assignment-type preference:
parser.add_option("-T", "--worktype", dest="work_preference", default=str(PRIMENET.WP_LL_FIRST), help="""Type of work, Default: %default,
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
parser.add_option("--min-exp", dest="min_exp", type="int",
                  help="Minimum exponent to get from PrimeNet (2 - 999,999,999)")
parser.add_option("--max-exp", dest="max_exp", type="int",
                  help="Maximum exponent to get from PrimeNet (2 - 999,999,999)")

parser.add_option("-g", "--gpuowl", action="store_true", dest="gpuowl",
                  help="Get assignments for a GPU (GpuOwl) instead of the CPU (Mlucas).")
parser.add_option("--cudalucas", dest="cudalucas",
                  help="Get assignments for a GPU (CUDALucas) instead of the CPU (Mlucas). Provide the CUDALucas output filename as the argument.")
parser.add_option("--prime95", action="store_true",
                  dest="prime95", help=optparse.SUPPRESS_HELP)
parser.add_option("--num-workers", dest="num_worker_threads", type="int", default=1,
                  help="Number of worker threads (CPU Cores/GPUs), Default: %default")
parser.add_option("-c", "--cpu-num", dest="cpu", type="int", default=0,
                  help="CPU core or GPU number to get assignments for, Default: %default. Deprecated in favor of the --dir option.")
parser.add_option("-n", "--num-cache", dest="num_cache", type="int", default=0,
                  help="Number of assignments to cache, Default: %default (automatically incremented by 1 when doing manual testing). Deprecated in favor of the --days-work option.")
parser.add_option("-W", "--days-work", dest="days_of_work", type="float", default=3.0,
                  help="Days of work to queue (1-180 days), Default: %default days. Adds one to num_cache when the time left for all assignments is less than this number of days.")
parser.add_option("--force-pminus1", dest="tests_saved", type="float",
                  help="Force P-1 factoring before LL/PRP tests and/or change the default PrimeNet PRP tests_saved value.")
parser.add_option("--pminus1-threshold", dest="pm1_multiplier", type="float",
                  help="Retry the P-1 factoring before LL/PRP tests only if the existing P-1 bounds are less than the target bounds (as listed on mersenne.ca) times this threshold/multiplier. Requires the --force-pminus1 option.")
parser.add_option("--convert-ll-to-prp", action="store_true", dest="convert_ll_to_prp",
                  help="Convert all LL assignments to PRP. This is for use when registering assignments.")
parser.add_option("--convert-prp-to-ll", action="store_true", dest="convert_prp_to_ll",
                  help="Convert all PRP assignments to LL. This is automatically enabled for first time PRP assignments when the --worktype option is for a first time LL worktype.")
parser.add_option("--no-report-100m", action="store_true", dest="no_report_100m",
                  help="Do not report any prime results for exponents greater than 100 million digits. You must setup another method to notify yourself.")

parser.add_option("--checkin", dest="hours_between_checkins", type="int", default=6,
                  help="Hours to wait between sending assignment progress and expected completion dates (1-168 hours), Default: %default hours. Requires that the instance is registered with PrimeNet.")
parser.add_option("-t", "--timeout", dest="timeout", type="int", default=60 * 60,
                  help="Seconds to wait between updates, Default: %default seconds (1 hour). Users with slower internet may want to set a larger value to give time for any PRP proof files to upload. Use 0 to update once and exit.")
parser.add_option("-s", "--status", action="store_true", dest="status", default=False,
                  help="Output a status report and any expected completion dates for all assignments and exit.")
parser.add_option("--upload-proofs", action="store_true", dest="proofs", default=False,
                  help="Report assignment results, upload all PRP proofs and exit. Requires PrimeNet User ID.")
parser.add_option("--recover-all", action="store_true", dest="recover", default=False,
                  help="Recover all assignments and exit. This will overwrite any existing work files. Requires that the instance is registered with PrimeNet.")
parser.add_option("--unreserve", dest="exponent", type="int",
                  help="Unreserve the exponent and exit. Use this only if you are sure you will not be finishing this exponent. Requires that the instance is registered with PrimeNet.")
parser.add_option("--unreserve-all", action="store_true", dest="unreserve_all", default=False,
                  help="Unreserve all assignments and exit. Quit GIMPS immediately. Requires that the instance is registered with PrimeNet.")
parser.add_option("--no-more-work", action="store_true", dest="NoMoreWork", default=False,
                  help="Prevent the script from getting new assignments and exit. Quit GIMPS after current work completes.")
parser.add_option("--ping", action="store_true", dest="ping", default=False,
                  help="Ping the PrimeNet server, show version information and exit.")

# TODO: add detection for most parameter, including automatic change of the hardware
memory = get_physical_memory() or 1024
cores, threads = get_cpu_cores_threads()

group = optparse.OptionGroup(parser, "Registering Options", "Sent to PrimeNet/GIMPS when registering. It will automatically send the progress, which allows the program to then be monitored on the GIMPS website CPUs page (https://www.mersenne.org/cpus/), just like with Prime95/MPrime. This also allows the program to get much smaller Category 0 and 1 exponents, if it meets the other requirements (https://www.mersenne.org/thresholds/).")
group.add_option("-H", "--hostname", dest="computer_id", default=platform.node()[:20],
                 help="Optional computer name, Default: %default")
group.add_option("--cpu-model", dest="cpu_brand", default=get_cpu_model() or "cpu.unknown",
                 help="Processor (CPU) model, Default: %default")
group.add_option("--features", dest="cpu_features", default="",
                 help="CPU features, Default: '%default'")
group.add_option("--frequency", dest="cpu_speed", type="int", default=get_cpu_frequency() or 1000,
                 help="CPU frequency/speed (MHz), Default: %default MHz")
group.add_option("-m", "--memory", dest="memory", type="int", default=memory,
                 help="Total physical memory (RAM) (MiB), Default: %default MiB")
group.add_option("--max-memory", dest="day_night_memory", type="int", default=int(.9 * memory),
                 help="Configured day/night P-1 stage 2 memory (MiB), Default: %default MiB (90% of physical memory). Required for P-1 assignments.")
group.add_option("--L1", dest="cpu_l1_cache_size", type="int", default=8,
                 help="L1 Cache size (KiB), Default: %default KiB")
group.add_option("--L2", dest="cpu_l2_cache_size", type="int", default=512,
                 help="L2 Cache size (KiB), Default: %default KiB")
group.add_option("--L3", dest="cpu_l3_cache_size", type="int", default=0,
                 help="L3 Cache size (KiB), Default: %default KiB")
group.add_option("--np", dest="num_cores", type="int", default=cores or 1,
                 help="Number of physical CPU cores, Default: %default")
group.add_option("--hp", dest="cpu_hyperthreads", type="int", default=-(threads // -cores) if cores else 0,
                 help="Number of CPU threads per core (0 is unknown), Default: %default. Choose 1 for non-hyperthreaded and 2 or more for hyperthreaded.")
group.add_option("--hours", dest="cpu_hours", type="int", default=24,
                 help="Hours per day you expect to run the GIMPS program (1 - 24), Default: %default hours. Used to give better estimated completion dates.")
parser.add_option_group(group)

opts_no_defaults = optparse.Values()
_, args = parser.parse_args(values=opts_no_defaults)
if args:
    parser.error("Unexpected arguments")
options = optparse.Values(parser.get_default_values().__dict__)
options._update_careful(opts_no_defaults.__dict__)

workdir = os.path.expanduser(options.workdir)
dirs = [os.path.join(workdir, adir)
        for adir in options.dirs] if options.dirs else [workdir]

logging.basicConfig(level=max(logging.INFO - options.debug * 10, 0), format="%(filename)s: " + (
    "%(funcName)s:\t" if options.debug > 1 else "") + "[%(threadName)s %(asctime)s]  %(levelname)s: %(message)s")
handler = logging.FileHandler(os.path.join(workdir, options.logfile))
handler.setFormatter(logging.Formatter(
    "[%(threadName)s %(asctime)s]  %(levelname)s: %(message)s"))
logging.getLogger().addHandler(handler)

# r'^(?:(Test|DoubleCheck)=([0-9A-F]{32})(,[0-9]+(?:\.[0-9]+)?){1,3}|(PRP(?:DC)?)=([0-9A-F]{32})(,-?[0-9]+(?:\.[0-9]+)?){4,8}(,"[0-9]+(?:,[0-9]+)*")?|(P[Ff]actor)=([0-9A-F]{32})(,-?[0-9]+(?:\.[0-9]+)?){6}|(P[Mm]inus1)=([0-9A-F]{32})(,-?[0-9]+(?:\.[0-9]+)?){6,8}(,"[0-9]+(?:,[0-9]+)*")?|(Cert)=([0-9A-F]{32})(,-?[0-9]+(?:\.[0-9]+)?){5})$'
workpattern = re.compile(
    r'^(Test|DoubleCheck|PRP(?:DC)?|P[Ff]actor|P[Mm]inus1|Cert)\s*=\s*(?:(([0-9A-F]{32})|[Nn]/[Aa]|0),)?(?:(-?[0-9]+(?:\.[0-9]+)?|"[0-9]+(?:,[0-9]+)*")(?:,|$)){1,9}$')

# If debug is requested

# https://stackoverflow.com/questions/10588644/how-can-i-see-the-entire-http-request-thats-being-sent-by-my-python-application
if options.debug > 1:
    try:
        # Python 3+
        from http.client import HTTPConnection
    except ImportError:
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
# TODO: check that input char are ASCII or at least supported by the server
if not 8 <= len(options.cpu_brand) <= 64:
    parser.error("CPU model must be between 8 and 64 characters")
if options.computer_id is not None and len(options.computer_id) > 20:
    parser.error("Computer name must be less than or equal to 20 characters")
if options.cpu_features is not None and len(options.cpu_features) > 64:
    parser.error("CPU features must be less than or equal to 64 characters")

PROGRAM = PROGRAMS[3 if options.cudalucas else 2 if options.gpuowl else 1]

# Convert mnemonic-form worktypes to corresponding numeric value, check
# worktype value vs supported ones:
worktypes = {
    "Pfactor": PRIMENET.WP_PFACTOR,
    "SmallestAvail": PRIMENET.WP_LL_FIRST,
    "DoubleCheck": PRIMENET.WP_LL_DBLCHK,
    "WorldRecord": PRIMENET.WP_LL_WORLD_RECORD,
    "100Mdigit": PRIMENET.WP_LL_100M,
    "SmallestAvailPRP": PRIMENET.WP_PRP_FIRST,
    "DoubleCheckPRP": PRIMENET.WP_PRP_DBLCHK,
    "WorldRecordPRP": PRIMENET.WP_PRP_WORLD_RECORD,
    "100MdigitPRP": PRIMENET.WP_PRP_100M}
# this and the above line of code enables us to use words or numbers on the cmdline
if options.work_preference in worktypes:
    options.work_preference = worktypes[options.work_preference]
supported = frozenset([PRIMENET.WP_LL_FIRST,
                       PRIMENET.WP_LL_DBLCHK,
                       PRIMENET.WP_LL_WORLD_RECORD,
                       PRIMENET.WP_LL_100M] + ([PRIMENET.WP_PFACTOR,
                                                PRIMENET.WP_PRP_FIRST,
                                                PRIMENET.WP_PRP_DBLCHK,
                                                PRIMENET.WP_PRP_WORLD_RECORD,
                                                PRIMENET.WP_PRP_100M,
                                                PRIMENET.WP_PRP_NO_PMINUS1] if not options.cudalucas else []) + ([PRIMENET.WP_PRP_DC_PROOF] if options.gpuowl else []))
if not options.work_preference.isdigit() or int(
        options.work_preference) not in supported:
    parser.error("Unsupported/unrecognized worktype = {0} for {1}".format(
        options.work_preference, PROGRAM["name"]))
work_preference = int(options.work_preference)
# Convert first time LL worktypes to PRP
option_dict = {
    PRIMENET.WP_LL_FIRST: PRIMENET.WP_PRP_FIRST,
    PRIMENET.WP_LL_WORLD_RECORD: PRIMENET.WP_PRP_WORLD_RECORD,
    PRIMENET.WP_LL_100M: PRIMENET.WP_PRP_100M}
if work_preference in option_dict:
    work_preference = option_dict[work_preference]

# if guid already exist, recover it, this way, one can (re)register to change
# the CPU model (changing instance name can only be done in the website)
guid = get_guid(config)
if options.user_id is None:
    parser.error("Username must be given")

if options.dirs and len(options.dirs) != options.num_worker_threads:
    parser.error(
        "The number of directories must be equal to the number of worker threads")

if not options.dirs and options.cpu >= options.num_worker_threads:
    parser.error(
        "CPU core or GPU number must be less than the number of worker threads")

if options.gpuowl and options.cudalucas:
    parser.error(
        "This script can only be used with GpuOwl or CUDALucas")

if options.day_night_memory > options.memory:
    parser.error(
        "Max memory must be less than or equal to the total physical memory")

if not 0 <= options.days_of_work <= 180:
    parser.error("Days of work must be less than or equal to 180 days")

if not 1 <= options.cpu_hours <= 24:
    parser.error("Hours per day must be between 1 and 24 hours")

if options.convert_ll_to_prp and options.convert_prp_to_ll:
    parser.error(
        "Cannot convert LL assignments to PRP and PRP assignments to LL at the same time")

if not 1 <= options.hours_between_checkins <= 7 * 24:
    parser.error(
        "Hours between checkins must be between 1 and 168 hours (7 days)")

# write back local.ini if necessary
if config_updated:
    logging.debug("write {0!r}".format(options.localfile))
    config_write(config)

if 0 < options.timeout < 30 * 60:
    parser.error(
        "Timeout must be greater than or equal to {0:n} seconds (30 minutes)".format(30 * 60))

if options.status:
    output_status(dirs)
    sys.exit(0)

if options.proofs:
    for i, adir in enumerate(dirs):
        if options.dirs:
            logging.info("[Worker #{0:n}]".format(i + 1))
        tasks = read_workfile(adir)
        submit_work(adir, tasks)
        upload_proofs(adir)
    sys.exit(0)

if options.recover:
    recover_assignments(dirs)
    sys.exit(0)

if options.exponent:
    unreserve(dirs, options.exponent)
    sys.exit(0)

if options.unreserve_all:
    unreserve_all(dirs)
    sys.exit(0)

if options.NoMoreWork:
    logging.info("Quitting GIMPS after current work completes.")
    config.set(section, "NoMoreWork", "1")
    config_write(config)
    sys.exit(0)

if options.ping:
    result = ping_server()
    if result is None:
        logging.error("Failure pinging server")
        sys.exit(1)
    logging.info("\n" + result)
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
    start = timeit.default_timer()
    config = config_read()
    current_time = time.time()
    last_time = config.getint(section, "LastEndDatesSent") if config.has_option(
        section, "LastEndDatesSent") else 0
    checkin = options.timeout <= 0 or current_time >= last_time + \
        options.hours_between_checkins * 60 * 60
    last_time = last_time if checkin else None

    # Carry on with Loarer's style of primenet
    if options.password:
        try:
            login_data = {"user_login": options.user_id,
                          "user_password": options.password}
            r = session.post(primenet_baseurl + "default.php", data=login_data)
            r.raise_for_status()

            if options.user_id + "<br>logged in" not in r.text:
                primenet_login = False
                logging.error("Login failed.")
            else:
                primenet_login = True
        except HTTPError:
            logging.exception("Login failed.")
        except ConnectionError:
            logging.exception("Login failed.")

    for i, adir in enumerate(dirs):
        if options.dirs:
            logging.info("[Worker #{0:n}]".format(i + 1))
        cpu_num = i if options.dirs else options.cpu
        if not options.password or primenet_login:
            tasks = read_workfile(adir)
            submit_work(adir, tasks)
            registered = register_assignments(adir, cpu_num, tasks)
            progress = update_progress_all(
                adir, cpu_num, last_time, tasks, None, checkin or registered)
            got = get_assignments(adir, cpu_num, progress, tasks)
            if got and not options.password:
                logging.debug("Redo progress update to acknowledge receipt of the just obtained assignment{0}".format(
                    "s" if len(got) > 1 else ""))
                update_progress_all(adir, cpu_num, None, got, progress)
        if options.timeout <= 0:
            upload_proofs(adir)

    if checkin and not options.password:
        config.set(section, "LastEndDatesSent", str(int(current_time)))
    config_write(config)
    if options.timeout <= 0:
        logging.info("Done communicating with server.")
        break
    logging.debug("Done communicating with server.")
    thread = threading.Thread(target=aupload_proofs,
                              name="UploadProofs", args=(dirs,))
    thread.start()
    elapsed = timeit.default_timer() - start
    if options.timeout > elapsed:
        try:
            time.sleep(options.timeout - elapsed)
        except KeyboardInterrupt:
            break
    thread.join()

sys.exit(0)
