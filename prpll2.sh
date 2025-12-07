#!/bin/bash

# Copyright © 2020 Teal Dulcet
# wget -qO - https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/prpll2.sh | bash -s --
# ./prpll2.sh <Computer number> [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
# ./prpll2.sh <N> "$USER" "$HOSTNAME" 150 10
# ./prpll2.sh <N> ANONYMOUS

set -e

DIR="prpll"
BRANCH=master
if [[ $# -lt 1 || $# -gt 5 ]]; then
	echo "Usage: $0 <Computer number> [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]" >&2
	exit 1
fi
N=$1
USERID=${2:-$USER}
COMPUTER=${3:-$HOSTNAME}
TYPE=${4:-100}
TIME=${5:-10}
DEVICE=0
RE='^[0-9]+$'
if ! [[ $N =~ $RE ]]; then
	echo "Usage: <Computer number> must be a number" >&2
	exit 1
fi
RE='^1(0[01246]|5[01235])$'
if ! [[ $TYPE =~ $RE ]]; then
	echo "Usage: [Type of work] must be a number" >&2
	exit 1
fi
RE='^([0-9]*\.)?[0-9]+$'
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
	wget -qO - https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/idletime.sh | bash -s
fi
GPU=$(lspci | grep -i 'vga\|3d\|2d')
if ! echo "$GPU" | grep -iq 'amd\|nvidia\|intel'; then
	echo -e "Please enter your password if prompted.\n"
	sudo update-pciids
	GPU=$(lspci | grep -i 'vga\|3d\|2d')
	if ! echo "$GPU" | grep -iq 'amd\|nvidia\|intel'; then
		echo "$GPU" | sed -n 's/^.*: //p'
		echo "Error: This computer does not have an AMD, Nvidia or Intel GPU" >&2
		exit 1
	fi
fi
if command -v clinfo >/dev/null; then
	if [[ $(clinfo --raw | sed -n 's/^#PLATFORMS *//p') -eq 0 ]]; then
		clinfo
		echo "Error: This computer does not have an OpenCL platform" >&2
		exit 1
	fi
fi
if ! command -v make >/dev/null || ! command -v g++ >/dev/null; then
	echo -e "Installing Make and the GNU C++ compiler"
	echo -e "Please enter your password if prompted.\n"
	sudo apt-get update -y
	sudo apt-get install -y build-essential
fi
if [[ -n $CXX ]] && ! command -v "$CXX" >/dev/null; then
	echo "Error: $CXX is not installed." >&2
	exit 1
fi
CXX=${CXX:-g++}
VERSION=$("$CXX" -dumpversion)
RE='^g\+\+'
if [[ $CXX =~ $RE && ${VERSION%%.*} -lt 8 ]]; then
	echo "Error: PRPLL requires at least the GNU C++ compiler 8 and you have $VERSION" >&2
	exit 1
fi
if ! command -v python3 >/dev/null; then
	echo "Error: Python 3 is not installed." >&2
	exit 1
fi
if ! ldconfig -p | grep -iq 'libOpenCL\.'; then
	echo -e "Installing the OpenCL library"
	echo -e "Please enter your password if prompted.\n"
	sudo apt-get update -y
	# sudo apt-get install -y ocl-icd-* opencl-headers clinfo
	sudo apt-get install -y ocl-icd-opencl-dev clinfo
fi
TIME=$(echo "$TIME" | awk '{ printf "%g", $1 * 60 }')
if [[ -d $DIR && -x "$DIR/prpll" ]]; then
	echo -e "PRPLL is already downloaded\n"
	cd "$DIR"
else
	if command -v git >/dev/null; then
		echo -e "Downloading PRPLL\n"
		git clone https://github.com/gwoltman/gpuowl.git "$DIR"
		cd "$DIR"
		git remote add upstream https://github.com/preda/gpuowl.git
		git fetch upstream
		sed -i 's/--dirty //' Makefile
		sed -i 's/ --match v\/prpll\/\*//' Makefile
	else
		echo -e "Downloading PRPLL\n"
		wget https://github.com/gwoltman/gpuowl/archive/$BRANCH.tar.gz
		echo -e "\nDecompressing the files\n"
		tar -xzvf $BRANCH.tar.gz
		mv -v gpuowl-$BRANCH/ "$DIR"/
		cd "$DIR"
		if output=$(curl -sf 'https://api.github.com/repos/gwoltman/gpuowl/tags?per_page=1'); then
			if command -v jq >/dev/null; then
				name=$(echo "$output" | jq -r '.[0].name')
			else
				name=$(echo "$output" | python3 -c 'import sys, json; print(json.load(sys.stdin)[0]["name"])')
			fi
			if output=$(curl -sf "https://api.github.com/repos/gwoltman/gpuowl/compare/$BRANCH...$name"); then
				if command -v jq >/dev/null; then
					behind_by=$(echo "$output" | jq '.behind_by')
					sha=$(echo "$output" | jq -r '.base_commit.sha')
				else
					behind_by=$(echo "$output" | python3 -c 'import sys, json; print(json.load(sys.stdin)["behind_by"])')
					sha=$(echo "$output" | python3 -c 'import sys, json; print(json.load(sys.stdin)["base_commit"]["sha"])')
				fi
			fi
			sed -i 's/\\`git describe --tags --long --dirty --always --match v\/prpll\/\*\\`/'"${name}${behind_by:+-${behind_by}${sha:+-g${sha::7}}}"'/' Makefile
		fi
	fi
	echo -e "\nSetting up PRPLL\n"
	sed -i 's/^CXX =/CXX ?=/' Makefile
	sed -i 's/\.\/genbundle\.sh/bash genbundle.sh/' Makefile
	# -funsafe-math-optimizations
	sed -i 's/-O2/-Wall -g -O3 -flto -ffinite-math-only/' Makefile
	make -j "$(nproc)"
	pushd build-release >/dev/null
	rm -- *.o
	mv -v prpll ..
	popd >/dev/null
fi
if [[ -f "autoprimenet.py" ]]; then
	echo -e "AutoPrimeNet is already downloaded\n"
else
	echo -e "\nDownloading AutoPrimeNet\n"
	if [[ -e ../autoprimenet.py ]]; then
		cp -v ../autoprimenet.py .
	else
		wget -nv https://raw.github.com/tdulcet/AutoPrimeNet/main/autoprimenet.py
	fi
	chmod +x autoprimenet.py
	python3 -OO -m py_compile autoprimenet.py
fi
echo -e "\nInstalling the Requests library\n"
# python3 -m ensurepip --default-pip || true
python3 -m pip install --upgrade pip || true
if ! python3 -m pip install requests; then
	if command -v pip3 >/dev/null; then
		pip3 install requests
	else
		echo -e "\nWarning: Python pip3 is not installed and the Requests library may also not be installed\n"
	fi
fi
mkdir "$N"
cd "$N"
DIR=$PWD
echo "-user $USERID -unsafeMath" >config.txt
echo -e "\nRegistering computer with PrimeNet\n"
ARGS=()
if command -v clinfo >/dev/null; then
	clinfo=$(clinfo --raw)
	mapfile -t GPU < <(echo "$clinfo" | sed -n 's/.*CL_DEVICE_NAME *//p')
	ARGS+=(--cpu-model="${GPU[DEVICE]//\[*\]/}")

	mapfile -t GPU_FREQ < <(echo "$clinfo" | sed -n 's/.*CL_DEVICE_MAX_CLOCK_FREQUENCY *//p')
	ARGS+=(--frequency="${GPU_FREQ[DEVICE]}")

	mapfile -t TOTAL_GPU_MEM < <(echo "$clinfo" | sed -n 's/.*CL_DEVICE_GLOBAL_MEM_SIZE *//p')
	maxAlloc=$((TOTAL_GPU_MEM[DEVICE] >> 20))
	ARGS+=(--memory="$maxAlloc" --max-memory="$(echo "$maxAlloc" | awk '{ printf "%d", $1 * 0.9 }')")
elif command -v nvidia-smi >/dev/null && nvidia-smi >/dev/null; then
	mapfile -t GPU < <(nvidia-smi --query-gpu=gpu_name --format=csv,noheader)
	ARGS+=(--cpu-model="${GPU[DEVICE]}")

	mapfile -t GPU_FREQ < <(nvidia-smi --query-gpu=clocks.max.gr --format=csv,noheader,nounits | grep -iv 'not supported')
	if [[ -n $GPU_FREQ ]]; then
		ARGS+=(--frequency="${GPU_FREQ[DEVICE]}")
	fi

	mapfile -t TOTAL_GPU_MEM < <(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | grep -iv 'not supported')
	if [[ -n $TOTAL_GPU_MEM ]]; then
		maxAlloc=${TOTAL_GPU_MEM[DEVICE]}
		ARGS+=(--memory="$maxAlloc" --max-memory="$(echo "$maxAlloc" | awk '{ printf "%d", $1 * 0.9 }')")
	fi
fi
python3 -OO ../autoprimenet.py -t 0 -T "$TYPE" -u "$USERID" --prpll -H "$COMPUTER" "${ARGS[@]}"
echo -e "\nStarting AutoPrimeNet\n"
nohup python3 -OO ../autoprimenet.py >>'autoprimenet.out' &
sleep 1
echo -e "\nTuning PRPLL for your computer and GPU\nThis may take a while…\n"
time ../prpll -device $DEVICE -tune minexp=0
sed -i '/-log/ s/^/# /' config.txt
echo -e "\nStarting PRPLL\n"
nohup ../prpll -device $DEVICE >>"prpll.out" &
sleep 1
#crontab -l | { cat; echo "@reboot cd ${DIR@Q} && nohup ../prpll -device $DEVICE >> 'prpll.out' &"; } | crontab -
#crontab -l | { cat; echo "@reboot cd ${DIR@Q} && nohup python3 -OO ../autoprimenet.py >> 'autoprimenet.out' &"; } | crontab -
cat <<EOF >prpll.sh
#!/bin/bash

# Copyright © 2020 Teal Dulcet
# Start PRPLL and AutoPrimeNet if the computer has not been used in the specified idle time and stop it when someone uses the computer
# ${DIR@Q}/prpll.sh

NOW=\${EPOCHSECONDS:-\$(date +%s)}

if who -s | awk '{ print \$2 }' | (cd /dev && xargs -r stat -c '%U %X') | awk '{if ('"\$NOW"'-\$2<$TIME) { print \$1"\t"'"\$NOW"'-\$2; ++count }} END{if (count>0) { exit 1 }}' >/dev/null; then
	pgrep -x prpll >/dev/null || (cd ${DIR@Q} && exec nohup ../prpll -device $DEVICE >>'prpll.out' &)
	pgrep -f '^python3 -OO \.\./autoprimenet\.py' >/dev/null || (cd ${DIR@Q} && exec nohup python3 -OO ../autoprimenet.py >>'autoprimenet.out' &)
else
	pgrep -x prpll >/dev/null && killall -g -INT prpll
fi
EOF
chmod +x prpll.sh
echo -e "\nRun this command for it to start if the computer has not been used in the specified idle time and stop it when someone uses the computer:\n"
echo "crontab -l | { cat; echo \"* * * * * ${DIR@Q}/prpll.sh\"; } | crontab -"
echo -e "\nTo edit the crontab, run \"crontab -e\""
