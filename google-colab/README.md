# Google Colaboratory and GIMPS
Google offers a service known as [Colaboratory](https://research.google.com/colaboratory/faq.html) (Colab), which allows anyone with an internet connection free access to high-performance TPU, GPU and CPU-powered [Jupyter Notebooks](https://en.wikipedia.org/wiki/Project_Jupyter#Jupyter_Notebook).
This service can be used to run Distributed Computing projects such as the [Great Internet Mersenne Prime Search](https://www.mersenne.org/) (GIMPS) for free.
GIMPS can be run on some Nvidia, AMD and Intel GPUs using the [GpuOwl](https://github.com/preda/gpuowl) program or a CPU using the [Prime95](https://www.mersenne.org/download/) program.

This repository contains two Jupyter Notebooks, a “CPU” only notebook (`GoogleColabCPU.ipynb`) and a “GPU and CPU” notebook (`GoogleColabGPU.ipynb`). The “CPU” only notebook runs Prime95, while the “GPU and CPU” notebook runs both GpuOwl and Prime95 since they can run simultaneously to “crunch” more prime numbers. Previous versions of the GPU notebook ran CUDALucas.
Each notebook makes use of Google Drive storage, which is provided to all Google accounts. See [here](https://github.com/TPU-Mersenne-Prime-Search/TensorPrime/wiki/Usage-and-Arguments) for a “TPU” only notebook which runs TensorPrime.

## How to Use
**Please Note:** you must keep each notebook **OPEN** in your browser to prevent it from disconnecting due to being perceived as idle. [Pin the tab(s)](https://support.mozilla.org/en-US/kb/pinned-tabs-keep-favorite-websites-open) or move them to a dedicated window for easy access to your notebook(s).

1. **Choose a Persistent Storage Option** Recommend Method: Copy the source of our respective [“GPU and CPU” notebook](GoogleColabGPU.ipynb) and/or [“CPU” notebook](GoogleColabCPU.ipynb), pasting them into one or more [new notebooks](http://colab.research.google.com/#create=true) in Colab. Then, uniquely name and save the notebook(s) (<kbd>Ctrl</kbd> + <kbd>s</kbd>). Then, on the far left, click “📁”, the “Mount Drive” folder button and select “CONNECT TO GOOGLE DRIVE”. Your Drive storage should automatically remount each time you run the notebook(s). You may need to repeat this last part after a while. See the official [video](https://video.twimg.com/tweet_video/EQbtltjVAAA2qTs.mp4) for a walkthrough.
<details>
    <summary>Alternative Method</summary>
    Open “GPU and CPU” notebook: <a href="https://colab.research.google.com/github/tdulcet/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabGPU.ipynb"> <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="GPU-CPU-Notebook"></a> and/or the “CPU” only notebook: <a href="https://colab.research.google.com/github/tdulcet/Distributed-Computing-Scripts/blob/master/google-colab/GoogleColabCPU.ipynb"> <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="CPU-Notebook"></a> in Colab. Then, uniquely name and save a copy to your Drive (<kbd>Ctrl</kbd> + <kbd>s</kbd>) to avoid a warning each time you run the notebook. *WARNINGS*: This method will continually require an authorization step each time you run the notebook(s). After step 4 below, follow the link Google provides to authorize the login to your Drive and copy-and-paste the authorization string into the textbox Google provides within the notebook's output box.
</details>

2. **If Running the GPU** notebook, you must enable the GPU runtime. On the upper left, click “Runtime” → “Change runtime type”, under “Hardware accelerator” select “GPU” and click “SAVE”.

3. Leave the default options to run anonymously. Alternatively, fill in your GIMPS/PrimeNet account user ID and set any other desired options. Each instance of a notebook type needs to have a unique `computer_number` value. Note that the PRP worktypes can use several GiB of your Drive storage. Every lower value will halve Drive storage requirements for PRP tests, but double the certification cost. Set the highest `prp_proof_power` value that you have available Drive storage for (see below for the space needed for several proof powers and exponents).

4. **Click** “▶️” to run the notebook.

5. **When the Notebook Disconnects** – for example due to its [12-hour](https://research.google.com/colaboratory/faq.html#idle-timeouts)
usage limit, idle timeouts, Google requiring your GPU type, etc. – repeat step 4 again to continue where you left off. Use our [Colab Autorun and Connect](https://github.com/tdulcet/Colab-Autorun-and-Connect) Firefox and Chrome add-on/extension to automate this step.

Google may offer you up to two GPU runtimes to disperse among your notebooks. In this case, you may create another GPU notebook by re-running the steps with a different `computer_number` value. For example, choose `2` if you are already running a GPU notebook with the `Default (1)` number.

## Optional
A user may optionally perform other steps to gain more insight into GIMPS and/or this software:

1. Create a GIMPS/PrimeNet account [here](https://www.mersenne.org/update/) and [join](https://www.mersenne.org/jteam/) the “Portland State University” team!

2. Set the `debug` option to view the last 100 lines of output and the status from the respective GIMPS program. Alternatively, you may access the `cpu1.out`…`cpuN.out`, `1/gpu.out`…`N/gpu.out`, and `1/primenet.out`…`N/primenet.out` files, where `N` is the `computer_number` value, in your Google Drive under the `GIMPS` and `mprime_gpu`/`mprime_cpu` or `gpuowl` folders to see the full Prime95 and/or GpuOwl output respectively.

## Required Tools, Restrictions
Anyone with an internet connection and a free Google/Gmail account with just [~50 MiB of free space](https://www.google.com/settings/storage) on Google Drive can use both our notebooks to “crunch” primes.

Drive storage (GiB) needed to store the proof interim residues file during each PRP test:

Proof Power | Exp 50M | Exp 100M | Exp 150M | Exp 200M | Exp 250M | Exp 300M | Exp 332.1M (100M digits) | Exp 1,000M (PrimeNet limit)
--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---:
5 | 0.186 | 0.372 | 0.558 | 0.745 | 0.931 | 1.117 | 1.237 | **3.725**
6 | 0.372 | 0.745 | 1.117 | 1.49 | 1.862 | 2.235 | 2.475 | 7.45
7 | 0.745 | 1.49 | 2.235 | **2.98** | **3.725** | **4.47** | **4.95** | 14.9
8 | 1.49^ | **2.98**^ | **4.47**^ | 5.96^ | 7.45^ | 8.94^ | 9.9^ | 29.8^
9 | ***2.98*** | *5.96* | 8.94 | 11.9 | 14.9 | 17.88 | 19.8 | 59.6
10 | 5.96 | 11.92 | *17.88* | *23.84* | *29.8* | *35.76* | *39.6* | 119.2
11 | 11.92 | 23.84 | 35.76 | 47.68 | 59.6 | 71.52 | 79.2 | *238.4*
12 | 23.84 | 47.68 | 71.52 | 95.36 | 119.2 | 143 | 158.4 | 476.8

Drive storage (MiB) needed to generate proof file at the end of each PRP test:

Proof Power | Proof Power Multiplier | Certification Cost | Exp 50M | Exp 100M | Exp 150M | Exp 200M | Exp 250M | Exp 300M | Exp 332.1M | Exp 1,000M
--- | --- |  --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---:
5 | 1 | 1⁄32 | 35.76 | 71.52 | 107.2 | 143 | 178.8 | 214.5| 237.6 | 715.2
\- | 2 | 1⁄64 | 71.52 | 143 | 214.5 | 286.1 | 357.6 | 429.1 | 475.2 | 1430
\- | 3 | 1⁄128 | 107.2 | 214.5 | 321.8 | 429.1 | 536.4 | 643.7 | 712.8 | **2145**
\- | 4 | 1⁄256 | 143 | 286.1 | 429.1 | 572.2 | 715.2 | 858.3 | 950.4 | 2861
6 | 1 | 1⁄64 | 41.72 | 83.44 | 125.1 | 166.8 | 208.6 | 250.3 | 277.2 | 834.4
\- | 2 | 1⁄128 | 83.44 | 166.8 | 250.3 | 333.7 | 417.2 | 500.6 | 554.4 | 1668
\- | 3 | 1⁄256 | 125.1 | 250.3 | 375.5 | 500.6 | 625.8 | 751 | 831.6 | 2503
\- | 4 | 1⁄512 | 166.8 | 333.7 | 500.6 | 667.5 | 834.4 | 1001 | 1108 | 3337
7 | 1 | 1⁄128 | 47.68 | 95.36 | 143 | 190.7 | 238.4 | 286.1 | 316.8 | 953.6
\- | 2 | 1⁄256 | 95.36 | 190.7 | 286.1 | **381.4** | **476.8** | **572.2** | **633** | 1907
\- | 3 | 1⁄512 | 143 | 286.1 | 429.1 | 572.2 | 715.2 | 858.3 | 950 | 2861
\- | 4 | 1⁄1024 | 190.7 | 381.4 | 572.2 | 762.9 | 953.6 | 1144 | 1267 | 3814
8 | 1 | 1⁄256 | 53.6^ | **107.2**^ | **160.9**^ | 214.5^ | 268.2^ | 321.8^ | 356.4^ | 1072^
\- | 2 | 1⁄512 | 107.2 | 214.5 | 321.8 | 429.1 | 536.4 | 643.7 | 712.8 | 2145
\- | 3 | 1⁄1024 | 160.9 | 321.8 | 482.7 | 643.7 | 804.6 | 965.5 | 1069 | 3218
\- | 4 | 1⁄2048 | 214.5 | 429.1 | 643.7 | 858.3 | 1072.8 | 1287 | 1425 | 4291
9 | 1 | 1⁄512 | ***59.6*** | *119.2* | 178.8 | 238.4 | 298 | 357.6 | 396 | 1192
\- | 2 | 1⁄1024 | 119.2 | 238.4 | 357.6 | 476.8 | 596 | 715.2 | 792 | 2384
\- | 3 | 1⁄2048 | 178.8 | 357.6 | 536.4 | 715.2 | 894 | 1072 | 1188 | 3576
\- | 4 | 1⁄4096 | 238.4 | 476.8 | 715.2 | 953.6 | 1192 | 1430 | 19.8 | 4768
10 | 1 | 1⁄1024 | 65.56 | 131.1 | *196.6* | *262.2* | *327.82* | *393.3* | *1584* | 1311
\- | 2 | 1⁄2048 | 131.1 | 262.2 | 393.3 | 524.5 | 655.6 | 786.7 | 435.6 | 2622
\- | 3 | 1⁄4096 | 196.6 | 393.3 | 590 | 786.7 | 983.4 | 1180 | 871.2 | 3933
11 | 1 | 1⁄2048 | 71.52 | 143 | 214.5 | 286.1 | 357.6 | 429.1 | 1742 | *1430*
\- | 2 | 1⁄4096 | 143 | 286.1 | 429.1 | 572.2 | 715.2 | 858.3 | 475.2 | 2861
12 | 1 | 1⁄4096 | 77.48 | 154.9 | 232.4 | 309.9 | 387.4 | 464.9 | 514.8 | 1549

**Bold** - Prime95 default proof power and multiplier, uses a maximum of 6 GB (5.587 GiB) per exponent\
*Italic* - Optimal proof power, 9 for exponents above 26.6M, 10 above 106.5M and 11 above 414.2M\
^ GpuOwl default proof power, uses 8 for all exponents

Please note, though the [resource limits](https://research.google.com/colaboratory/faq.html#resource-limits) are at times variable, generally the free version of Colab imposes a 12-hour usage limit per notebook. 
Additionally, a user may only assign a GPU runtime to up to two notebooks at a time whereas one may run an unknown upper-bound of notebooks with the CPU runtime enabled. 
(This usage limit, the GPU runtime limit, and other usage limits are increased if one purchases a [Colab Pro or Colab Pro+](https://colab.research.google.com/signup) plan.)

## GPUs Offered
Google Colab provides Nvidia GPUs where the specific model assigned to you depends on availability.
The most [powerful GPU](https://www.mersenne.ca/cudalucas.php) currently offered is the `NVIDIA A100-SXM4-40GB`.

The possible GPUs that may be assigned are listed below:

GPU | Speed (MHz) | CUDA cores | GPU Memory (GiB) | Single precision/F32 (TFLOPS) | Double precision/F64 (TFLOPS)
--- | ---: | ---: | ---: | ---: | ---:
Tesla P4 | 810 - 1063 | 2560 | 8 | 4.15 - 5.44 | 0.129 - 0.17
Tesla T4 | 585 - 1590 | 2560 | 16 | 8.1 | 0.254
Tesla K80 | 560 - 875 | 2496 | 12 | 2.8 - 4.37 | 0.932 - 1.46
Tesla P100-PCIE-16GB | 1126 - 1303 | 3584 | 16 | 8.07 - 9.34 | 4.04 - 4.67
Tesla V100-SXM2-16GB | 1455 | 5120 | 16 | 14.8 | 7.45
NVIDIA A100-SXM4-40GB | 765 - 1410 | 6912 | 40 | 19.5 | 9.7

See the [gpu_optimizations](gpu_optimizations) directory for more information about each GPU, including the ms/iter speeds for CUDALucas at different FFT lengths.

Though each GPU works well and will complete most assignments in a matter of days, one may use the following method to attain a new GPU:
“Runtime” → “Factory reset runtime” → “YES”. After repeating 1-3 times, Google will usually assign a new GPU.

## Acknowledgements
We acknowledge the following projects, which enabled and encouraged us to create these notebooks:
* [Our Bash install scripts](/../../#organizations), which automatically download, build and setup the respective GIMPS programs on Colab.
* [Our PrimeNet Python script](/../../#primenet), which automatically gets assignments, reports assignment results and progress for CUDALucas and GpuOwl using the PrimeNet API. Adapted from the PrimeNet Python script from [Mlucas](https://www.mersenneforum.org/mayer/README.html#download2) by Loïc Le Loarer and Ernst W. Mayer.
* The [GPU72 notebook](https://github.com/chalsall/GPU72_CoLab), whose work encouraged us to also use the [form](https://colab.research.google.com/notebooks/forms.ipynb) format.
* The [Linux System Information script](https://github.com/tdulcet/Linux-System-Information), which outputs the system information for the Colab VMs.

## ❤️ Donate
To support this endeavor, please consider making a [donation](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=NJ4PULABRVNCC).
