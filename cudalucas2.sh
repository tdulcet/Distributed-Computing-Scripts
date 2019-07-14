#!/bin/bash

# Teal Dulcet
# wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/cudalucas2.sh -qO - | bash -s --
# ./cudalucas2.sh <Computer number> <PrimeNet Password> [PrimeNet User ID] [Type of work] [Idle time to run]
# ./cudalucas2.sh <N> <PrimeNet Password> "$USER" 100 10
# ./cudalucas2.sh <N> <PrimeNet Password> ANONYMOUS

DIR1="cudalucas"
DIR2="mlucas_v18/src"
FILE2="mlucas_v18.txz"
SUM="a3ab997df7d7246b29e47a851088d2a5"
if [[ "$#" -lt 2 || "$#" -gt 5 ]]; then
	echo "Usage: $0 <Computer number> <PrimeNet Password> [PrimeNet User ID] [Type of work] [Idle time to run]" >&2
	exit 1
fi
N=$1
PASSWORD=$2
USERID=${3:-$USER}
TYPE=${4:-100}
TIME=${5:-10}
RE='^[0-9]+$'
if ! [[ $N =~ $RE ]]; then
	echo "Usage: <Computer number> must be a number" >&2
	exit 1
fi
RE='^[0-9]{3}$'
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
echo -e "PrimeNet Password:\t$PASSWORD"
echo -e "Type of work:\t\t$TYPE"
echo -e "Idle time to run:\t$TIME minutes\n"
GPU=$(lspci | grep -i 'vga\|3d\|2d')
if ! echo "$GPU" | grep -iq 'nvidia'; then
	echo -e "Please enter your password when prompted.\n"
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
	echo -e "Please enter your password when prompted.\n"
	sudo apt-get update -y
	sudo apt-get install subversion -y
fi
if ! command -v nvcc >/dev/null; then
	echo -e "Installing the Nvidia CUDA Toolkit"
	echo -e "Please enter your password when prompted.\n"
	sudo apt-get update -y
	sudo apt-get install nvidia-cuda-toolkit -y
fi
TIME=$(echo "$TIME" | awk '{ printf "%g", $1 * 60 }')
if [[ -d "$DIR1" && -x "$DIR1/CUDALucas" ]]; then
	echo -e "CUDALucas is already downloaded\n"
	cd "$DIR1"
else
	echo -e "Downloading CUDALucas\n"
	svn checkout https://svn.code.sf.net/p/cudalucas/code/trunk "$DIR1"
	cd "$DIR1"
	echo -e "\nSetting up CUDALucas\n"
	sed -i 's/^OptLevel = 1/OptLevel = 3/' Makefile
	CUDA=$(command -v nvcc | sed 's/\/bin\/nvcc$//')
	sed -i "s/^CUDA = \/usr\/local\/cuda/CUDA = ${CUDA//\//\\/}/" Makefile

	# Adapted from: https://stackoverflow.com/a/37757606
	cat << EOF > /tmp/cudaComputeVersion.cu
#include <stdio.h>
int main()
{
	cudaDeviceProp prop;
	cudaError_t status = cudaGetDeviceProperties(&prop, 0);
	if (status != cudaSuccess) { 
		fprintf(stderr, "cudaGetDeviceProperties() for device 0 failed: %s\n", cudaGetErrorString(status)); 
		return 1;
	}
	int v = prop.major * 10 + prop.minor;
	printf("--generate-code arch=compute_%d,code=sm_%d\n", v, v);
	return 0;
}
EOF

	# nvcc /tmp/cudaComputeVersion.cu -o /tmp/cudaComputeVersion -O3 --compiler-options=-Wall
	nvcc /tmp/cudaComputeVersion.cu -O3 -D_FORCE_INLINES --compiler-options=-Wall -o /tmp/cudaComputeVersion
	if ! COMPUTE=$(/tmp/cudaComputeVersion); then
		echo "$COMPUTE"
		echo "Error: CUDA compute capability not found" >&2
		exit 1
	fi
	rm /tmp/cudaComputeVersion.cu
	rm /tmp/cudaComputeVersion
	# sed -i "s/--generate-code arch=compute_35,code=sm_35/$COMPUTE/" Makefile
	sed -i "s/--generate-code arch=compute_35,code=sm_35/$COMPUTE -D_FORCE_INLINES/" Makefile
	sed -i '/nvmlInit();/d' CUDALucas.cu
	sed -i '/nvmlDevice_t device;/d' CUDALucas.cu
	sed -i '/nvmlDeviceGetHandleByIndex(device_number, &device);/d' CUDALucas.cu
	sed -i '/nvmlDeviceGetUUID(device, uuid, sizeof(uuid)\/sizeof(uuid\[0\]));/d' CUDALucas.cu
	sed -i '/nvmlShutdown();/d' CUDALucas.cu
	awk -i inplace '{print} /workdir/ && !x {print "parser.add_option(\"-i\", \"--workfile\", dest=\"workfile\", default=\"worktodo.txt\", help=\"WorkFile filename, default %(default)\")"; x=1}' primenet.py
	sed -i 's/^workfile = os.path.join(workdir, "worktodo.ini")/workfile = os.path.join(workdir, options.workfile)/' primenet.py
	make
	make clean
fi
DIR=$(pwd)
if [[ -d "$DIR2" && -f "$DIR2/primenet.py" ]]; then
	echo -e "Mlucas is already downloaded\n"
else
	echo -e "\nDownloading Mlucas\n"
	wget https://www.mersenneforum.org/mayer/src/C/$FILE2
	if [[ ! "$(md5sum $FILE2 | head -c 32)" = "$SUM" ]]; then
		echo "Error: md5sum does not match" >&2
		echo "Please run \"rm -r $DIR\" and try running this script again" >&2
		exit 1
	fi
	echo -e "\nDecompressing the files\n"
	tar -xvf $FILE2
	cp "$DIR2/primenet.py" primenet.py
fi
cp CUDALucas.ini "CUDALucas$N.ini"
sed -i "s/^WorkFile=worktodo.txt/WorkFile=worktodo$N.txt/" "CUDALucas$N.ini"
echo -e "\nStarting PrimeNet\n"
nohup python primenet.py -d -T "$TYPE" -u "$USERID" -p "$PASSWORD" -i "worktodo$N.txt" &
sleep 1
echo -e "\nOptimizing CUDALucas for your computer and GPU\nThis may take awhile…\n"
./CUDALucas -cufftbench 1024 8192 5
./CUDALucas -threadbench 1024 8192 5 0
# echo -e "\nRunning self tests\nThis will take awhile…\n"
# ./CUDALucas -r 1
# ./CUDALucas 6972593
echo -e "\nStarting CUDALucas\n"
nohup nice ./CUDALucas -i "CUDALucas$N.ini" &
sleep 1
echo -e "\nSetting it to start if the computer has not been used in the specified idle time and stop it when someone uses the computer\n" | fold -s -w "$(tput cols)"
#crontab -l | { cat; echo "cd $DIR && nohup nice ./CUDALucas -i \"CUDALucas$N.ini\" &"; } | crontab -
#crontab -l | { cat; echo "cd $DIR && nohup python primenet.py -d -T \"$TYPE\" -u \"$USERID\" -p \"$PASSWORD\" -i \"worktodo$N.txt\" &"; } | crontab -
crontab -l | { cat; echo "* * * * * if who -s | awk '{ print \$2 }' | (cd /dev && xargs -r stat -c '\%U \%X') | awk '{if ('\"\$(date +\%s)\"'-\$2<$TIME) { print \$1\"\t\"'\"\$(date +\%s)\"'-\$2; ++count }} END{if (count>0) { exit 1 }}' > /dev/null; then pgrep CUDALucas > /dev/null || (cd $DIR && nohup nice ./CUDALucas -i \"CUDALucas$N.ini\" &); pgrep -f '^python primenet\.py' > /dev/null || (cd $DIR && nohup python primenet.py -d -T \"$TYPE\" -u \"$USERID\" -p \"$PASSWORD\" -i \"worktodo$N.txt\" &); else pgrep CUDALucas > /dev/null && killall CUDALucas; fi"; } | crontab -
