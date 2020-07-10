#!/bin/bash

# Teal Dulcet
# wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/cudalucas.sh -qO - | bash -s --
# ./cudalucas.sh <PrimeNet Password> [PrimeNet User ID] [Type of work] [Idle time to run]
# ./cudalucas.sh <PrimeNet Password> "$USER" 100 10
# ./cudalucas.sh <PrimeNet Password> ANONYMOUS

DIR1="cudalucas"
DIR2="mlucas_v19/src"
FILE2="mlucas_v19.txz"
SUM="10906d3f1f4206ae93ebdb045f36535c"
if [[ $# -lt 1 || $# -gt 4 ]]; then
	echo "Usage: $0 <PrimeNet Password> [PrimeNet User ID] [Type of work] [Idle time to run]" >&2
	exit 1
fi
PASSWORD=$1
USERID=${2:-$USER}
TYPE=${3:-100}
TIME=${4:-10}
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
wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/idletime.sh -qO - | bash -s
if [[ -d "$DIR1" ]]; then
	echo "Error: CUDALucas is already downloaded" >&2
	exit 1
fi
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
echo -e "Downloading CUDALucas\n"
svn checkout https://svn.code.sf.net/p/cudalucas/code/trunk "$DIR1"
cd "$DIR1"
DIR=$PWD
echo -e "\nDownloading Mlucas\n"
wget https://www.mersenneforum.org/mayer/src/$FILE2
if [[ ! "$(md5sum $FILE2 | head -c 32)" == "$SUM" ]]; then
    echo "Error: md5sum does not match" >&2
    echo "Please run \"rm -r $DIR\" and try running this script again" >&2
	exit 1
fi
echo -e "\nDecompressing the files\n"
tar -xvf $FILE2
cp "$DIR2/primenet.py" primenet.py
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
sed -i 's/r"rogram"/r"CUDALucas"/' primenet.py
sed -i 's/^workfile = os.path.join(workdir, "worktodo.ini")/workfile = os.path.join(workdir, "worktodo.txt")/' primenet.py
# make debug
make
make clean
echo -e "\nStarting PrimeNet\n"
nohup python2 primenet.py -d -T "$TYPE" -u "$USERID" -p "$PASSWORD" &
sleep 1
echo -e "\nOptimizing CUDALucas for your computer and GPU\nThis may take awhile…\n"
./CUDALucas -cufftbench 1024 8192 5
./CUDALucas -threadbench 1024 8192 5 0
# echo -e "\nRunning self tests\nThis will take awhile…\n"
# ./CUDALucas -r 1
# ./CUDALucas 6972593
echo -e "\nStarting CUDALucas\n"
nohup nice ./CUDALucas &
sleep 1
echo -e "\nSetting it to start if the computer has not been used in the specified idle time and stop it when someone uses the computer\n"
#crontab -l | { cat; echo "cd $DIR && nohup nice ./CUDALucas &"; } | crontab -
#crontab -l | { cat; echo "cd $DIR && nohup python2 primenet.py -d -T \"$TYPE\" -u \"$USERID\" -p \"$PASSWORD\" &"; } | crontab -
crontab -l | { cat; echo "* * * * * if who -s | awk '{ print \$2 }' | (cd /dev && xargs -r stat -c '\%U \%X') | awk '{if ('\"\${EPOCHSECONDS:-\$(date +\%s)}\"'-\$2<$TIME) { print \$1\"\t\"'\"\${EPOCHSECONDS:-\$(date +\%s)}\"'-\$2; ++count }} END{if (count>0) { exit 1 }}' > /dev/null; then pgrep CUDALucas > /dev/null || (cd $DIR && nohup nice ./CUDALucas &); pgrep -f '^python2 primenet\.py' > /dev/null || (cd $DIR && nohup python2 primenet.py -d -T \"$TYPE\" -u \"$USERID\" -p \"$PASSWORD\" &); else pgrep CUDALucas > /dev/null && killall CUDALucas; fi"; } | crontab -
