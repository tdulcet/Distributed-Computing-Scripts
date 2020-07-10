[![Build Status](https://travis-ci.org/tdulcet/Distributed-Computing-Scripts.svg?branch=master)](https://travis-ci.org/tdulcet/Distributed-Computing-Scripts)
[![Actions Status](https://github.com/tdulcet/Distributed-Computing-Scripts/workflows/CI/badge.svg?branch=master)](https://github.com/tdulcet/Distributed-Computing-Scripts/actions)

# Distributed Computing Scripts
Linux Distributed Computing Scripts

Copyright © 2018 Teal Dulcet

## Great Internet Mersenne Prime Search (GIMPS)

### Prime95/MPrime

Downloads, sets up and runs [Prime95](https://www.mersenne.org/download/#download).

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mprime.sh -qO - | bash -s -- [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
```

To run Prime95 for Stress/Torture Testing, see the [Testing and Benchmarking](https://github.com/tdulcet/Testing-and-Benchmarking-Scripts) scripts.

### CUDALucas

Downloads, builds, sets up and runs [CUDALucas](https://sourceforge.net/p/cudalucas/code/HEAD/tree/trunk/). Downloads, sets up and runs the Python script from [Mlucas](https://www.mersenneforum.org/mayer/README.html#download) for automated PrimeNet assignments.

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/cudalucas.sh -qO - | bash -s -- <PrimeNet Password> [PrimeNet User ID] [Type of work] [Idle time to run]
```

### Mlucas

Downloads, builds, sets up and runs [Mlucas](https://www.mersenneforum.org/mayer/README.html#download). Supports x86 Intel and AMD and ARM CPUs, but only recommended for ARM CPUs, which [Prime95/MPrime](#prime95mprime) does not support. Prime95/MPrime is faster than Mlucas on x86 CPUs. Run: `wget https://raw.github.com/tdulcet/Linux-System-Information/master/info.sh -qO - | bash -s` to output your system information, including CPU and architecture.
This script follows the recommended instructions on the [Mlucas README](https://www.mersenneforum.org/mayer/README.html) for each architecture and CPU and is currently for testing only.

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mlucas.sh -qO - | bash -s -- <PrimeNet Password> [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
```

### Organizations

For installing on multiple computers to a shared or network directory. Developed for use by the [PSU Computer Science Graduate Student Organization](https://gso.cs.pdx.edu/programs/).

#### Prime95/MPrime

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mprime2.sh -qO - | bash -s -- <Computer number> [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
```

#### CUDALucas

```
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/cudalucas2.sh -qO - | bash -s -- <Computer number> <PrimeNet Password> [PrimeNet User ID] [Type of work] [Idle time to run]
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

These scripts should work on Ubuntu and any Linux distribution that can use the apt package manager.

## Contributing

Pull requests welcome!
