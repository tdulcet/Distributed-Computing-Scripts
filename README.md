[![Actions Status](https://github.com/tdulcet/Distributed-Computing-Scripts/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/tdulcet/Distributed-Computing-Scripts/actions/workflows/ci.yml)

# Distributed Computing Scripts
Distributed Computing Scripts for GIMPS, BOINC and Folding@home

Copyright © 2018 Teal Dulcet and Daniel Connelly

❤️ Please visit [tealdulcet.com](https://www.tealdulcet.com/) to support these scripts and my other software development.

## Great Internet Mersenne Prime Search (GIMPS)

🆕 Thanks to Google's [Colaboratory](https://colab.research.google.com/) (Colab) service, anyone with an internet connection can now contribute to GIMPS for 🆓, without downloading or installing anything! Please see our [google-colab](google-colab) directory for instructions.

### Prime95/MPrime

Downloads, sets up and runs [Prime95/MPrime](https://www.mersenne.org/download/#download). Supports only x86 CPUs.

```
wget -qO - https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mprime.sh | bash -s -- [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
```

To run MPrime for Stress/Torture Testing, see the [Testing and Benchmarking](https://github.com/tdulcet/Testing-and-Benchmarking-Scripts) scripts.

### CUDALucas

Downloads, builds, sets up and runs [CUDALucas](https://sourceforge.net/p/cudalucas/code/HEAD/tree/trunk/). Downloads, sets up and runs [AutoPrimeNet](https://github.com/tdulcet/AutoPrimeNet) for automated PrimeNet assignments.

```
wget -qO - https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/cudalucas.sh | bash -s -- [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
```

### Mlucas

Downloads, builds, sets up and runs [Mlucas](https://www.mersenneforum.org/mayer/README.html#download1). Downloads, sets up and runs [AutoPrimeNet](https://github.com/tdulcet/AutoPrimeNet) for automated PrimeNet assignments. Supports x86 Intel and AMD and ARM CPUs, but only recommended for ARM CPUs, which [Prime95/MPrime](#prime95mprime) does not support. Prime95/MPrime is faster than Mlucas on x86 CPUs. Run: `wget -qO - https://raw.github.com/tdulcet/Linux-System-Information/master/info.sh | bash -s` to output your system information, including CPU and architecture.
This script follows the recommended instructions on the [Mlucas README](https://www.mersenneforum.org/mayer/README.html) for each architecture and CPU.

```
wget -qO - https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mlucas.sh | bash -s -- [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
```

### GpuOwl

Downloads, builds, sets up and runs the latest version of [GpuOwl](https://github.com/preda/gpuowl) for PRP tests, version 7.2-112 for PRP tests with combined P-1 and the [v6 branch](https://github.com/preda/gpuowl/tree/v6) for LL and standalone P-1 tests. Downloads, sets up and runs [AutoPrimeNet](https://github.com/tdulcet/AutoPrimeNet) for automated PrimeNet assignments. Creates wrapper script to run the correct version of GpuOwl based on the next assignment. Supports Nvidia, AMD and Intel GPUs supporting OpenCL. Note that [GpuOwl uses C++20](https://github.com/preda/gpuowl#build) and thus requires at least the GNU C++ compiler 8. Run: `g++ --version` to output your version.

```
wget -qO - https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/gpuowl.sh | bash -s -- [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
```

### PrimeNet

AutoPrimeNet (the Python PrimeNet program) was moved to a [separate repository](https://github.com/tdulcet/AutoPrimeNet).

### Organizations

For installing on multiple computers to a shared or network directory. Developed for use by the [PSU Computer Science Graduate Student Organization](https://gso.cs.pdx.edu/programs/). Also used by our [Google Colab Jupyter Notebooks](google-colab).

#### Prime95/MPrime

```
wget -qO - https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mprime2.sh | bash -s -- <Computer number> [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
```

#### CUDALucas

```
wget -qO - https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/cudalucas2.sh | bash -s -- <Computer number> [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
```

#### GpuOwl

```
wget -qO - https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/gpuowl2.sh | bash -s -- <Computer number> [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
```

## BOINC

Downloads, installs and sets up [BOINC](https://boinc.berkeley.edu/download.php).

```
wget -qO - https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/boinc.sh | bash -s -- <Project URL> <E-mail> <Password>
```

OR

```
wget -qO - https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/boinc.sh | bash -s -- <Project URL> <Account Key>
```

This script can be used with any [project that uses BOINC](https://boinc.berkeley.edu/projects.php).

## Folding@home

Downloads, installs and sets up [Folding@home](https://foldingathome.org/start-folding/).

```
wget -qO - https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/folding.sh | bash -s -- [Username] [Team number] [Passkey] [Power]
```

These scripts should work on Ubuntu, Debian and any Linux distribution that can use the apt package manager.

## Contributing

Pull requests welcome! Ideas for contributions:

* Create install script for the [CUDAPm1](https://sourceforge.net/projects/cudapm1/) GIMPS program
* Update install scripts to support CLI options
* Add options for setting the maximum CPU time
* Update CUDALucas to support PRP tests and the Jacobi error check for LL tests
* Update Mlucas to support the Jacobi error check for LL and P-1 tests
* Finish and improve the performance of [TensorPrime](https://github.com/TPU-Mersenne-Prime-Search/TensorPrime), the [Tensor Processing Unit](https://en.wikipedia.org/wiki/Tensor_Processing_Unit) (TPU) GIMPS program (see [here](https://github.com/TPU-Mersenne-Prime-Search/TensorPrime/wiki#results-and-next-steps))

Thanks to [Daniel Connelly](https://github.com/Danc2050) for porting the MPrime script to Python and for helping create and test the Google Colab Jupyter Notebooks!
