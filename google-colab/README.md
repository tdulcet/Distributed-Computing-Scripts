# Google Colabatory and GIMPS
Google offers a service known as [Colabatory](https://research.google.com/colaboratory/faq.html) (Colab), which allows for free access to 
a high-performance GPU and CPU-powered [Jupyter Notebooks](https://en.wikipedia.org/wiki/Project_Jupyter#Jupyter_Notebook).

This service can be used to run Distributed Computing projects such as the [Great Internet Mersenne Prime Search](https://www.mersenne.org/) (GIMPS) 
at no cost to the user. GIMPS can be run on an Nvidia GPU using the [CUDALucas](https://sourceforge.net/projects/cudalucas/) program
or a CPU using the [Prime95](https://www.mersenne.org/download/) program.

This repository contains two Jupyter Notebooks, a CPU notebook and a GPU notebook. The CPU notebook runs `Prime95`. The GPU notebook runs both `CUDALucas` and `Prime95` 
since they both can run in parallel to "crunch" more prime numbers. Each notebook makes use of Google Drive storage, which is provided to all Google accounts.

## How to Use
**Please Note:** you must keep each notebook **OPEN** in your browser in order to prevent them from shutting off due to being perceived as idle.

1. **Open the GPU Notebook in Colab:** [![Open GPU Notebook In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Danc2050/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabGPU.ipynb) or **Open The CPU Notebook in Colab** [![Open CPU Notebook In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Danc2050/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabCPU.ipynb).
If not already signed in, sign in to your Google Account in the upper right-hand corner. 

2. **Save a Copy of the Notebook** (Ctrl + s) to your drive to avoid a warning each time you run the notebook.

3. **If Running the GPU** notebook, you must enable the GPU runtime: `Runtime -> Change Runtime Type -> Hardware accelerator -> GPU -> SAVE`. 

4. **Run/Click the First Cell**. The first cell is required to be run the very first time to set up the cell on their Google Colab notebook 
and should not need to be run again if this is successful. 

5. **Follow the link** Google provides to authorize the login to your drive account. Copy-and-paste the authorization string into the textbox Google provides within the notebook's output box.
(**Note**: You will need to perform this step each time you connect to a Colab notebook).

6. **When the Notebook Disconnects** -- for example due to its [12-hour](https://research.google.com/colaboratory/faq.html#idle-timeouts)
usage limit, a bad internet connection, Google requiring your GPU type, etc. -- you must run/click the second cell on subsequent runs of the notebook to continue where the software left off.

## Optional 
A user may optionally perform other steps to gain more insight into GIMPS and/or this software:

1. Create an account on [Mersenne.org](https://www.mersenne.org/update/).

2. In a GPU-powered notebook, run the third cell to see which Nvidia GPU is assigned to your notebook and see the progress CUDALucas has made.

3. Pin the tab in [Firefox](https://support.mozilla.org/en-US/kb/pinned-tabs-keep-favorite-websites-open) for easy access to the Colab notebook(s).

## Required Tools, Restrictions
As long as they have a Google/Gmail account, a Google Drive with ~50MB of free space, an internet connection, and a browser,
a user can use both GPU and CPU notebooks to crunch primes.

Please note that with the free version of Colab, a 12-hour usage limit exists. The 12-hour usage limit is lifted if one purchases a [Google Colab Pro](https://colab.research.google.com/) plan. 
Additionally, a user may only connect to two notebooks at a time and only one of these notebooks may run a GPU. 

## GPUs Offered
Google runs exclusively on Nvidia GPUs. The GPU model assigned to you will depend on availability.
To determine which GPU one has in the current environment, run the third cell.

The most [powerful GPU](https://www.mersenne.ca/cudalucas.php) that is currently offered is the `Tesla P100-PCIE-16GB`. However, Google will assign other GPU models to you:

```
Tesla K80
Tesla T4
Tesla P4
```

Though each GPU works well and will complete most assignments in a matter of days, one may use the following method to attain a new GPU:
`Runtime -> Factory reset runtime -> YES`. After repeating 1-3 times, this method will assign a new GPU.
