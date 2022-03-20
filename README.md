[![Build Status](https://travis-ci.com/tdulcet/Distributed-Computing-Scripts.svg?branch=master)](https://travis-ci.com/tdulcet/Distributed-Computing-Scripts)
[![Actions Status](https://github.com/tdulcet/Distributed-Computing-Scripts/workflows/CI/badge.svg?branch=master)](https://github.com/tdulcet/Distributed-Computing-Scripts/actions)

# Distributed Computing Scripts
Distributed Computing Scripts

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

Downloads, builds, sets up and runs [CUDALucas](https://sourceforge.net/p/cudalucas/code/HEAD/tree/trunk/). Downloads, sets up and runs our [PrimeNet Python script](#primenet) for automated PrimeNet assignments.

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/cudalucas.sh -qO - | bash -s -- [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
```

### Mlucas

Downloads, builds, sets up and runs [Mlucas](https://www.mersenneforum.org/mayer/README.html#download1). Downloads, sets up and runs our [PrimeNet Python script](#primenet) for automated PrimeNet assignments. Supports x86 Intel and AMD and ARM CPUs, but only recommended for ARM CPUs, which [Prime95/MPrime](#prime95mprime) does not support. Prime95/MPrime is faster than Mlucas on x86 CPUs. Run: `wget https://raw.github.com/tdulcet/Linux-System-Information/master/info.sh -qO - | bash -s` to output your system information, including CPU and architecture.
This script follows the recommended instructions on the [Mlucas README](https://www.mersenneforum.org/mayer/README.html) for each architecture and CPU.

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mlucas.sh -qO - | bash -s -- [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
```

### PrimeNet

Automatically gets assignments, reports assignment results and optionally progress to PrimeNet for the GpuOwl, CUDALucas and Mlucas GIMPS programs. Supports both Python 2 and 3 and Windows, macOS and Linux. Requires the [Requests library](https://requests.readthedocs.io/en/master/), which is included with many Python 3 installations. The script will automatically install Requests on first run if it is not already installed. GIMPS [discontinued first time LL assignments](https://mersenneforum.org/showthread.php?t=26682) in April 2021, although the script [still supports them](https://mersenneforum.org/showthread.php?p=575260#post575260) for users of CUDALucas or with limited disk space. Our [GpuOwl](#gpuowl), [CUDALucas](#cudalucas) and [Mlucas](#mlucas) Linux scripts automatically download, setup and run this. Adapted from the PrimeNet Python script from [Mlucas](https://www.mersenneforum.org/mayer/README.html#download2) by [Loïc Le Loarer](https://github.com/llloic11/primenet) and Ernst W. Mayer, which itself was adapted from primetools by [Mark Rose](https://github.com/MarkRose/primetools) and [teknohog](https://github.com/teknohog/primetools).

#### Usage

```
Usage: primenet.py [options]

This program will automatically get assignments, report assignment results and
optionally progress to PrimeNet for the GpuOwl, CUDALucas and Mlucas GIMPS
programs. It also saves its configuration to a “local.ini” file, so it is only
necessary to give most of the arguments the first time it is run. The first
time it is run, if a password is NOT provided, it will register the current
GpuOwl/CUDALucas/Mlucas instance with PrimeNet (see below). Then, it will get
assignments, report the results, upload any proofs and report the progress, if
registered, to PrimeNet on a “timeout” interval, or only once if timeout is 0.

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -d, --debug           Output detailed information. Provide multiple times
                        for even more verbose output.
  -w WORKDIR, --workdir=WORKDIR
                        Working directory with the local file from this
                        program, Default: . (current directory)
  -D DIRS, --dir=DIRS   Directories with the worktodo and results files from
                        the GIMPS program. Provide once for each worker
                        thread. It automatically sets the --cpu_num option for
                        each directory.
  -i WORKFILE, --workfile=WORKFILE
                        WorkFile filename, Default: “worktodo.ini”
  -r RESULTSFILE, --resultsfile=RESULTSFILE
                        ResultsFile filename, Default: “results.txt”
  -l LOCALFILE, --localfile=LOCALFILE
                        Local configuration file filename, Default:
                        “local.ini”
  --archive_proofs=PROOFARCHIVEDIR
                        Directory to archive PRP proof files after upload,
                        Default: none
  -u USERNAME, --username=USERNAME
                        GIMPS/PrimeNet User ID. Create a GIMPS/PrimeNet
                        account: https://www.mersenne.org/update/. If you do
                        not want a PrimeNet account, you can use ANONYMOUS.
  -p PASSWORD, --password=PASSWORD
                        Optional GIMPS/PrimeNet Password. Only provide if you
                        want to do manual testing and not report the progress.
                        This was the default behavior for old versions of this
                        script.
  -T WORKPREFERENCE, --worktype=WORKPREFERENCE
                        Type of work, Default: 100, 4 (P-1 factoring), 100
                        (smallest available first-time LL), 101 (double-check
                        LL), 102 (world-record-sized first-time LL), 104 (100M
                        digit number LL), 150 (smallest available first-time
                        PRP), 151 (double-check PRP), 152 (world-record-sized
                        first-time PRP), 153 (100M digit number PRP), 154
                        (smallest available first-time PRP that needs P-1
                        factoring), 155 (double-check using PRP with proof),
                        160 (first time Mersenne cofactors PRP), 161 (double-
                        check Mersenne cofactors PRP)
  --min_exp=GETMINEXPONENT
                        Minimum exponent to get from PrimeNet (2 -
                        999,999,999)
  --max_exp=GETMAXEXPONENT
                        Maximum exponent to get from PrimeNet (2 -
                        999,999,999)
  -g, --gpuowl          Get assignments for a GPU (GpuOwl) instead of the CPU
                        (Mlucas).
  --cudalucas=CUDALUCAS
                        Get assignments for a GPU (CUDALucas) instead of the
                        CPU (Mlucas). This option takes as an argument the
                        CUDALucas output filename.
  --num_workers=WORKERTHREADS
                        Number of worker threads (CPU Cores/GPUs), Default: 1
  -c CPU, --cpu_num=CPU
                        CPU core or GPU number to get assignments for,
                        Default: 0
  -n NUM_CACHE, --num_cache=NUM_CACHE
                        Number of assignments to cache, Default: 0
                        (automatically set to 1 when doing manual testing)
  -W DAYSOFWORK, --days_work=DAYSOFWORK
                        Days of work to queue (1-90 days), Default: 3.0 days.
                        Adds one to num_cache when the time left for the
                        current assignment is less then this number of days.
  --no_report_100m      Do not report any prime results for exponents greater
                        than 100 million digits. You must setup another method
                        to notify yourself.
  -t TIMEOUT, --timeout=TIMEOUT
                        Seconds to wait between network updates, Default: 3600
                        seconds (1 hour). Users with slower internet may want
                        to set a larger value to give time for any PRP proofs
                        to upload. Use 0 for a single update without looping.
  -s, --status          Output a status report and any expected completion
                        dates for all assignments and exit.
  --upload_proofs       Report assignment results, upload all PRP proofs and
                        exit. Requires PrimeNet User ID.
  --unreserve_all       Unreserve all assignments and exit. Quit GIMPS
                        immediately. Requires that the instance is registered
                        with PrimeNet.
  --no_more_work        Prevent script from getting new assignments and exit.
                        Quit GIMPS after current work completes.

  Registering Options: sent to PrimeNet/GIMPS when registering. The progress will automatically be sent and the program can then be monitored on the GIMPS website CPUs page (https://www.mersenne.org/cpus/), just like with Prime95/MPrime. This also allows for the program to get much smaller Category 0 and 1 exponents, if it meets the other requirements (https://www.mersenne.org/thresholds/).:
    -H COMPUTERID, --hostname=COMPUTERID
                        Computer name, Default: example
    --cpu_model=CPU_MODEL
                        Processor (CPU) model, Default: cpu.unknown
    --features=FEATURES
                        CPU features, Default: ''
    --frequency=CPUSPEED
                        CPU frequency/speed (MHz), Default: 1000 MHz
    -m MEMORY, --memory=MEMORY
                        Total memory (RAM) (MiB), Default: 0 MiB. Required for
                        P-1 assignments.
    --L1=L1             L1 Cache size (KiB), Default: 8 KiB
    --L2=L2             L2 Cache size (KiB), Default: 512 KiB
    --L3=L3             L3 Cache size (KiB), Default: 0 KiB
    --np=NUMCORES       Number of physical CPU cores, Default: 1
    --hp=CPUNUMHYPERTHREADS
                        Number of CPU threads per core (0 is unknown),
                        Default: 0. Choose 1 for non-hyperthreaded and 2 or
                        more for hyperthreaded.
    --hours=CPUHOURS    Hours per day you expect to run the GIMPS program (1 -
                        24), Default: 24 hours. Used to give better estimated
                        completion dates.
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

PrimeNet script:
* Support more GIMPS programs.
* Support reserving a specific exponent.
* Support setting more of the program options.
* Support setting per thread options.
    * Get different work types on different CPU cores or GPUs.
* Improve the error handling of PrimeNet API calls.
* Support the recovery of assignments if there is an error or the worktodo file was deleted.
* Check for new results to submit when the results file is updated.
* Automatically detect more system information using code from [psutil](https://github.com/giampaolo/psutil), so users do not have to manually determine and specify it.
	* Currently this requires using the Bash scripts.
* Improve the performance.
* Add an option to send the user an e-mail/text message if there is an error, if the GIMPS program has not made any progress in a while or if it found a prime, using the [Send Msg CLI/SendPy](https://github.com/tdulcet/Send-Msg-CLI).
* Support reporting interim residues.
* Calculate the rolling average.
* Support downloading certification assignments.
* Translate the output into other languages (see [here](https://mersenneforum.org/showthread.php?t=27046)).
* Adapt Loïc Le Loarer's [test suite](https://github.com/llloic11/primenet/tree/main/tests).

General:
* Create install script for the [GpuOwl](https://github.com/preda/gpuowl) GIMPS program
* Update install scripts to support CLI options
* Add options for setting the maximum CPU time
* Update CUDALucas to support PRP tests and the Jacobi error check for LL tests
* Update Mlucas to support the Jacobi error check for LL and P-1 tests

Thanks to [Daniel Connelly](https://github.com/Danc2050) for updating the PrimeNet Python script from Mlucas to eliminate the password requirement by getting assignments using the [PrimeNet API](http://v5.mersenne.org/v5design/v5webAPI_0.97.html) and to support reporting the assignment results and progress for CUDALucas using the PrimeNet API, for porting the Prime95 script to Python and for helping create and test the Google Colab Jupyter Notebooks!

Thanks to Ernst W. Mayer for helping test and for providing feedback on the Mlucas install script.

Thanks to Isaac Terrell for providing the needed PRP proof files to test the proof file uploading feature.
