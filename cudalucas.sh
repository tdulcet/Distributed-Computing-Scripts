#!/bin/bash

# Teal Dulcet
# wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/cudalucas.sh -qO - | bash -s --
# ./cudalucas.sh [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
# ./cudalucas.sh "$USER" "$HOSTNAME" 100 10
# ./cudalucas.sh ANONYMOUS

DIR="cudalucas"
if [[ $# -gt 4 ]]; then
	echo "Usage: $0 [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]" >&2
	exit 1
fi
USERID=${1:-$USER}
COMPUTER=${2:-$HOSTNAME}
TYPE=${3:-100}
TIME=${4:-10}
DEVICE=0
RE='^10[0124]$'
if ! [[ $TYPE =~ $RE ]]; then
	echo "Usage: [Type of work] must be a number" >&2
	exit 1
fi
RE='^([0-9]*[.])?[0-9]+$'
if ! [[ $TIME =~ $RE ]]; then
	echo "Usage: [Idle time to run] must be a number" >&2
	exit 1
fi
echo -e "PrimeNet User ID:\t$USERID"
echo -e "Computer name:\t\t$COMPUTER"
echo -e "Type of work:\t\t$TYPE"
echo -e "Idle time to run:\t$TIME minutes\n"
if [[ -e idletime.sh ]]; then
	bash -- idletime.sh
else
	wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/idletime.sh -qO - | bash -s
fi
if [[ -d "$DIR" ]]; then
	echo "Error: CUDALucas is already downloaded" >&2
	exit 1
fi
GPU=$(lspci | grep -i 'vga\|3d\|2d')
if ! echo "$GPU" | grep -iq 'nvidia'; then
	echo -e "Please enter your password if prompted.\n"
	sudo update-pciids
	GPU=$(lspci | grep -i 'vga\|3d\|2d')
	if ! echo "$GPU" | grep -iq 'nvidia'; then
		echo "$GPU" | sed -n 's/^.*: //p'
		echo "Error: This computer does not have an Nvidia GPU" >&2
		exit 1
	fi
fi
if ! command -v svn >/dev/null; then
	echo -e "Installing Apache Subversion"
	echo -e "Please enter your password if prompted.\n"
	sudo apt-get update -y
	sudo apt-get install subversion -y
fi
if ! command -v nvcc >/dev/null; then
	echo -e "Installing the Nvidia CUDA Toolkit"
	echo -e "Please enter your password if prompted.\n"
	sudo apt-get update -y
	sudo apt-get install nvidia-cuda-toolkit -y
fi
if ! command -v python3 >/dev/null; then
	echo "Error: Python 3 is not installed." >&2
	exit 1
fi
TIME=$(echo "$TIME" | awk '{ printf "%g", $1 * 60 }')
echo -e "Downloading CUDALucas\n"
svn checkout https://svn.code.sf.net/p/cudalucas/code/trunk "$DIR"
cd "$DIR"
DIR=$PWD
echo -e "\nDownloading the PrimeNet script\n"
if [[ -e ../primenet.py ]]; then
	cp -v ../primenet.py .
else
	wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/primenet.py -nv
fi
python3 -m pip install --upgrade pip
if command -v pip3 >/dev/null; then
	echo -e "\nInstalling the Requests library\n"
	pip3 install requests
else
	echo -e "\nWarning: pip3 is not installed and the Requests library may also not be installed\n"
fi
echo -e "\nSetting up CUDALucas\n"
# sed -i 's/\r//g' Makefile
sed -i 's/^OptLevel = 1/OptLevel = 3/' Makefile
CUDA=$(command -v nvcc | sed 's/\/bin\/nvcc$//')
sed -i "s/^CUDA = \/usr\/local\/cuda/CUDA = ${CUDA//\//\\/}/" Makefile
# sed -i '/^LDFLAGS / s/$/ -lstdc++/' Makefile

# Adapted from: https://stackoverflow.com/a/37757606
cat << EOF > /tmp/cudaComputeVersion.cu
#include <stdio.h>
int main()
{
	cudaDeviceProp prop;
	cudaError_t status = cudaGetDeviceProperties(&prop, $DEVICE);
	if (status != cudaSuccess) { 
		fprintf(stderr, "cudaGetDeviceProperties() for device $DEVICE failed: %s\n", cudaGetErrorString(status)); 
		return 1;
	}
	const int v = prop.major * 10 + prop.minor;
	printf("--generate-code arch=compute_%d,code=sm_%d\n", v, v);
	return 0;
}
EOF

trap 'rm /tmp/cudaComputeVersion.cu /tmp/cudaComputeVersion' EXIT
# nvcc /tmp/cudaComputeVersion.cu -o /tmp/cudaComputeVersion -O3 --compiler-options=-Wall
nvcc /tmp/cudaComputeVersion.cu -O3 -D_FORCE_INLINES --compiler-options=-Wall -o /tmp/cudaComputeVersion
if ! COMPUTE=$(/tmp/cudaComputeVersion); then
	echo "$COMPUTE"
	echo "Error: CUDA compute capability not found" >&2
	exit 1
fi
# sed -i "s/--generate-code arch=compute_35,code=sm_35/$COMPUTE/" Makefile
sed -i "s/--generate-code arch=compute_35,code=sm_35/$COMPUTE -D_FORCE_INLINES/" Makefile
sed -i '/nvmlInit();/d' CUDALucas.cu
sed -i '/nvmlDevice_t device;/d' CUDALucas.cu
sed -i '/nvmlDeviceGetHandleByIndex(device_number, &device);/d' CUDALucas.cu
sed -i '/nvmlDeviceGetUUID(device, uuid, sizeof(uuid)\/sizeof(uuid\[0\]));/d' CUDALucas.cu
sed -i '/nvmlShutdown();/d' CUDALucas.cu
# Increase buffers to prevent buffer overflow
sed -i 's/file\[32\]/file[268]/g' CUDALucas.cu
sed -i 's/file_bak\[64\]/file_bak[268]/g' CUDALucas.cu
# make debug
make
make clean
echo -e "\nRegistering computer with PrimeNet\n"
ARGS=()
if command -v nvidia-smi >/dev/null && nvidia-smi >/dev/null; then
	mapfile -t GPU < <(nvidia-smi --query-gpu=gpu_name --format=csv,noheader)
	ARGS+=( --cpu_model="${GPU[DEVICE]}" )
	
	mapfile -t GPU_FREQ < <(nvidia-smi --query-gpu=clocks.max.gr --format=csv,noheader,nounits | grep -iv 'not supported')
	if [[ -n "$GPU_FREQ" ]]; then
		ARGS+=( --frequency="${GPU_FREQ[DEVICE]}" )
	fi
	
	mapfile -t TOTAL_GPU_MEM < <(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | grep -iv 'not supported')
	if [[ -n "$TOTAL_GPU_MEM" ]]; then
		ARGS+=( -m "${TOTAL_GPU_MEM[DEVICE]}" )
	fi
fi
python3 primenet.py -d -t 0 -T "$TYPE" -u "$USERID" -i "worktodo.txt" --cudalucas "cudalucas.out" -H "$COMPUTER" "${ARGS[@]}"
echo -e "\nStarting PrimeNet\n"
nohup python3 primenet.py -d -t 21600 >> "primenet.out" &
sleep 1
echo -e "\nOptimizing CUDALucas for your computer and GPU\nThis may take a while…\n"
./CUDALucas -cufftbench 1024 8192 5
./CUDALucas -threadbench 1024 8192 5 0
echo -e "\nRunning self tests\nThis will take a while…\n"
./CUDALucas -r 1
# ./CUDALucas 6972593
echo -e "\nStarting CUDALucas\n"
nohup nice ./CUDALucas -d $DEVICE >> "cudalucas.out" &
sleep 1
echo -e "\nSetting it to start if the computer has not been used in the specified idle time and stop it when someone uses the computer\n"
#crontab -l | { cat; echo "cd '$DIR' && nohup nice ./CUDALucas -d $DEVICE >> 'cudalucas.out' &"; } | crontab -
#crontab -l | { cat; echo "cd '$DIR' && nohup python3 primenet.py -d -t 21600 >> 'primenet.out' &"; } | crontab -
crontab -l | { cat; echo "* * * * * if who -s | awk '{ print \$2 }' | (cd /dev && xargs -r stat -c '\%U \%X') | awk '{if ('\"\${EPOCHSECONDS:-\$(date +\%s)}\"'-\$2<$TIME) { print \$1\"\t\"'\"\${EPOCHSECONDS:-\$(date +\%s)}\"'-\$2; ++count }} END{if (count>0) { exit 1 }}' >/dev/null; then pgrep -x CUDALucas >/dev/null || (cd '$DIR' && nohup nice ./CUDALucas -d $DEVICE >> 'cudalucas.out' &); pgrep -f '^python3 primenet\.py' >/dev/null || (cd '$DIR' && nohup python3 primenet.py -d -t 21600 >> 'primenet.out' &); else pgrep -x CUDALucas >/dev/null && killall CUDALucas; fi"; } | crontab -
