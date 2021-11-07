#!/bin/bash

# Teal Dulcet
# wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mlucas.sh -qO - | bash -s --
# ./mlucas.sh [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
# ./mlucas.sh "$USER" "$HOSTNAME" 150 10
# ./mlucas.sh ANONYMOUS

DIR="mlucas_v20.1.1"
FILE="mlucas_v20.1.1.txz"
SUM="c917eb8faa6ff643d359b335cdacbfda"
if [[ $# -gt 4 ]]; then
	echo "Usage: $0 [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]" >&2
	exit 1
fi
USERID=${1:-$USER}
COMPUTER=${2:-$HOSTNAME}
TYPE=${3:-150}
TIME=${4:-10}
decimal_point=$(locale decimal_point)
RE='^(4|1(0[0124]|5[0123]))$'
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
if ! command -v make >/dev/null || ! command -v gcc >/dev/null; then
	echo -e "Installing Make and the GNU C compiler"
	echo -e "Please enter your password if prompted.\n"
	sudo apt-get update -y
	sudo apt-get install build-essential -y
fi
if [[ -n "$CC" ]] && ! command -v "$CC" >/dev/null; then
	echo "Error: $CC is not installed." >&2
	exit 1
fi
if ! command -v python3 >/dev/null; then
	echo "Error: Python 3 is not installed." >&2
	exit 1
fi
files=( /usr/include/gmp*.h )
if ! ldconfig -p | grep -iq 'libgmp\.' || ! [[ -f "${files[0]}" ]]; then
	echo -e "Installing the GNU Multiple Precision (GMP) library"
	echo -e "Please enter your password if prompted.\n"
	sudo apt-get update -y
	sudo apt-get install libgmp3-dev -y
fi
TIME=$(echo "$TIME" | awk '{ printf "%g", $1 * 60 }')

# Adapted from: https://github.com/tdulcet/Linux-System-Information/blob/master/info.sh
. /etc/os-release

echo -e "\nLinux Distribution:\t\t${PRETTY_NAME:-$ID-$VERSION_ID}"

KERNEL=$(</proc/sys/kernel/osrelease) # uname -r
echo -e "Linux Kernel:\t\t\t$KERNEL"

mapfile -t CPU < <(sed -n 's/^model name[[:blank:]]*: *//p' /proc/cpuinfo | uniq)
if [[ -z "$CPU" ]]; then
	mapfile -t CPU < <(lscpu | grep -i '^model name' | sed -n 's/^.\+:[[:blank:]]*//p' | uniq)
fi
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

CPU_FREQS=( $(sed -n 's/^cpu MHz[[:blank:]]*: *//p' /proc/cpuinfo) )
if [[ -z "$CPU_FREQS" ]]; then
	for file in /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq; do
		if [[ -r "$file" ]]; then
			CPU_FREQS=( $(awk '{ printf "%g\n", $1 / 1000 }' /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq) )
		fi
		break
	done
fi
CPU_FREQ=${CPU_FREQ:+$(printf '%s\n' "${CPU_FREQS[@]}" | sort -nr | head -n 1)}
echo -e "CPU frequency/speed:\t\t$(printf "%'.0f" "${CPU_FREQ/./$decimal_point}") MHz"

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

if [[ -d "$DIR" ]]; then
	if [[ -e "$FILE" ]] && [[ "$(md5sum $FILE | head -c 32)" != "$SUM" ]]; then
		echo "Error: Mlucas is already downloaded, but md5sum does not match" >&2
		echo "Please run \"rm -r $FILE $DIR\" and run this script again" >&2
		exit 1
	elif [[ -d "$DIR/obj" && -x "$DIR/obj/Mlucas" && ! -L "$DIR/obj/mlucas.0.cfg" ]]; then
		echo -e "\nMlucas is already downloaded\n"
		cd "$DIR"
	else
		echo "Error: Mlucas is already downloaded" >&2
		exit 1
	fi
else
	echo -e "\nDownloading Mlucas\n"
	wget https://www.mersenneforum.org/mayer/src/C/$FILE
	if [[ "$(md5sum $FILE | head -c 32)" != "$SUM" ]]; then
		echo "Error: md5sum does not match" >&2
		echo "Please run \"rm $FILE\" make sure you are using the latest version of this script and try running it again" >&2
		echo "If you still get this error, please create an issue: https://github.com/tdulcet/Distributed-Computing-Scripts/issues" >&2
		exit 1
	fi
	echo -e "\nDecompressing the files\n"
	tar -xvf $FILE
	cd "$DIR"
	mkdir obj
	cd obj
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
		ARGS+=( "-DUSE_ARM_V8_SIMD" -march=native )
	fi
	cat << EOF > Makefile
CC?=gcc
OBJS=\$(patsubst ../src/%.c, %.o, \$(wildcard ../src/*.c))

Mlucas: \$(OBJS)
	\$(CC) -Wall -g -o \$@ \$(OBJS) -lm -lpthread -lrt -lgmp
%.o: ../src/%.c
	\$(CC) -Wall -g -c -O3 ${ARGS[@]} -DUSE_THREADS \$<
clean:
	rm -f *.o
EOF
	if ! make -j "$CPU_THREADS" >& build.log; then
		cat build.log
		exit 1
	fi
	if [[ -n "$CI" ]]; then
		cat build.log
	fi
	make clean
	cd ..
fi
if [[ ! -f "primenet.py.bak" ]]; then
	mv -v primenet.py{,.bak}
fi
if [[ -f "primenet.py" ]]; then
	echo -e "\nThe PrimeNet script is already downloaded\n"
else
	echo -e "\nDownloading the PrimeNet script\n"
	if [[ -e ../primenet.py ]]; then
		cp -v ../primenet.py .
	else
		wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/primenet.py -nv
	fi
fi
if command -v pip3 >/dev/null; then
	echo -e "\nInstalling the Requests library\n"
	pip3 install requests
else
	echo -e "\nWarning: pip3 is not installed and the Requests library may also not be installed\n"
fi
cd obj
DIR=$PWD
echo -e "\nTesting Mlucas\n"
./Mlucas -fft 192 -iters 100 -radset 0
CORES=()
THREADS=()
ARGS=()
echo -e "\nOptimizing Mlucas for your computer\nThis may take a while…\n"
if echo "${CPU[0]}" | grep -iq 'intel'; then
	echo -e "The CPU is Intel."
	for ((k=1; k<=HP; k*=2)); do
		for ((l=1; l<=CPU_CORES; l*=2)); do
			rem=$(( CPU_CORES % l ))
			if (( rem )); then
				args=()
				for ((i=0; i<CPU_CORES; i+=i==0?rem:l)); do
					arg=$i
					if [[ $l -gt 1 ]]; then
						arg+=":$(( i + (i==0 ? rem : l) - 1 ))"
					fi
					for ((j=i+CPU_CORES; j<k*CPU_CORES; j+=CPU_CORES)); do
						arg+=",$j"
						if [[ $l -gt 1 ]]; then
							arg+=":$(( j + (i==0 ? rem : l) - 1 ))"
						fi
					done
					args+=( "$arg" )
				done
				CORES+=( "$k" )
				THREADS+=( "$((rem*k)) $((l*k))" )
				ARGS+=( "${args[*]}" )
			fi
			args=()
			for ((i=0; i<CPU_CORES; i+=l)); do
				arg=$i
				if [[ $l -gt 1 ]]; then
					temp=$(( i + l - 1 ))
					arg+=":$(( temp < CPU_CORES ? temp : CPU_CORES - 1 ))"
				fi
				for ((j=i+CPU_CORES; j<k*CPU_CORES; j+=CPU_CORES)); do
					arg+=",$j"
					if [[ $l -gt 1 ]]; then
						temp=$(( j + l - 1 ))
						arg+=":$(( temp < k*CPU_CORES ? temp : k*CPU_CORES - 1 ))"
					fi
				done
				args+=( "$arg" )
			done
			CORES+=( "$k" )
			if (( rem )); then
				THREADS+=( "$((l*k)) $((rem*k))" )
			else
				THREADS+=( "$((l*k))" )
			fi
			ARGS+=( "${args[*]}" )
		done
	done
elif echo "${CPU[0]}" | grep -iq 'amd'; then
	echo -e "The CPU is AMD."
	for ((k=1; k<=HP; k*=2)); do
		for ((l=1; l<=CPU_CORES; l*=2)); do
			rem=$(( CPU_CORES % l ))
			if (( rem )); then
				args=()
				for ((i=0; i<CPU_THREADS; i+=(i==0?rem:l)*HP)); do
					arg=$i
					if [[ $k -gt 1 || $l -gt 1 ]]; then
						arg+=":$(( i + ((i==0 ? rem : l)*HP) - 1 ))"
						if [[ $k -ne $HP ]]; then
							arg+=":$(( HP / k ))"
						fi
					fi
					args+=( "$arg" )
				done
				CORES+=( "$k" )
				THREADS+=( "$((rem*k)) $((l*k))" )
				ARGS+=( "${args[*]}" )
			fi
			args=()
			for ((i=0; i<CPU_THREADS; i+=l*HP)); do
				arg=$i
				if [[ $k -gt 1 || $l -gt 1 ]]; then
					temp=$(( i + (l * HP) - 1 ))
					arg+=":$(( temp < CPU_THREADS ? temp : CPU_THREADS - 1 ))"
					if [[ $k -ne $HP ]]; then
						arg+=":$(( HP / k ))"
					fi
				fi
				args+=( "$arg" )
			done
			CORES+=( "$k" )
			if (( rem )); then
				THREADS+=( "$((l*k)) $((rem*k))" )
			else
				THREADS+=( "$((l*k))" )
			fi
			ARGS+=( "${args[*]}" )
		done
	done
else
	for ((l=1; l<=CPU_CORES; l*=2)); do
		rem=$(( CPU_CORES % l ))
		if (( rem )); then
			args=()
			for ((i=0; i<CPU_CORES; i+=i==0?rem:l)); do
				arg=$i
				if [[ $l -gt 1 ]]; then
					arg+=":$(( i + (i==0 ? rem : l) - 1 ))"
				fi
				args+=( "$arg" )
			done
			THREADS+=( "$rem $l" )
			ARGS+=( "${args[*]}" )
		fi
		args=()
		for ((i=0; i<CPU_CORES; i+=l)); do
			arg=$i
			if [[ $l -gt 1 ]]; then
				temp=$(( i + l - 1 ))
				arg+=":$(( temp < CPU_CORES ? temp : CPU_CORES - 1 ))"
			fi
			args+=( "$arg" )
		done
		if (( rem )); then
			THREADS+=( "$l $rem" )
		else
			THREADS+=( "$l" )
		fi
		ARGS+=( "${args[*]}" )
	done
fi
echo "Combinations of CPU cores/threads"
{
	echo -e "#\tWorkers/Runs\tThreads\t-cpu arguments"
	for i in "${!ARGS[@]}"; do
		args=( ${ARGS[i]} )
		printf "%'d\t%'d\t%s\t%s\n" $((i+1)) ${#args[*]} "${THREADS[i]// /, }" "${args[*]}"
	done
} | column -t -s $'\t'
echo
# https://www.mersenneforum.org/showpost.php?p=569485&postcount=71
TIMES=()
FFTS=()
RADICES=()
if [[ -e mlucas.cfg ]]; then
	rm -v mlucas.cfg
fi
for i in "${!ARGS[@]}"; do
	args=( ${ARGS[i]} )
	threads=( ${THREADS[i]} )
	times=()
	ffts=()
	radices=()
	for j in "${!threads[@]}"; do
		index=$(( j==0 ? 0 : -1 ))
		printf "\n#%'d\tThreads: %s\t(-cpu argument: %s)\n\n" $((i+1)) "${threads[j]}" "${args[index]}"
		file="mlucas.${CORES:+${CORES[i]}c.}${threads[j]}t.$j.cfg"
		if [[ ! -e "$file" ]]; then
			# for ((k=7; k<12; ++k)); do
				# m=$((2 ** k))
				# for l in {8..15}; do
					# fft=$((l * m))
					# printf '\n\tFFT length: %sK\n\n' $fft
					# time ./Mlucas -s $fft -cpu "${args[index]}"
				# done
			# done
			time ./Mlucas -s m -cpu "${args[index]}" |& tee -a "test.${CORES:+${CORES[i]}c.}${threads[j]}t.$j.log" | grep -i 'error\|warn\|info'
			mv mlucas.cfg "$file"
		fi
		times+=( "$(awk 'BEGIN { fact='$(( (${#CORES[*]} == 0 ? threads[j] : threads[j] / CORES[i]) * (${#threads[*]}==1 ? ${#args[*]} : ((threads[0]<threads[1] && j==0) || (threads[0]>threads[1] && j==1) ? 1 : ${#args[*]}-1)) ))'/'${#args[*]}' } /^[[:space:]]*#/ || NF<4 { next } { printf "%.15g\n", $4*fact }' "$file")" )
		ffts+=( "$(awk '/^[[:space:]]*#/ || NF<4 { next } { print $1 }' "$file")" )
		radices+=( "$(awk '/^[[:space:]]*#/ || NF<4 { next } { for(i=11;i<=NF && $i!=0;++i) printf "%s%s", $i, i==NF || $(i+1)==0 ? RS : OFS }' "$file")" )
	done
	if [[ ${#threads[*]} -eq 1 ]]; then
		TIMES+=( "${times[0]}" )
		FFTS+=( "${ffts[0]}" )
		RADICES+=( "${radices[0]// /,}" )
	else
		mapfile -t atimes <<< "${times[0]}"
		mapfile -t times <<< "${times[1]}"
		mapfile -t affts <<< "${ffts[0]}"
		mapfile -t ffts <<< "${ffts[1]}"
		mapfile -t aradices <<< "${radices[0]}"
		mapfile -t radices <<< "${radices[1]}"
		TIMES+=( "$(for k in "${!affts[@]}"; do for j in "${!ffts[@]}"; do if [[ ${affts[k]} -eq ${ffts[j]} ]]; then echo "${atimes[k]} ${times[j]}"; break; fi; done; done | awk '{ printf "%.15g\n", $1 + $2 }')" )
		FFTS+=( "$(for k in "${!affts[@]}"; do for j in "${!ffts[@]}"; do if [[ ${affts[k]} -eq ${ffts[j]} ]]; then echo "${affts[k]}"; break; fi; done; done)" )
		RADICES+=( "$(for k in "${!affts[@]}"; do for j in "${!ffts[@]}"; do if [[ ${affts[k]} -eq ${ffts[j]} ]]; then printf '%s\t%s\n' "${aradices[k]// /,}" "${radices[j]// /,}"; break; fi; done; done)" )
	fi
done
# MIN=0
# mapfile -t affts <<< "${FFTS[MIN]}"
# atimes=( ${TIMES[MIN]} )
# for i in "${!TIMES[@]}"; do
	# if [[ $i -gt 0 ]]; then
		# mapfile -t ffts <<< "${FFTS[i]}"
		# times=( ${TIMES[i]} )
		# mean=$(for k in "${!affts[@]}"; do for j in "${!ffts[@]}"; do if [[ ${affts[k]} -eq ${ffts[j]} ]]; then printf '%s\t%s\n' "${atimes[k]}" "${times[j]}"; break; fi; done; done | awk '{ sum+=$1/$2 } END { printf "%.15g\n", sum / NR }')
		# if (( $(echo "$mean" | awk '{ print ($1>1) }') )); then
			# MIN=$i
			# affts=( "${ffts[@]}" )
			# atimes=( "${times[@]}" )
		# fi
	# fi
# done
files=()
for ((i=0; i<CPU_CORES; ++i)); do
	if [[ -d /dev/shm ]]; then
		file=$(mktemp -p /dev/shm)
	else
		file=$(mktemp)
	fi
	files+=( "$file" )
done
trap 'rm "${files[@]}"' EXIT
ITERS=()
for i in "${!ARGS[@]}"; do
	args=( ${ARGS[i]} )
	threads=( ${THREADS[i]} )
	mapfile -t ffts <<< "${FFTS[i]}"
	mapfile -t aradices <<< "${RADICES[i]}"
	iters=()
	printf "\n#%'d\tThreads: %s\n" $((i+1)) "${THREADS[i]// /, }"
	for j in "${!ffts[@]}"; do
		printf '\n\tFFT length: %sK\n\n' "${ffts[j]}"
		radices=( ${aradices[j]} )
		for k in "${!args[@]}"; do
			./Mlucas -fft "${ffts[j]}" -iters 1000 -radset "${radices[${#threads[*]}==1 || (threads[0]<threads[1] && k==0) || (threads[0]>threads[1] && k<${#args[*]}-1) ? 0 : 1]}" -cpu "${args[k]}" >& "${files[k]}" &
		done
		wait
		grep -ih 'error\|warn\||assert\|clocks' "${files[@]::${#args[*]}}"
		if grep -iq 'fatal' "${files[@]::${#args[*]}}"; then
			for k in "${!args[@]}"; do
				./Mlucas -fft "${ffts[j]}" -iters 1000 -radset "${radices[${#threads[*]}==1 || (threads[0]<threads[1] && k==0) || (threads[0]>threads[1] && k<${#args[*]}-1) ? 0 : 1]}" -cpu "${args[k]}" -shift $RANDOM >& "${files[k]}" &
			done
			wait
			grep -ih 'error\|warn\||assert\|clocks' "${files[@]::${#args[*]}}"
		fi
		iters+=( "$(sed -n 's/^Clocks = //p' "${files[@]::${#args[*]}}" | awk -F'[:.]' '{ sum+=1/((($1*60*60*1000)+($2*60*1000)+($3*1000)+$4)/1000) } END { printf "%.15g\n", 1000 * sum }')" )
	done
	ITERS+=( "$(printf '%s\n' "${iters[@]}")" )
done
MAX=0
mapfile -t affts <<< "${FFTS[MAX]}"
aiters=( ${ITERS[MAX]} )
for i in "${!ITERS[@]}"; do
	if [[ $i -gt 0 ]]; then
		mapfile -t ffts <<< "${FFTS[i]}"
		iters=( ${ITERS[i]} )
		mean=$(for k in "${!affts[@]}"; do for j in "${!ffts[@]}"; do if [[ ${affts[k]} -eq ${ffts[j]} ]]; then printf '%s\t%s\n' "${aiters[k]}" "${iters[j]}"; break; fi; done; done | awk '{ sum+=$1/$2 } END { printf "%.15g\n", sum / NR }')
		if (( $(echo "$mean" | awk '{ print $1<1 }') )); then
			MAX=$i
			affts=( "${ffts[@]}" )
			aiters=( "${iters[@]}" )
		fi
	fi
done
RUNS=( ${ARGS[MAX]} )
threads=( ${THREADS[MAX]} )
for j in "${!threads[@]}"; do
	ln -s "mlucas.${CORES:+${CORES[MAX]}c.}${threads[j]}t.$j.cfg" "mlucas.$j.cfg"
done
echo -e "\nSummary\n"
echo -e "\tAdjusted msec/iter times (ms/iter) vs Actual iters/sec total throughput (iters/s) for each combination\n"
{
	printf 'FFT\t'
	for i in "${!ARGS[@]}"; do
		if [[ $i -gt 0 ]]; then
			printf '\t \t'
		fi
		printf "#%'d" $((i+1))
	done
	echo
	printf 'length\t'
	for i in "${!ARGS[@]}"; do
		printf 'ms/iter\titers/s\t'
	done
	echo
	mapfile -t affts < <(printf '%s\n' "${FFTS[@]}" | sort -nu)
	for k in "${!affts[@]}"; do
		printf '%sK\t' "${affts[k]}"
		for i in "${!ITERS[@]}"; do
			mapfile -t ffts <<< "${FFTS[i]}"
			iters=( ${ITERS[i]} )
			times=( ${TIMES[i]} )
			for ((j=k>=${#ffts[*]}?${#ffts[*]}-1:k; j>=0; --j)); do
				if [[ ${affts[k]} -eq ${ffts[j]} ]]; then
					break
				fi
			done
			if [[ $j -ge 0 ]]; then
				printf "%'g\t%'.3f\t" "${times[j]/./$decimal_point}" "${iters[j]/./$decimal_point}"
			else
				printf -- '-\t-\t'
			fi
		done
		echo
	done
} | column -t -s $'\t'
echo
echo "Fastest combination"
{
	echo -e "#\tWorkers/Runs\tThreads\tFirst -cpu argument"
	printf "%'d\t%'d\t%s\t%s\n" $((MAX+1)) ${#RUNS[*]} "${THREADS[MAX]// /, }" "${RUNS[0]}$(if [[ ${#threads[*]} -gt 1 ]]; then echo "  ${RUNS[-1]}"; fi)"
} | column -t -s $'\t'
echo
if [[ ${#ARGS[*]} -gt 1 ]]; then
	{
		echo -e "Mean ± σ std dev faster\t#\tWorkers/Runs\tThreads\tFirst -cpu argument"
		for i in "${!ARGS[@]}"; do
			if [[ $i -ne $MAX ]]; then
				args=( ${ARGS[i]} )
				threads=( ${THREADS[i]} )
				mapfile -t ffts <<< "${FFTS[i]}"
				iters=( ${ITERS[i]} )
				# join -o 1.2,2.2 <(paste <(echo "${FFTS[MAX]}") <(echo "${ITERS[MAX]}")) <(paste <(echo "${FFTS[i]}") <(echo "${ITERS[i]}"))
				array=( $(for k in "${!affts[@]}"; do for j in "${!ffts[@]}"; do if [[ ${affts[k]} -eq ${ffts[j]} ]]; then printf '%s\t%s\n' "${aiters[k]}" "${iters[j]}"; break; fi; done; done | awk '{ sum+=$1/$2; sumsq+=($1/$2)^2 } END { mean=sum/NR; variance=sumsq/NR-mean^2; printf "%.15g\t%.15g\t%.15g\n", mean, sqrt(variance<0 ? 0 : variance), (mean * 100) - 100 }') )
				printf "%'.3f ± %'.3f (%'.1f%%)\t%'d\t%'d\t%s\t%s\n" "${array[0]/./$decimal_point}" "${array[1]/./$decimal_point}" "${array[2]/./$decimal_point}" $((i+1)) ${#args[*]} "${THREADS[i]// /, }" "${args[0]}$(if [[ ${#threads[*]} -gt 1 ]]; then echo "  ${args[-1]}"; fi)"
			fi
		done
	} | column -t -s $'\t'
fi
echo -e "\nRegistering computer with PrimeNet\n"
python3 ../primenet.py -d -t 0 -T "$TYPE" -u "$USERID" --num_workers ${#RUNS[*]} -H "$COMPUTER" --frequency="$(if [[ -n "$CPU_FREQ" ]]; then printf "%.0f" "${CPU_FREQ/./$decimal_point}"; else echo "1000"; fi)" -m "$((TOTAL_PHYSICAL_MEM / 1024))" --np="$CPU_CORES" --hp="$HP"
maxalloc=$(echo ${#RUNS[*]} | awk '{ printf "%g", 90 / $1 }')
for i in "${!RUNS[@]}"; do
	printf "\nWorker/CPU Core %'d: (-cpu argument: %s)\n" $((i+1)) "${RUNS[i]}"
	mkdir "run$i"
	pushd "run$i" >/dev/null
	ln -s ../mlucas.$((${#threads[*]}==1 || (threads[0]<threads[1] && i==0) || (threads[0]>threads[1] && i<${#RUNS[*]}-1) ? 0 : 1)).cfg mlucas.cfg
	echo -e "\tStarting PrimeNet\n"
	ln -s ../local.ini .
	nohup python3 ../../primenet.py -d -t 21600 -c "$i" >> "primenet.out" &
	sleep 1
	echo -e "\n\tStarting Mlucas\n"
	nohup nice ../Mlucas -cpu "${RUNS[i]}" -maxalloc "$maxalloc" &
	sleep 1
	popd >/dev/null
done
# maxalloc=$(echo ${#RUNS[*]} | awk '{ printf "%g", 90 / sqrt($1) }')
cat << EOF > jobs.sh
#!/bin/bash

# Copyright © 2020 Teal Dulcet
# Start Mlucas and the PrimeNet script
# Run: ./jobs.sh

set -e

pgrep -x Mlucas >/dev/null || {
echo -e "\nStarting Mlucas\n"
$(for i in "${!RUNS[@]}"; do echo "(cd 'run$i' && exec nohup nice ../Mlucas -cpu '${RUNS[i]}' -maxalloc $maxalloc &) "; done)
}

pgrep -f '^python3 \.\./\.\./primenet\.py' >/dev/null || {
echo -e "\nStarting PrimeNet\n"
$(for i in "${!RUNS[@]}"; do echo "(cd 'run$i' && exec nohup python3 ../../primenet.py -d -t 21600 -c $i >> 'primenet.out' &) "; done)
}
EOF
chmod +x jobs.sh
#crontab -l | { cat; echo "cd '$DIR' && ./jobs.sh"; } | crontab -
cat << EOF > Mlucas.sh
#!/bin/bash

# Copyright © 2020 Teal Dulcet
# Start Mlucas and the PrimeNet script if the computer has not been used in the specified idle time and stop it when someone uses the computer
# Run: '$DIR'/Mlucas.sh

if who -s | awk '{ print \$2 }' | (cd /dev && xargs -r stat -c '%U %X') | awk '{if ('"\${EPOCHSECONDS:-\$(date +%s)}"'-\$2<$TIME) { print \$1"\t"'"\${EPOCHSECONDS:-\$(date +%s)}"'-\$2; ++count }} END{if (count>0) { exit 1 }}' >/dev/null; then cd '$DIR' && ./jobs.sh; else pgrep -x Mlucas >/dev/null && killall -9 Mlucas; fi
EOF
chmod +x Mlucas.sh
echo -e "\nRun this command for it to start if the computer has not been used in the specified idle time and stop it when someone uses the computer:\n"
echo "crontab -l | { cat; echo \"* * * * * '$DIR'/Mlucas.sh\"; } | crontab -"
echo -e "\nTo edit the crontab, run \"crontab -e\""
