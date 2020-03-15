# Nvidia GPU

The program is compiled with a specific GPU -- the GPU that is available
at runtime. However, GPUs vary in Google Colab a little.

Typically, only one GPU is offered for 12 hours. This GPU can be seen by
typing the  command:

`!nvidia-smi --query-gpu=gpu_name --format=csv`

The first (and most powerful) GPU that is offered should be labeled:

```
name
Tesla T4
```

However, there may be another GPU that Google will assign you when the
12-hour period has been exhausted:

```
name
Tesla P100-PCIE-16GB
```

This will not run CUDALucas as the compilation, as mentioned, has been done
for the T4 GPU (if it has).

At the moment, the solution is to simply wait 12-hours until the T4 GPU
becomes available to you, though future plans are in the works.
