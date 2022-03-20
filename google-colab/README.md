# Google Colaboratory and GIMPS
Google offers a service known as [Colaboratory](https://research.google.com/colaboratory/faq.html) (Colab), which allows anyone with an internet connection free access to high-performance TPU, GPU and CPU-powered [Jupyter Notebooks](https://en.wikipedia.org/wiki/Project_Jupyter#Jupyter_Notebook).
This service can be used to run Distributed Computing projects such as the [Great Internet Mersenne Prime Search](https://www.mersenne.org/) (GIMPS) for free.
GIMPS can be run on an Nvidia GPU using the [CUDALucas](https://sourceforge.net/projects/cudalucas/) program or a CPU using the [Prime95](https://www.mersenne.org/download/) program.

This repository contains two Jupyter Notebooks, a “CPU” only notebook (`GoogleColabCPU.ipynb`) and a “GPU and CPU” notebook (`GoogleColabGPU.ipynb`). The “CPU” only notebook runs `Prime95`, while the “GPU and CPU” notebook runs both `CUDALucas` and `Prime95` since they can run simultaneously to “crunch” more prime numbers.
Each notebook makes use of Google Drive storage, which is provided to all Google accounts. See [here](https://github.com/TPU-Mersenne-Prime-Search/TensorPrime/wiki/Usage-and-Arguments) for a “TPU” only notebook which runs `TensorPrime`.

## How to Use
**Please Note:** you must keep each notebook **OPEN** in your browser to prevent it from disconnecting due to being perceived as idle. [Pin the tab(s)](https://support.mozilla.org/en-US/kb/pinned-tabs-keep-favorite-websites-open) or move them to a dedicated window for easy access to your notebook(s).

1. **Choose a Persistent Storage Option** Recommend Method: Copy the source of our respective [“GPU and CPU” notebook](GoogleColabGPU.ipynb) and/or [“CPU” notebook](GoogleColabCPU.ipynb), pasting them into one or more [new notebooks](http://colab.research.google.com/#create=true) in Colab. Then, uniquely name and save the notebook(s) (<kbd>Ctrl</kbd> + <kbd>s</kbd>). Next, on the upper right, click “Connect”. Then, on the far left, click “📁”, the “Mount Drive” folder button and select “CONNECT TO GOOGLE DRIVE”. Your Drive storage should automatically remount each time you run the notebook(s). You may need to repeat this last part after a month. See the official [video](https://video.twimg.com/tweet_video/EQbtltjVAAA2qTs.mp4) for a walkthrough.
<details>
    <summary>Alternative Method</summary>
    Open “GPU and CPU” notebook: <a href="https://colab.research.google.com/github/tdulcet/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabGPU.ipynb"> <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="GPU-CPU-Notebook"></a> and/or the “CPU” only notebook: <a href="https://colab.research.google.com/github/tdulcet/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabCPU.ipynb"> <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="CPU-Notebook"></a> in Colab. Then, uniquely name and save a copy to your Drive (<kbd>Ctrl</kbd> + <kbd>s</kbd>) to avoid a warning each time you run the notebook. *WARNINGS*: This method will continually require an authorization step each time you run the notebook(s). After step 4 below, follow the link Google provides to authorize the login to your Drive and copy-and-paste the authorization string into the textbox Google provides within the notebook's output box.
</details>

2. **If Running the GPU** notebook, you must enable the GPU runtime. On the upper left, click “Runtime” → “Change runtime type”, under “Hardware accelerator” select “GPU” and click “SAVE”.

3. Leave the default options to run anonymously. Alternatively, fill in your GIMPS/PrimeNet account user ID and set any other desired options. Each instance of a notebook type needs to have a unique `computer_number` value. Note that the PRP worktypes can use several GiB of your Drive storage. The `prp_proof_power` defaults to 8 for Prime95. Every lower value will halve Drive storage requirements for PRP tests, but double the certification cost. Set the highest `prp_proof_power` value that you have available Drive storage for (see the [Prime95 README](https://www.mersenne.org/download/#download) for the space needed for several proof powers and exponents).

4. **Click** “▶️” to run the notebook.

5. **When the Notebook Disconnects** – for example due to its [12-hour](https://research.google.com/colaboratory/faq.html#idle-timeouts)
usage limit, idle timeouts, Google requiring your GPU type, etc. – repeat step 4 again to continue where you left off. Use our [Colab Autorun and Connect](https://github.com/tdulcet/Colab-Autorun-and-Connect) Firefox and Chrome add-on/extension to automate this step.

Google may offer you up to two GPU runtimes to disperse among your notebooks. In this case, you may create another GPU notebook by re-running the steps with a different `computer_number` value. For example, choose `2` if you are already running a GPU notebook with the `Default (1)` number.

## Optional
A user may optionally perform other steps to gain more insight into GIMPS and/or this software:

1. Create a GIMPS/PrimeNet account [here](https://www.mersenne.org/update/) and [join](https://www.mersenne.org/jteam/) the “Portland State University” team!

2. Set the `debug` option to view the last 100 lines of output and the status from the respective GIMPS program. Alternatively, you may access the `cpu1.out`…`cpuN.out`, `gpu1.out`…`gpuN.out`, and `primenet1.out`…`primenetN.out` files, where `N` is the `computer_number` value, in your Google Drive under the `GIMPS` and `mprime_gpu`/`mprime_cpu` or `cudalucas` folders to see the full Prime95 and/or CUDALucas output respectively.

## Required Tools, Restrictions
Anyone with an internet connection and a free Google/Gmail account with just [~50 MiB of free space](https://www.google.com/settings/storage) on Google Drive can use both our notebooks to “crunch” primes.

Please note, though the [resource limits](https://research.google.com/colaboratory/faq.html#resource-limits) are at times variable, generally the free version of Colab imposes a 12-hour usage limit per notebook. 
Additionally, a user may only assign a GPU runtime to up to two notebooks at a time whereas one may run an unknown upper-bound of notebooks with the CPU runtime enabled. 
(This usage limit, the GPU runtime limit, and other usage limits are increased if one purchases a [Colab Pro or Colab Pro+](https://colab.research.google.com/signup) plan.)

## GPUs Offered
Google Colab runs exclusively on Nvidia GPUs where the specific model assigned to you depends on availability.
The most [powerful GPU](https://www.mersenne.ca/cudalucas.php) currently offered is the `Tesla V100-SXM2-16GB`.

The other possible GPUs that may be assigned are listed below:

```
Tesla P100-PCIE-16GB
Tesla K80
Tesla T4
Tesla P4
```
See the [gpu_optimizations](gpu_optimizations) directory for more information about each GPU, including the ms/iter speeds for CUDALucas at different FFT lengths.

Though each GPU works well and will complete most assignments in a matter of days, one may use the following method to attain a new GPU:
`Runtime → Factory reset runtime → YES`. After repeating 1-3 times, Google will usually assign a new GPU.

## Acknowledgements
We acknowledge the following projects, which enabled and encouraged us to create these notebooks:
* [Our Bash install scripts](/../../#organizations), which automatically download, build and setup the respective GIMPS programs on Colab.
* [Our PrimeNet Python script](/../../#primenet), which automatically gets assignments, reports assignment results and progress for CUDALucas and GpuOwl using the PrimeNet API. Adapted from the PrimeNet Python script from [Mlucas](https://www.mersenneforum.org/mayer/README.html#download2) by Loïc Le Loarer and Ernst W. Mayer.
* The [GPU72 notebook](https://github.com/chalsall/GPU72_CoLab), whose work encouraged us to also use the [form](https://colab.research.google.com/notebooks/forms.ipynb) format.
* The [Linux System Information script](https://github.com/tdulcet/Linux-System-Information), which outputs the system information for the Colab VMs.

## ❤️ Donate
To support this endeavor, please consider making a [donation](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=NJ4PULABRVNCC).
