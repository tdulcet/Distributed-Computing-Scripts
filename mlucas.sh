#!/bin/bash

# Teal Dulcet
# wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mlucas.sh -qO - | bash -s --
# ./mlucas.sh <PrimeNet Password> [PrimeNet User ID] [Type of work] [Idle time to run]
# ./mlucas.sh <PrimeNet Password> "$USER" 100 10
# ./mlucas.sh <PrimeNet Password> ANONYMOUS

DIR2="mlucas_v19"
FILE2="mlucas_v19.txz"
SUM="7c48048cb6d935638447e45e0528fe9c"
if [[ "$#" -lt 1 || "$#" -gt 4 ]]; then
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
if [[ -d "$DIR2" ]]; then
	echo "Error: Mlucas is already downloaded" >&2
	exit 1
fi
if ! command -v make >/dev/null || ! command -v gcc >/dev/null; then
	echo -e "Installing Make and the GNU C compiler"
	echo -e "Please enter your password when prompted.\n"
	sudo apt-get update -y
	sudo apt-get install build-essential -y
fi
TIME=$(echo "$TIME" | awk '{ printf "%g", $1 * 60 }')

# Adapted from: https://github.com/tdulcet/Linux-System-Information/blob/master/info.sh
. /etc/os-release

echo -e "Linux Distribution:\t\t${PRETTY_NAME:-$ID-$VERSION_ID}"

KERNEL=$(uname -r)
echo -e "Linux Kernel:\t\t\t$KERNEL"

mapfile -t CPU < <(sed -n 's/^model name[[:space:]]*: *//p' /proc/cpuinfo | uniq)
if [[ -n "$CPU" ]]; then
	echo -e "Processor (CPU):\t\t${CPU[0]}$([[ ${#CPU[*]} -gt 1 ]] && echo; printf '\t\t\t\t%s\n' "${CPU[@]:1}")"
fi

CPU_THREADS=$(nproc --all) # $(lscpu | grep -i '^cpu(s)' | sed -n 's/^.\+:[[:blank:]]*//p')
CPU_CORES=$(( CPU_THREADS / $(lscpu | grep -i '^thread(s) per core' | sed -n 's/^.\+:[[:blank:]]*//p') ))
echo -e "CPU Cores/Threads:\t\t$CPU_CORES/$CPU_THREADS"

ARCHITECTURE=$(getconf LONG_BIT)
echo -e "Architecture:\t\t\t$HOSTTYPE (${ARCHITECTURE}-bit)"

TOTAL_PHYSICAL_MEM=$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)
echo -e "Total memory (RAM):\t\t$(printf "%'d" $((TOTAL_PHYSICAL_MEM / 1024))) MiB ($(printf "%'d" $((((TOTAL_PHYSICAL_MEM * 1024) / 1000) / 1000))) MB)"

TOTAL_SWAP=$(awk '/^SwapTotal:/ {print $2}' /proc/meminfo)
echo -e "Total swap space:\t\t$(printf "%'d" $((TOTAL_SWAP / 1024))) MiB ($(printf "%'d" $((((TOTAL_SWAP * 1024) / 1000) / 1000))) MB)"

if command -v lspci >/dev/null; then
	mapfile -t GPU < <(lspci 2>/dev/null | grep -i 'vga\|3d\|2d' | sed -n 's/^.*: //p')
fi
if [[ -n "$GPU" ]]; then
	echo -e "Graphics Processor (GPU):\t${GPU[0]}$([[ ${#GPU[*]} -gt 1 ]] && echo; printf '\t\t\t\t%s\n' "${GPU[@]:1}")"
fi

echo -e "\nDownloading Mlucas\n"
wget https://www.mersenneforum.org/mayer/src/C/$FILE2
if [[ ! "$(md5sum $FILE2 | head -c 32)" = "$SUM" ]]; then
    echo "Error: md5sum does not match" >&2
    echo "Please run \"rm -r $PWD\" and try running this script again" >&2
	exit 1
fi
echo -e "\nDecompressing the files\n"
tar -xvf $FILE2
cd "$DIR2"
mkdir obj
cd obj
DIR=$PWD
ARGS=()
echo -e "\nBuilding Mlucas\n"
# for mode in avx512 avx2 avx sse2; do
	# if grep -iq "$mode" /proc/cpuinfo; then
		# echo -e "The CPU supports the ${mode^^} SIMD build mode.\n"
		# ARGS+=( "-DUSE_${mode^^}" )
		# break
	# fi
# done
if grep -iq 'avx512' /proc/cpuinfo; then
	echo -e "The CPU supports the AVX512 SIMD build mode.\n"
	ARGS+=( "-DUSE_AVX512" )
elif grep -iq 'avx2' /proc/cpuinfo; then
	echo -e "The CPU supports the AVX2 SIMD build mode.\n"
	ARGS+=( "-DUSE_AVX2" -mavx2 )
elif grep -iq 'avx' /proc/cpuinfo; then
	echo -e "The CPU supports the AVX SIMD build mode.\n"
	ARGS+=( "-DUSE_AVX" -mavx )
elif grep -iq 'sse2' /proc/cpuinfo; then
	echo -e "The CPU supports the SSE2 SIMD build mode.\n"
	ARGS+=( "-DUSE_SSE2" )
fi
if grep -iq 'asimd' /proc/cpuinfo; then
	echo -e "The CPU supports the ASIMD build mode.\n"
	ARGS+=( "-DUSE_ARM_V8_SIMD" )
fi
cat << EOF > Makefile
OBJS=\$(patsubst ../src/%.c, %.o, \$(wildcard ../src/*.c))

Mlucas: \$(OBJS)
	gcc -Wall -g -o \$@ \$(OBJS) -lm -lpthread -lrt
%.o: ../src/%.c
	gcc -Wall -g -c -O3 -march=native ${ARGS[@]} -DUSE_THREADS \$<
clean:
	rm -f *.o
EOF
make -j "$CPU_THREADS"
make clean
echo -e "\nTesting Mlucas\n"
./Mlucas -fftlen 192 -iters 100 -radset 0
ARGS=()
echo -e "\nOptimizing Mlucas for your computer\nThis may take awhile…\n"
if echo "${CPU[0]}" | grep -iq 'intel'; then
	echo -e "The CPU is Intel.\n"
	if [[ $CPU_CORES -ne $CPU_THREADS && $CPU_CORES -gt 1 ]]; then
		ARGS+=( -cpu "0$(for ((j=CPU_CORES; j<CPU_THREADS; j+=CPU_CORES)); do echo -n ",$j"; done)" )
	fi
elif echo "${CPU[0]}" | grep -iq 'amd'; then
	echo -e "The CPU is AMD.\n"
	if [[ $CPU_CORES -ne $CPU_THREADS && $CPU_THREADS -gt 1 ]]; then
		# ARGS+=( -cpu "0:$(( CPU_THREADS - 1 )):$(( CPU_THREADS / CPU_CORES ))" )
		ARGS+=( -cpu "0:$(( (CPU_THREADS / CPU_CORES) - 1 ))" )
	fi
else
	ARGS+=( -cpu "0:$(( CPU_CORES - 1 ))" )
fi
./Mlucas -s m "${ARGS[@]}"
RUNS=()
if echo "${CPU[0]}" | grep -iq 'intel'; then
	echo -e "The CPU is Intel."
	for ((i=0; i<CPU_CORES; ++i)); do
		if [[ $CPU_CORES -ne $CPU_THREADS ]]; then
			arg="$i$(for ((j=i+CPU_CORES; j<CPU_THREADS; j+=CPU_CORES)); do echo -n ",$j"; done)"
		else
			arg=$i
		fi
		RUNS+=( "$arg" )
	done
elif echo "${CPU[0]}" | grep -iq 'amd'; then
	echo -e "The CPU is AMD."
	for ((i=0; i<CPU_CORES; ++i)); do
		if [[ $CPU_CORES -ne $CPU_THREADS ]]; then
			temp=$(( CPU_THREADS / CPU_CORES ))
			# arg=$(( i * (CPU_THREADS / CPU_CORES) ))
			arg="$(( i * temp )):$(( (i * temp) + temp - 1 ))"
		else
			arg=$i
		fi
		RUNS+=( "$arg" )
	done
else
	for ((i=0; i<CPU_CORES; i+=4)); do
		arg="$i:$(if [[ $(( i + 3 )) -lt $CPU_CORES ]]; then echo "$(( i + 3 ))"; else echo "$(( CPU_CORES - 1 ))"; fi)"
		RUNS+=( "$arg" )
	done
fi
for i in "${!RUNS[@]}"; do
	echo -e "\nCPU Core $i:"
	mkdir "run$i"
	pushd "run$i" > /dev/null
	ln -s ../mlucas.cfg .
	echo -e "\tStarting PrimeNet\n"
	nohup python ../../src/primenet.py -d -T "$TYPE" -u "$USERID" -p "$PASSWORD" &
	sleep 1
	echo -e "\n\tStarting Mlucas\n"
	nohup nice ../Mlucas -cpu "${RUNS[i]}" &
	sleep 1
	popd > /dev/null
done
echo -e "\nSetting it to start if the computer has not been used in the specified idle time and stop it when someone uses the computer\n"
#crontab -l | { cat; echo "$(for i in "${!RUNS[@]}"; do echo -n "(cd $DIR/run$i && nohup nice ../Mlucas -cpu \"${RUNS[i]}\" &); "; done)"; } | crontab -
#crontab -l | { cat; echo "$(for i in "${!RUNS[@]}"; do echo -n "(cd $DIR/run$i && nohup python ../../src/primenet.py -d -T \"$TYPE\" -u \"$USERID\" -p \"$PASSWORD\" &); "; done)"; } | crontab -
crontab -l | { cat; echo "* * * * * if who -s | awk '{ print \$2 }' | (cd /dev && xargs -r stat -c '\%U \%X') | awk '{if ('\"\$(date +\%s)\"'-\$2<$TIME) { print \$1\"\t\"'\"\$(date +\%s)\"'-\$2; ++count }} END{if (count>0) { exit 1 }}' > /dev/null; then pgrep Mlucas > /dev/null || $(for i in "${!RUNS[@]}"; do echo -n "(cd $DIR/run$i && nohup nice ../Mlucas -cpu \"${RUNS[i]}\" &); "; done) pgrep -f '^python \.\./\.\./src/primenet\.py' > /dev/null || $(for i in "${!RUNS[@]}"; do echo -n "(cd $DIR/run$i && nohup python ../../src/primenet.py -d -T \"$TYPE\" -u \"$USERID\" -p \"$PASSWORD\" &); "; done) else pgrep Mlucas > /dev/null && killall Mlucas; fi"; } | crontab -
