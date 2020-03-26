# Nvidia GPU

The program is compiled with a specific GPU -- the GPU that is available
at runtime. However, GPUs vary in Google Colab a little.

Typically, only one GPU is offered for 12 hours. This GPU can be seen by
typing the  command:

`!nvidia-smi --query-gpu=gpu_name --format=csv,noheader`

The first (and most powerful) GPU that is offered should be labeled:

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
