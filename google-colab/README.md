# Google Colabatory and GIMPS
Google offers a service known as [Colabatory](https://research.google.com/colaboratory/faq.html) (Colab), which allows for free access to 
a high-performance GPU and CPU-powered [Jupyter Notebooks](https://en.wikipedia.org/wiki/Project_Jupyter#Jupyter_Notebook).

This service can be used to run Distributed Computing projects such as the [Great Internet Mersenne Prime Search](https://www.mersenne.org/) (GIMPS) 
at no cost to the user. GIMPS can be run on an Nvidia GPU using the [CUDALucas](https://sourceforge.net/projects/cudalucas/) program
or a CPU using the [Prime95](https://www.mersenne.org/download/) program.

This repository contains two Jupyter Notebooks, a "CPU" notebook and a "GPU and CPU" notebook. The CPU notebook runs `Prime95`. The "GPU and CPU" notebook runs both `CUDALucas` and `Prime95` 
since they can run in parallel to "crunch" more prime numbers. Each notebook makes use of Google Drive storage, which is provided to all Google accounts.

## How to Use
**Please Note:** you must keep each notebook **OPEN** in your browser in order to prevent them from shutting off due to being perceived as idle.

1. **Choose Your Persistent Storage Option** We recommend copying the source code of the respective [CPU notebook](https://github.com/Danc2050/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabCPU.ipynb) or ["GPU and CPU" notebook](https://github.com/Danc2050/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabGPU.ipynb), pasting this into a [new notebook](http://colab.research.google.com/#create=true), and naming + saving the notebook(s). On the far left, click "📁", the "Mount Drive" button and select "CONNECT TO GOOGLE DRIVE". Your drive storage should remount automatically each time you run the notebook(s).
<details>
    <summary>Alternative Method</summary>
    You may open a notebook using the link for your respective intention(s): Open "GPU and CPU" notebook: [![Open GPU Notebook In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Danc2050/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabGPU.ipynb) and/or open the CPU notebook: [![Open CPU Notebook In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Danc2050/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabCPU.ipynb). You will also want to save a copy of the notebook to your drive using <kbd>Ctrl</kbd> + <kbd>s</kbd> to avoid a warning each time you run the notebook. *WARNINGS* This method will continually require an authorization step each time you connect to the notebook. When authorizing, follow the link Google provides to authorize the login to your drive account. Copy-and-paste the authorization string into the textbox Google provides within the notebook's output box. If not already signed in, sign in to your Google Account in the upper right-hand corner.
</details>

2. **If Running the GPU** notebook, you must enable the GPU runtime: `Runtime → Change Runtime Type → Hardware accelerator → GPU → SAVE`. 

3. **Run/Click the ▶** to run the GIMPS project annonymously. Alternatively, fill in the fields with your Mersenne.org user credentials.

4. **When the Notebook Disconnects** -- for example due to its [12-hour](https://research.google.com/colaboratory/faq.html#idle-timeouts)
usage limit, a bad internet connection, Google requiring your GPU type, etc. -- you must press the `reconnect` button and potentially start steps 2-3 again to continue where the software left off.

5. **Starting a 2nd GPU-powered Notebook** Google may offer you two GPUs between the two notebooks allotted to you. If you would like to run another CUDALucas job, change the `computer_number` from `Default (1)` to `2`.

## Optional 
A user may optionally perform other steps to gain more insight into GIMPS and/or this software:

1. Create an account on [Mersenne.org](https://www.mersenne.org/update/).

2. In a GPU-powered notebook, set the `debug` option to view the output of a respective GIMPS programs output and which Nvidia GPU is assigned to your notebook. Alternatively, you may access the `gpu1.out`,  `gpu2.out`, and the `cpu1.out` files in your Google drive under the `cudalucas` or `mprime\_gpu/` folders to manually see the CUDALucas and/or Prime95 progress respectively.

3. Pin the tab(s) in [Firefox](https://support.mozilla.org/en-US/kb/pinned-tabs-keep-favorite-websites-open) for easy access to the Colab notebook(s).

## Required Tools, Restrictions
As long as they have a Google/Gmail account, a Google Drive with ~50MB of free space, an internet connection, and a browser,
a user can use both the "GPU and CPU" and CPU notebooks to crunch primes.

Please note that with the free version of Colab, a 12-hour usage limit exists per notebook. The 12-hour usage limit is lifted if one purchases a [Google Colab Pro](https://colab.research.google.com/) plan. 
Additionally, a user may only connect to two notebooks at a time, and only one of these notebooks may run a GPU. 

## GPUs Offered
Google runs exclusively on Nvidia GPUs. The GPU model assigned to you will depend on availability.
To determine which GPU one has in the current environment, run the cell with the `debug` option set to `True`.

The most [powerful GPU](https://www.mersenne.ca/cudalucas.php) that is currently offered is the `Tesla P100-PCIE-16GB`. However, Google will assign other GPU models to you:

```
Tesla K80
Tesla T4
Tesla P4
```

Though each GPU works well and will complete most assignments in a matter of days, one may use the following method to attain a new GPU:
`Runtime → Factory reset runtime → YES`. After repeating 1-3 times, Google will usually assign a new type of GPU.
