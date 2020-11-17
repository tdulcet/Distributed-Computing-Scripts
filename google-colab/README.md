# Google Colabatory and GIMPS
Google offers a service known as [Colabatory](https://research.google.com/colaboratory/faq.html) (Colab), which allows for free access to 
a high-performance GPU and CPU-powered [Jupyter Notebooks](https://en.wikipedia.org/wiki/Project_Jupyter#Jupyter_Notebook).

This service can be used to run Distributed Computing projects such as the [Great Internet Mersenne Prime Search](https://www.mersenne.org/) (GIMPS) 
at no cost to the user. GIMPS can be run on an Nvidia GPU using the [CUDALucas](https://sourceforge.net/projects/cudalucas/) program
or a CPU using the [Prime95](https://www.mersenne.org/download/) program.

This repository contains two Jupyter Notebooks, a "CPU" notebook and a "GPU and CPU" notebook. The CPU notebook runs `Prime95`. The "GPU and CPU" notebook runs both `CUDALucas` and `Prime95` 
since they can run in parallel to "crunch" more prime numbers. Each notebook makes use of Google Drive storage, which is provided to all Google accounts.

## How to Use
**Please Note:** you must keep each notebook **OPEN** in your browser to prevent them from shutting off due to being perceived as idle.

1. **Choose Your Persistent Storage Option** We recommend copying the source of our respective ["GPU and CPU" notebook](GoogleColabGPU.ipynb) and/or [CPU notebook](GoogleColabCPU.ipynb), pasting each one into one or more [new notebooks](http://colab.research.google.com/#create=true) in Colab and then uniquely naming and saving the notebook(s) (<kbd>Ctrl</kbd> + <kbd>s</kbd>). Next, on the far left, click "📁", the "Mount Drive" button and select "CONNECT TO GOOGLE DRIVE". Your drive storage should automatically remount each time you run the notebook(s). Optionally, see the official [video](https://video.twimg.com/tweet_video/EQbtltjVAAA2qTs.mp4) for a walkthrough. <details>
    <summary>Alternative Method</summary>
    You may open a notebook using the link for your respective intention(s): Open "GPU and CPU" notebook: <a href="https://colab.research.google.com/github/tdulcet/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabGPU.ipynb"> <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="GPU-CPU-Notebook"></a> and/or open the CPU notebook: <a href="https://colab.research.google.com/github/tdulcet/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabCPU.ipynb"> <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="CPU-Notebook"></a>. You will also want to save a copy of the notebook to your drive using <kbd>Ctrl</kbd> + <kbd>s</kbd> to avoid a warning each time you run the notebook. *WARNINGS*: This method will continually require an authorization step each time you connect to the notebook. When authorizing, follow the link Google provides to authorize the login to your drive account. Copy-and-paste the authorization string into the textbox Google provides within the notebook's output box. 
</details>

2. **If Running the GPU** notebook, you must enable the GPU runtime: `Runtime → Change Runtime Type → Hardware accelerator → GPU → SAVE`. 

3. **Run/Click ▶** to run the GIMPS project anonymously. Alternatively, fill in the fields with your Mersenne.org user credentials.

4. **When the Notebook Disconnects** – for example due to its [12-hour](https://research.google.com/colaboratory/faq.html#idle-timeouts)
usage limit, a bad internet connection, Google requiring your GPU type, etc. – after the usage limit is over, follow step 3 again to continue where the software left off.

Google may offer you two GPU runtimes to disperse among two of the notebooks assigned to you. In this case, you may run another CUDALucas job by re-running the notebook with a different `computer_number` option. For example, choose `2` if you are already running a notebook with the `Default (1)` number.

## Optional 
A user may optionally perform other steps to gain more insight into GIMPS and/or this software:

1. Create an account on [Mersenne.org](https://www.mersenne.org/update/).

2. Set the `debug` option to view the output of a respective GIMPS program. Alternatively, you may access the `gpu1.out`,  `gpu2.out`, `cpu1.out`…`cpuN.out`, and `nohup.out` files in your Google drive under the `cudalucas` or `mprime_gpu`/`mprime_cpu` folders to manually see the CUDALucas and/or Prime95 progress respectively.

3. Pin the tab(s) in [Firefox](https://support.mozilla.org/en-US/kb/pinned-tabs-keep-favorite-websites-open) for easy access to the Colab notebook(s).

## Required Tools, Restrictions
Anyone with a free Google/Gmail account with [~50 MiB of free space](https://www.google.com/settings/storage) on Google Drive and an internet connection can use both our "GPU and CPU" and "CPU" notebooks to "crunch" primes.

Please note, though the [resource limits](https://research.google.com/colaboratory/faq.html#resource-limits) are at times variable, generally the free version of Colab imposes a 12-hour usage limit per notebook. (This usage limit, the GPU runtime limit, and other usage limits are modified if one purchases a [Google Colab Pro](https://colab.research.google.com/) plan.).
Additionally, a user may only assign a GPU runtime to two notebooks at a time whereas one may run an unknown upper-bound of notebooks with the CPU runtime enabled.

## GPUs Offered
Google Colab runs exclusively on Nvidia GPUs where the model assigned to you depends on availability. The 
most [powerful GPU](https://www.mersenne.ca/cudalucas.php) currently offered is the `Tesla V100-SXM2-16GB`.  

To determine which GPU one has in the current environment, set the `debug` option to `GPU (CUDALucas)` and run the cell.
Some possible GPUs that may be assigned are listed below for reference:

```
Tesla P100-PCIE-16GB
Tesla K80
Tesla T4
Tesla P4
```

Though each GPU works well and will complete most assignments in a matter of days, one may use the following method to attain a new GPU:
`Runtime → Factory reset runtime → YES`. After repeating 1-3 times, Google will usually assign a new type of GPU.

## Acknowledgements
These notebooks acknowledge the following projects which enabled + encouraged us to create these notebooks:
* [our scripts](/../../#organizations), which automatically download, build and setup the respective GIMPS programs on Colab.
* [GPU72](https://www.gpu72.com/), whose work encouraged us to also use the [form](https://colab.research.google.com/notebooks/forms.ipynb) format.

## Donate

To support this endeavor, please consider making a [donation](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=NJ4PULABRVNCC).
