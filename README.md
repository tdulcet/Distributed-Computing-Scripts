[![Actions Status](https://github.com/tdulcet/Distributed-Computing-Scripts/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/tdulcet/Distributed-Computing-Scripts/actions/workflows/ci.yml)

# Distributed Computing Scripts
Distributed Computing Scripts for GIMPS, BOINC and Folding@home

Copyright © 2018 Teal Dulcet and Daniel Connelly

❤️ Please visit [tealdulcet.com](https://www.tealdulcet.com/) to support these scripts and my other software development.

## Great Internet Mersenne Prime Search (GIMPS)

🆕 Thanks to Google's [Colaboratory](https://colab.research.google.com/) (Colab) service, anyone with an internet connection can now contribute to GIMPS for 🆓, without downloading or installing anything! Please see our [google-colab](google-colab) directory for instructions.

### Prime95/MPrime

Downloads, sets up and runs [Prime95](https://www.mersenne.org/download/#download). Supports only x86 CPUs.

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mprime.sh -qO - | bash -s -- [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
```

To run Prime95 for Stress/Torture Testing, see the [Testing and Benchmarking](https://github.com/tdulcet/Testing-and-Benchmarking-Scripts) scripts.

### CUDALucas

Downloads, builds, sets up and runs [CUDALucas](https://sourceforge.net/p/cudalucas/code/HEAD/tree/trunk/). Downloads, sets up and runs our [PrimeNet Python program](#primenet) for automated PrimeNet assignments.

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/cudalucas.sh -qO - | bash -s -- [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
```

### Mlucas

Downloads, builds, sets up and runs [Mlucas](https://www.mersenneforum.org/mayer/README.html#download1). Downloads, sets up and runs our [PrimeNet Python program](#primenet) for automated PrimeNet assignments. Supports x86 Intel and AMD and ARM CPUs, but only recommended for ARM CPUs, which [Prime95/MPrime](#prime95mprime) does not support. Prime95/MPrime is faster than Mlucas on x86 CPUs. Run: `wget https://raw.github.com/tdulcet/Linux-System-Information/master/info.sh -qO - | bash -s` to output your system information, including CPU and architecture.
This script follows the recommended instructions on the [Mlucas README](https://www.mersenneforum.org/mayer/README.html) for each architecture and CPU.

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mlucas.sh -qO - | bash -s -- [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
```

### GpuOwl

Downloads, builds, sets up and runs the latest version of [GpuOwl](https://github.com/preda/gpuowl) for PRP tests, version 7.2-112 for PRP tests with combined P-1 and the [v6 branch](https://github.com/preda/gpuowl/tree/v6) for LL and standalone P-1 tests. Downloads, sets up and runs our [PrimeNet Python program](#primenet) for automated PrimeNet assignments. Creates wrapper script to run the correct version of GpuOwl based on the next assignment. Supports Nvidia, AMD and Intel GPUs supporting OpenCL. Note that [GpuOwl uses C++20](https://github.com/preda/gpuowl#build) and thus requires at least the GNU C++ compiler 8. Run: `g++ --version` to output your version.

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/gpuowl.sh -qO - | bash -s -- [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
```

### PrimeNet

Automatically gets assignments, reports assignment results, upload proof files and optionally registers assignments and reports assignment progress to PrimeNet for the GpuOwl, CUDALucas and Mlucas GIMPS programs. Supports both Python 2 and 3 and Windows, macOS and Linux. Requires the [Requests library](https://requests.readthedocs.io/en/master/), which is included with most Python 3 installations. The script will automatically install Requests on first run if it is not already installed. GIMPS [discontinued first time LL assignments](https://mersenneforum.org/showthread.php?t=26682) in April 2021, although the script [still supports them](https://mersenneforum.org/showthread.php?p=575260#post575260) for users of CUDALucas or with limited disk space. Our [GpuOwl](#gpuowl), [CUDALucas](#cudalucas) and [Mlucas](#mlucas) Linux scripts automatically download, setup and run this. Adapted from the PrimeNet Python script from [Mlucas](https://www.mersenneforum.org/mayer/README.html#download2) by [Loïc Le Loarer](https://github.com/llloic11/primenet) and Ernst W. Mayer, which itself was adapted from primetools by [Mark Rose](https://github.com/MarkRose/primetools) and [teknohog](https://github.com/teknohog/primetools).

#### Usage

```
Usage: primenet.py [options]

This program will automatically get assignments, report assignment results,
upload proof files and optionally register assignments and report assignment
progress to PrimeNet for the GpuOwl, CUDALucas and Mlucas GIMPS programs. It
also saves its configuration to a “local.ini” file by default, so it is only
necessary to give most of the arguments once. The first time it is run, if a
password is NOT provided, it will register the current GpuOwl/CUDALucas/Mlucas
instance with PrimeNet (see the Registering Options below). Then, it will
report assignment results, get assignments and upload any proof files to
PrimeNet on the --timeout interval, or only once if --timeout is 0. If
registered, it will additionally report the progress on the --checkin
interval.

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -d, --debug           Output detailed information. Provide multiple times
                        for even more verbose output.
  -w WORKDIR, --workdir=WORKDIR
                        Working directory with the local file from this
                        program, Default: . (current directory)
  -D DIRS, --dir=DIRS   Directories relative to --workdir with the work and
                        results files from the GIMPS program. Provide once for
                        each worker. It automatically sets the --cpu-num
                        option for each directory.
  -i WORKTODO_FILE, --workfile=WORKTODO_FILE
                        Work file filename, Default: “worktodo.txt”
  -r RESULTS_FILE, --resultsfile=RESULTS_FILE
                        Results file filename, Default: “results.txt”
  -L LOGFILE, --logfile=LOGFILE
                        Log file filename, Default: “primenet.log”
  -l LOCALFILE, --localfile=LOCALFILE
                        Local configuration file filename, Default:
                        “local.ini”
  --archive-proofs=ARCHIVE_DIR
                        Directory to archive PRP proof files after upload,
                        Default: none
  -u USER_ID, --username=USER_ID
                        GIMPS/PrimeNet User ID. Create a GIMPS/PrimeNet
                        account: https://www.mersenne.org/update/. If you do
                        not want a PrimeNet account, you can use ANONYMOUS.
  -p PASSWORD, --password=PASSWORD
                        Optional GIMPS/PrimeNet Password. Deprecated and not
                        recommended. Only provide if you want to do manual
                        testing and not report the progress. This was the
                        default behavior for old versions of this script.
  -T WORK_PREFERENCE, --worktype=WORK_PREFERENCE
                        Type of work, Default: 150. Supported work
                        preferences: 4 (P-1 factoring), 100 (First time LL
                        tests), 101 (Double-check LL tests), 102 (World record
                        LL tests), 104 (100M digit LL tests), 150 (First time
                        PRP tests), 151 (Double-check PRP tests), 152 (World
                        record PRP tests), 153 (100M digit PRP tests), 154
                        (Smallest available first time PRP that needs P-1
                        factoring), 155 (Double-check using PRP with proof),
                        160 (First time PRP on Mersenne cofactors), 161
                        (Double-check PRP on Mersenne cofactors). Provide once
                        to use the same worktype for all workers or once for
                        each worker to use different worktypes. Not all
                        worktypes are supported by all the GIMPS programs.
  --min-exp=MIN_EXP     Minimum exponent to get from PrimeNet (2 -
                        999,999,999)
  --max-exp=MAX_EXP     Maximum exponent to get from PrimeNet (2 -
                        999,999,999)
  -g, --gpuowl          Get assignments for GpuOwl instead of Mlucas.
  --cudalucas=CUDALUCAS
                        Get assignments for CUDALucas instead of Mlucas.
                        Provide the CUDALucas output filename as the argument.
  --num-workers=NUM_WORKERS
                        Number of workers (CPU Cores/GPUs), Default: 1
  -c CPU, --cpu-num=CPU
                        CPU core or GPU number to get assignments for,
                        Default: 0. Deprecated in favor of the --dir option.
  -n NUM_CACHE, --num-cache=NUM_CACHE
                        Number of assignments to cache, Default: 0
                        (automatically incremented by 1 when doing manual
                        testing). Deprecated in favor of the --days-work
                        option.
  -W DAYS_OF_WORK, --days-work=DAYS_OF_WORK
                        Days of work to queue (1-180 days), Default: 3.0 days.
                        Adds one to num_cache when the time left for all
                        assignments is less than this number of days.
  --force-pminus1=TESTS_SAVED
                        Force P-1 factoring before LL/PRP tests and/or change
                        the default PrimeNet PRP tests_saved value.
  --pminus1-threshold=PM1_MULTIPLIER
                        Retry the P-1 factoring before LL/PRP tests only if
                        the existing P-1 bounds are less than the target
                        bounds (as listed on mersenne.ca) times this
                        threshold/multiplier. Requires the --force-pminus1
                        option.
  --convert-ll-to-prp   Convert all LL assignments to PRP. This is for use
                        when registering assignments.
  --convert-prp-to-ll   Convert all PRP assignments to LL. This is
                        automatically enabled for first time PRP assignments
                        when the --worktype option is for a first time LL
                        worktype.
  --no-report-100m      Do not report any prime results for exponents greater
                        than or equal to 100 million digits. You must setup
                        another method to notify yourself, such as setting the
                        notification options below.
  --checkin=HOURS_BETWEEN_CHECKINS
                        Hours to wait between sending assignment progress and
                        expected completion dates (1-168 hours), Default: 6
                        hours. Requires that the instance is registered with
                        PrimeNet.
  -t TIMEOUT, --timeout=TIMEOUT
                        Seconds to wait between updates, Default: 3600 seconds
                        (1 hour). Users with slower internet may want to set a
                        larger value to give time for any PRP proof files to
                        upload. Use 0 to update once and exit.
  -s, --status          Output a status report and any expected completion
                        dates for all assignments and exit.
  --upload-proofs       Report assignment results, upload all PRP proofs and
                        exit. Requires PrimeNet User ID.
  --recover-all         Recover all assignments and exit. This will overwrite
                        any existing work files. Requires that the instance is
                        registered with PrimeNet.
  --register-exponents  Prompt for all parameters needed to register one or
                        more specific exponents and exit.
  --unreserve=EXPONENT  Unreserve the exponent and exit. Use this only if you
                        are sure you will not be finishing this exponent.
                        Requires that the instance is registered with
                        PrimeNet.
  --unreserve-all       Unreserve all assignments and exit. Quit GIMPS
                        immediately. Requires that the instance is registered
                        with PrimeNet.
  --no-more-work        Prevent this program from getting new assignments and
                        exit. Quit GIMPS after current work completes.
  --ping                Ping the PrimeNet server, show version information and
                        exit.
  --setup               Prompt for all the options that are needed to setup
                        this program and exit.

  Registering Options:
    Sent to PrimeNet/GIMPS when registering. It will automatically send
    the progress, which allows the program to then be monitored on the
    GIMPS website CPUs page (https://www.mersenne.org/cpus/), just like
    with Prime95/MPrime. This also allows the program to get much smaller
    Category 0 and 1 exponents, if it meets the other requirements
    (https://www.mersenne.org/thresholds/).

    -H COMPUTER_ID, --hostname=COMPUTER_ID
                        Optional computer name, Default: example
    --cpu-model=CPU_BRAND
                        Processor (CPU) model, Default: cpu.unknown
    --features=CPU_FEATURES
                        CPU features, Default: ''
    --frequency=CPU_SPEED
                        CPU frequency/speed (MHz), Default: 1000 MHz
    -m MEMORY, --memory=MEMORY
                        Total physical memory (RAM) (MiB), Default: 1024 MiB
    --max-memory=DAY_NIGHT_MEMORY
                        Configured day/night P-1 stage 2 memory (MiB),
                        Default: 921 MiB (90% of physical memory). Required
                        for P-1 assignments.
    --max-disk-space=WORKER_DISK_SPACE
                        Configured disk space limit per worker to store the
                        proof interim residues files for PRP tests
                        (GiB/worker), Default: 0.0 GiB/worker. Use 0 to not
                        send.
    --l1=CPU_L1_CACHE_SIZE
                        L1 Cache size (KiB), Default: 8 KiB
    --l2=CPU_L2_CACHE_SIZE
                        L2 Cache size (KiB), Default: 512 KiB
    --l3=CPU_L3_CACHE_SIZE
                        L3 Cache size (KiB), Default: 0 KiB
    --cores=NUM_CORES   Number of physical CPU cores, Default: 1
    --hyperthreads=CPU_HYPERTHREADS
                        Number of CPU threads per core (0 is unknown),
                        Default: 0. Choose 1 for non-hyperthreaded and 2 or
                        more for hyperthreaded.
    --hours=CPU_HOURS   Hours per day you expect the GIMPS program will run (1
                        - 24), Default: 24 hours. Used to give better
                        estimated completion dates.

  Notification Options:
    Optionally configure this program to automatically send an e-mail/text
    message notification if there is an error, if the GIMPS program has
    stalled, if the available disk space is low or if it found a new
    Mersenne prime. Send text messages by using your mobile providers
    e-mail to SMS or MMS gateway. Use the --test-email option to verify
    the configuration.

    --to=TOEMAILS       To e-mail address. Use multiple times for multiple
                        To/recipient e-mail addresses. Defaults to the --from
                        value if not provided.
    -f FROMEMAIL, --from=FROMEMAIL
                        From e-mail address
    -S SMTP, --smtp=SMTP
                        SMTP server. Optionally include a port with the
                        'hostname:port' syntax. Defaults to port 465 with
                        --tls and port 25 otherwise.
    --tls               Use a secure connection with SSL/TLS
    --starttls          Upgrade to a secure connection with StartTLS
    -U EMAIL_USERNAME, --email-username=EMAIL_USERNAME
                        SMTP server username
    -P EMAIL_PASSWORD, --email-password=EMAIL_PASSWORD
                        SMTP server password
    --test-email        Send a test e-mail message and exit
```

### Organizations

For installing on multiple computers to a shared or network directory. Developed for use by the [PSU Computer Science Graduate Student Organization](https://gso.cs.pdx.edu/programs/). Also used by our [Google Colab Jupyter Notebooks](google-colab).

#### Prime95/MPrime

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mprime2.sh -qO - | bash -s -- <Computer number> [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
```

#### CUDALucas

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/cudalucas2.sh -qO - | bash -s -- <Computer number> [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
```

#### GpuOwl

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/gpuowl2.sh -qO - | bash -s -- <Computer number> [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
```

## BOINC

Downloads, installs and sets up [BOINC](https://boinc.berkeley.edu/download.php).

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/boinc.sh -qO - | bash -s -- <Project URL> <E-mail> <Password>
```

OR

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/boinc.sh -qO - | bash -s -- <Project URL> <Account Key>
```

This script can be used with any [project that uses BOINC](https://boinc.berkeley.edu/projects.php).

## Folding@home

Downloads, installs and sets up [Folding@home](https://foldingathome.org/start-folding/).

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/folding.sh -qO - | bash -s -- [Username] [Team number] [Passkey] [Power]
```

These scripts should work on Ubuntu, Debian and any Linux distribution that can use the apt package manager.

## Contributing

Pull requests welcome! Ideas for contributions:

PrimeNet program/script:
* Support more GIMPS programs.
* Support setting more of the program options.
* Improve the error handling of PrimeNet API calls.
* Check for new results to submit and proof files to upload when the results file is updated.
* Automatically detect more system information using code from [psutil](https://github.com/giampaolo/psutil), so users do not have to manually determine and specify it.
	* Currently this requires using the Bash install scripts for Linux.
* Get the system information on Windows and macOS using the [ctypes library](https://docs.python.org/3/library/ctypes.html) instead of the `wmic` and `sysctl` commands respectively.
* Improve the performance.
* Support reporting interim residues.
* Calculate the rolling average.
* Support downloading certification assignments.
* Localize the output into other languages (see [here](https://mersenneforum.org/showthread.php?t=27046)).
* Adapt Loïc Le Loarer's [test suite](https://github.com/llloic11/primenet/tree/main/tests).
* Add an optional GUI using [Tk](https://en.wikipedia.org/wiki/Tk_(software)) and the [tkinter library](https://docs.python.org/3/library/tkinter.html)
* Add docstrings to all functions
* Support submitting P-1 results for Fermat numbers

General:
* Create install script for the [CUDAPm1](https://sourceforge.net/projects/cudapm1/) GIMPS program
* Update install scripts to support CLI options
* Add options for setting the maximum CPU time
* Update CUDALucas to support PRP tests and the Jacobi error check for LL tests
* Update Mlucas to support the Jacobi error check for LL and P-1 tests
* Finish and improve the performance of [TensorPrime](https://github.com/TPU-Mersenne-Prime-Search/TensorPrime), the [Tensor Processing Unit](https://en.wikipedia.org/wiki/Tensor_Processing_Unit) (TPU) GIMPS program (see [here](https://github.com/TPU-Mersenne-Prime-Search/TensorPrime/wiki#results-and-next-steps))

## License

The scripts are all MIT licensed, except the PrimeNet program which is GPLv2.

Thanks to [Daniel Connelly](https://github.com/Danc2050) for updating the PrimeNet Python script from Mlucas to eliminate the password requirement by getting assignments using the [PrimeNet API](http://v5.mersenne.org/v5design/v5webAPI_0.97.html) and to support reporting the assignment results and progress for CUDALucas using the PrimeNet API, for porting the Prime95 script to Python and for helping create and test the Google Colab Jupyter Notebooks!

Thanks to Ernst W. Mayer for helping test and for providing feedback on the Mlucas install script.

Thanks to Isaac Terrell for providing the needed PRP proof files to test the proof file uploading feature.
