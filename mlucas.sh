#!/bin/bash

# Teal Dulcet
# wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mlucas.sh -qO - | bash -s --
# ./mlucas.sh [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
# ./mlucas.sh "$USER" "$HOSTNAME" 100 10
# ./mlucas.sh ANONYMOUS

DIR2="mlucas_v19"
FILE2="mlucas_v19.txz"
SUM="10906d3f1f4206ae93ebdb045f36535c"
if [[ $# -gt 4 ]]; then
	echo "Usage: $0 [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]" >&2
	exit 1
fi
USERID=${1:-$USER}
COMPUTER=${2:-$HOSTNAME}
TYPE=${3:-150}
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
echo -e "Computer name:\t\t$COMPUTER"
echo -e "Type of work:\t\t$TYPE"
echo -e "Idle time to run:\t$TIME minutes\n"
if [[ -e idletime.sh ]]; then
	bash -- idletime.sh
else
	wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/idletime.sh -qO - | bash -s
fi
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

echo -e "\nLinux Distribution:\t\t${PRETTY_NAME:-$ID-$VERSION_ID}"

KERNEL=$(</proc/sys/kernel/osrelease) # uname -r
echo -e "Linux Kernel:\t\t\t$KERNEL"

mapfile -t CPU < <(sed -n 's/^model name[[:space:]]*: *//p' /proc/cpuinfo | uniq)
if [[ -n "$CPU" ]]; then
	echo -e "Processor (CPU):\t\t${CPU[0]}$([[ ${#CPU[*]} -gt 1 ]] && printf '\n\t\t\t\t%s' "${CPU[@]:1}")"
fi

CPU_THREADS=$(nproc --all) # $(lscpu | grep -i '^cpu(s)' | sed -n 's/^.\+:[[:blank:]]*//p')
if [[ $CPU_THREADS -gt 1 ]]; then
	for (( i = 0; i < CPU_THREADS - 1; ++i )); do
		seq 0 $(( 2 ** 22 )) | factor >/dev/null &
	done
fi

sleep 1

CPU_FREQS=( $(sed -n 's/^cpu MHz[[:space:]]*: *//p' /proc/cpuinfo) )
if [[ -z "$CPU_FREQS" ]]; then
	for file in /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq; do
		if [[ -r "$file" ]]; then
			CPU_FREQS=( $(awk '{ printf "%g\n", $1 / 1000 }' /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq) )
		fi
		break
	done
fi
CPU_FREQ=$(printf '%s\n' "${CPU_FREQS[@]}" | sort -nr | head -n 1)
echo -e "CPU frequency:\t\t\t$(printf "%'.0f" "$CPU_FREQ") MHz"

wait

HP=$(lscpu | grep -i '^thread(s) per core' | sed -n 's/^.\+:[[:blank:]]*//p')
CPU_CORES=$(( CPU_THREADS / HP ))
echo -e "CPU Cores/Threads:\t\t$CPU_CORES/$CPU_THREADS"

ARCHITECTURE=$(getconf LONG_BIT)
echo -e "Architecture:\t\t\t$HOSTTYPE (${ARCHITECTURE}-bit)"

MEMINFO=$(</proc/meminfo)
TOTAL_PHYSICAL_MEM=$(echo "$MEMINFO" | awk '/^MemTotal:/ {print $2}')
echo -e "Total memory (RAM):\t\t$(printf "%'d" $((TOTAL_PHYSICAL_MEM / 1024))) MiB ($(printf "%'d" $((((TOTAL_PHYSICAL_MEM * 1024) / 1000) / 1000))) MB)"

TOTAL_SWAP=$(echo "$MEMINFO" | awk '/^SwapTotal:/ {print $2}')
echo -e "Total swap space:\t\t$(printf "%'d" $((TOTAL_SWAP / 1024))) MiB ($(printf "%'d" $((((TOTAL_SWAP * 1024) / 1000) / 1000))) MB)"

if command -v lspci >/dev/null; then
	mapfile -t GPU < <(lspci 2>/dev/null | grep -i 'vga\|3d\|2d' | sed -n 's/^.*: //p')
fi
if [[ -n "$GPU" ]]; then
	echo -e "Graphics Processor (GPU):\t${GPU[0]}$([[ ${#GPU[*]} -gt 1 ]] && printf '\n\t\t\t\t%s' "${GPU[@]:1}")"
fi

echo -e "\nDownloading Mlucas\n"
wget https://www.mersenneforum.org/mayer/src/$FILE2
if [[ ! "$(md5sum $FILE2 | head -c 32)" == "$SUM" ]]; then
	echo "Error: md5sum does not match" >&2
	echo "Please run \"rm -r '$PWD'\" and try running this script again" >&2
	exit 1
fi
echo -e "\nDecompressing the files\n"
tar -xvf $FILE2
cd "$DIR2"
echo -e "\nDownloading the PrimeNet script\n"
if [[ -e ../primenet.py ]]; then
	cp ../primenet.py .
else
	wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/primenet.py -nv
fi
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
	ARGS+=( "-DUSE_AVX512" -march=native )
elif grep -iq 'avx2' /proc/cpuinfo; then
	echo -e "The CPU supports the AVX2 SIMD build mode.\n"
	ARGS+=( "-DUSE_AVX2" -march=native -mavx2 )
elif grep -iq 'avx' /proc/cpuinfo; then
	echo -e "The CPU supports the AVX SIMD build mode.\n"
	ARGS+=( "-DUSE_AVX" -march=native -mavx )
elif grep -iq 'sse2' /proc/cpuinfo; then
	echo -e "The CPU supports the SSE2 SIMD build mode.\n"
	ARGS+=( "-DUSE_SSE2" -march=native )
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
	gcc -Wall -g -c -O3 ${ARGS[@]} -DUSE_THREADS \$<
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
		arg="$i:$(if [[ i + 3 -lt $CPU_CORES ]]; then echo "$(( i + 3 ))"; else echo "$(( CPU_CORES - 1 ))"; fi)"
		RUNS+=( "$arg" )
	done
fi
echo -e "Registering computer with PrimeNet\n"
python3 ../primenet.py -d -t 0 -T "$TYPE" -u "$USERID" -H "$COMPUTER" --cpu_model="${CPU[0]}" --frequency="$(printf "%.0f" "$CPU_FREQ")" -m "$((TOTAL_PHYSICAL_MEM / 1024))" --np="$CPU_CORES" --hp="$HP"
for i in "${!RUNS[@]}"; do
	echo -e "\nCPU Core $i:"
	mkdir "run$i"
	pushd "run$i" >/dev/null
	ln -s ../mlucas.cfg .
	echo -e "\tStarting PrimeNet\n"
	ln -s ../local.ini .
	nohup python3 ../../primenet.py -d -c "$i" &
	sleep 1
	echo -e "\n\tStarting Mlucas\n"
	nohup nice ../Mlucas -cpu "${RUNS[i]}" &
	sleep 1
	popd >/dev/null
done
echo -e "\nSetting it to start if the computer has not been used in the specified idle time and stop it when someone uses the computer\n"
#crontab -l | { cat; echo "$(for i in "${!RUNS[@]}"; do echo -n "(cd \"$DIR/run$i\" && nohup nice ../Mlucas -cpu \"${RUNS[i]}\" &); "; done)"; } | crontab -
#crontab -l | { cat; echo "$(for i in "${!RUNS[@]}"; do echo -n "(cd \"$DIR/run$i\" && nohup python3 ../../primenet.py -d -c $i &); "; done)"; } | crontab -
cat << EOF > Mlucas.sh
#!/bin/bash

# Start Mlucas
# Run: $DIR/Mlucas.sh

if who -s | awk '{ print \$2 }' | (cd /dev && xargs -r stat -c '%U %X') | awk '{if ('"\${EPOCHSECONDS:-\$(date +%s)}"'-\$2<$TIME) { print \$1"\t"'"\${EPOCHSECONDS:-\$(date +%s)}"'-\$2; ++count }} END{if (count>0) { exit 1 }}' >/dev/null; then pgrep Mlucas >/dev/null || { $(for i in "${!RUNS[@]}"; do echo -n "(cd \"$DIR/run$i\" && nohup nice ../Mlucas -cpu \"${RUNS[i]}\" &); "; done) }; pgrep -f '^python3 \.\./\.\./primenet\.py' >/dev/null || { $(for i in "${!RUNS[@]}"; do echo -n "(cd \"$DIR/run$i\" && nohup python3 ../../primenet.py -d -c $i &); "; done) }; else pgrep Mlucas >/dev/null && killall Mlucas; fi
EOF
chmod +x Mlucas.sh
crontab -l | { cat; echo "* * * * * \"$DIR\"/Mlucas.sh"; } | crontab -
