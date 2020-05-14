# GIMPS and Google Colabatory
Google offers a service known as [Google Colabatory](https://research.google.com/colaboratory/faq.html) which allows for free access to 
a high-performance GPU-powered Jupyter Notebook and additionally a CPU-powered Jupyter Notebook. The service can
be used to run Distributed Computing projects, such as the [GIMPS project](https://www.mersenne.org/), at 
no cost to the user.

GIMPS can be ran on a GPU, using a software implementation called [CUDALucas](https://sourceforge.net/projects/cudalucas/) or using a CPU
, using the [Prime95](https://www.mersenne.org/download/) implementation.

This repository contains two Jupyter Notebooks that install and run each software respectively on Google Colab. 
Each notebook makes use of Google Drive storage, which is provided to Gmail users by default. 

## How to Use
There are two cells in each GPU and CPU Jupyter Notebook. Each are structured similarly, but contain their own instructions.

### The GPU Notebook: Special Instructions
If running the GPU notebook, you must enable the GPU runtime as, by default, it is not enabled on a notebook.

0. Click `Runtime`.
1. Select `Change Runtime Type`.
2. Under `Hardware accelerator` select `GPU` and press `SAVE`.
3. Follow the instructions below.

### General Instructions

With exception to the special instructions listed above, both Jupyter Notebooks require exactly the same input from a user. 

0. **(Optional): [Create an account on Mersenne.org**](https://www.mersenne.org/update/).

1. [![Open GPU Notebook In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Danc2050/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabGPU.ipynb).

or 

[![Open CPU Notebook In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Danc2050/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabCPU.ipynb).

If not already, sign in to your Google Account (upper right-hand corner).

2. **Run/click the first cell**. The first cell is required to be run the very first time one sets up the cell on their Google Colab notebook 
and should not need to be run again if this process is successful. 

3. Follow the link and follow the instructions at the link's location. Copy-and-paste the authorization string into the textbox Google provides in the notebook.

4. When the notebook disconnects -- for example due to its [12-hour](https://research.google.com/colaboratory/faq.html#idle-timeouts)
usage limit, a bad internet connection, Google requiring a GPU, etc. -- you must run/click the second cell on subsequent runs of the notebook to continue where the software left off.

5. **Please Note:** you must keep each browser window OPEN in your browser in order to avoid notebooks shutting off due to being perceived as idle.

6. **(Optional):** Run the third cell to see what NVIDIA GPU is assigned to your notebook.

7. **(Optional): [Pin the tab in Firefox**](https://support.mozilla.org/en-US/kb/pinned-tabs-keep-favorite-websites-open) for easy access to the Colab window(s).

# Required Tools and Restrictions

As long as a user has a Gmail account, a Google Drive that has ~50MB of free space, an internet connection, and a reliable browser,
anyone can use both notebooks to crunch primes using the GPU and CPU notebook.

Please note that with the free version of Colab, a 12-hour usage limit exists. Additionally, a user may only connect to 2 notebooks at a time
and only one of these notebooks may run a GPU.

The 12-hour usage limit is lifted if one purchases a [Google Colab Pro](https://colab.research.google.com/) plan.

# NVIDIA GPU (INCOMPLETE)

Google runs exclusively on NVIDIA GPUs. The GPUs offered by Google depend on the needs of Google, so the GPU assigned to you will vary.

The GPU notebook compiles CUDALucas with the GPU that is available at runtime. 

To determine what GPU one has in the current environment, run the third cell named `DEBUG`.

The first (and most powerful) GPU that is offered is:

```
Tesla T4
```

However, there are other GPU models that Google will assign you when the
12-hour period has been exhausted:

```
Tesla P4
```

```
Tesla K80
```

```
Tesla P100-PCIE-16GB
```

In the case of `Tesla P100-PCIE-16GB` CUDALucas will not run as the compilation has been done
for the T4 GPU. The other GPUs still operate on the CUDALucas compiled for the T4 GPU.

At the moment, the tried-and-true solution is disconnect the VM and reconnect it. Often, this method
will assign a compatible GPU. Future plans are in the works to re-work the CUDALucas script
to allow for this variation in GPU assignment.

# Using the GPU and CPU

It is also possible to run the two notebook's software in parallel; that is, CUDALucas and Prime95 within the same notebook. In order to do this:

1. Install CUDALucas and Prime95 using each respective notebook
2. **TODO** -- Teal, do we want to run by default or give them a line to insert?
