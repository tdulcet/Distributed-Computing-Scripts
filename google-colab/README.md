# Google Colabatory and GIMPS
Google offers a service known as [Google Colabatory](https://research.google.com/colaboratory/faq.html) which allows for free access to 
a high-performance GPU-powered Jupyter Notebook and additionally a CPU-powered Jupyter Notebook. 

The service can be used to run Distributed Computing projects such as the [GIMPS project](https://www.mersenne.org/) at 
no cost to the user. GIMPS can be ran on a GPU using a software implementation called 
[CUDALucas](https://sourceforge.net/projects/cudalucas/) or ran on a CPU using the [Prime95](https://www.mersenne.org/download/) implementation.

This repository contains two Jupyter Notebooks, a CPU notebook and a GPU notebook. The CPU notebook runs `Prime95`. The GPU notebook runs both `CUDALucas` and `Prime95` 
as the GPU and the CPU can use each respective software in parallel to "crunch" prime numbers. Each notebook makes use of Google Drive storage, which is provided to Gmail users by default. 

## How to Use
With minor exceptions, Jupyter Notebooks require exactly the same input from a user. 

0. **(Optional): [Create an account on Mersenne.org**](https://www.mersenne.org/update/).

1. **Open The GPU Notebook in Colab:** [![Open GPU Notebook In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Danc2050/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabGPU.ipynb) or **Open The CPU Notebook in Colab** [![Open CPU Notebook In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Danc2050/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabCPU.ipynb).
If not already signed in, sign in to your Google Account in the upper right-hand corner. 

2. **(Optional, Suggested)** Save a copy of the notebook (ctrl + s) to your drive to avoid a warning each time you run the notebook.

3. **If Running The GPU** notebook, you must enable the GPU runtime: `Runtime -> Change Runtime Type -> Hardware accelerator -> GPU -> SAVE`. 

4. **Run/Click The First Cell**. The first cell is required to be run the very first time one sets up the cell on their Google Colab notebook 
and should not need to be run again if this process is successful. 

5. **Follow The link** Google provides to authorize the login to your drive account. Copy-and-paste the authorization string into the textbox Google provides within the notebook's output box.
(**Note**: You will need to perform this step each time you connect to a Colab notebook).

6. **When The Notebook Disconnects** -- for example due to its [12-hour](https://research.google.com/colaboratory/faq.html#idle-timeouts)
usage limit, a bad internet connection, Google requiring your GPU type, etc. -- you must run/click the second cell on subsequent runs of the notebook to continue where the software left off.

7. **Please Note:** you must keep each browser window **OPEN** in your browser in order to avoid notebooks shutting off due to being perceived as idle.

8. **(Optional):** Run the third cell to see what NVIDIA GPU is assigned to your notebook and see the progress of CUDALucas.

9. **(Optional): [Pin the tab in Firefox]**(https://support.mozilla.org/en-US/kb/pinned-tabs-keep-favorite-websites-open) for easy access to the Colab window(s).

## Required Tools, Restrictions
As long as a user has a Gmail account, a Google Drive that has ~50MB of free space, an internet connection, and a reliable browser,
anyone can use both notebooks to crunch primes using the GPU and CPU notebook.

Please note that with the free version of Colab, a 12-hour usage limit exists. Additionally, a user may only connect to 2 notebooks at a time
and only one of these notebooks may run a GPU.

The 12-hour usage limit is lifted if one purchases a [Google Colab Pro](https://colab.research.google.com/) plan.

## GPUs Offered
Google runs exclusively on NVIDIA GPUs. The GPUs offered by Google depend on the needs of Google, so the GPU assigned to you will vary.
To determine what GPU one has in the current environment, run the third cell.

The first (and most powerful) GPU that is offered is the `Tesla T4`. However, there are other GPU models that Google will assign you:

```
Tesla P4
Tesla K80
Tesla P100-PCIE-16GB
```
Though each GPU works well and will complete any assignment in a matter of days, one may use the following method to attain a new GPU:
`Runtime -> Factory reset runtime -> YES`. After repeating 1-3 times, this method will assign a new GPU.
