#!/bin/bash

# Copyright © 2020 Teal Dulcet
# Benchmark GpuOwl
# Run: ./bench.sh <GpuOwl binary> [Iterations] [ROE option]

set -e

if [[ $# -lt 1 || $# -gt 3 ]]; then
	echo "Usage: $0 <GpuOwl binary> [Iterations] [ROE option]" >&2
	exit 1
fi

# GpuOwl
GPUOWL=$1

# Number of iterations
ITERS=${2:-20000}

# Device number
DEVICE=0

# Min FFT length (in K)
MIN=1024
# MIN=1
# Max FFT length (in K)
MAX=8192
# MAX=32768

# GpuOwl -use option to show roundoff error (ROE)
# USE=STATS
# USE=ROE1,ROE2
USE=${3:-ROE1,ROE2}

# GpuOwl arguments
ARGS=(
	-device $DEVICE
	# -log 10000
	-use "$USE"

)

if command -v clinfo >/dev/null; then
	mapfile -t TOTAL_GPU_MEM < <(clinfo --raw | sed -n 's/.*CL_DEVICE_GLOBAL_MEM_SIZE *//p')
	for i in "${!TOTAL_GPU_MEM[@]}"; do
		TOTAL_GPU_MEM[i]=$((TOTAL_GPU_MEM[i] / 1024 / 1024))
	done
elif command -v nvidia-smi >/dev/null && nvidia-smi >/dev/null; then
	mapfile -t TOTAL_GPU_MEM < <(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | grep -iv 'not supported')
fi
if [[ -n $TOTAL_GPU_MEM ]]; then
	ARGS+=(-maxAlloc "$(echo "${TOTAL_GPU_MEM[DEVICE]}" | awk '{ printf "%d", $1 * 0.9 }')M")
fi

if [[ ! -x $GPUOWL ]]; then
	echo "Error: GpuOwl binary not found" >&2
	exit 1
fi

RE='^[0-9]+$'
if ! [[ $ITERS =~ $RE ]]; then
	echo "Usage: [Iterations] must be a number" >&2
	exit 1
fi
if ! ((ITERS && ITERS % 10000 == 0)); then
	echo "Usage: [Iterations] must be a multiple of 10000" >&2
	exit 1
fi

output=$("$GPUOWL" -h)
if echo "$output" | grep -q '^-unsafeMath'; then
	ARGS+=(-unsafeMath)
# elif echo "$output" | grep -q '^-safeMath'; then
	# ARGS+=( -safeMath )
fi

{
	file=$(dirname "$GPUOWL")/version.inc
	if [[ -r $file ]]; then
		cat "$file"
	fi
	printf 'FFT length\tVariant\tMax exp\tus/iter\tError '
	if [[ $USE == STATS ]]; then
		printf 'mean / max / SD / z / N'
	else
		printf 'max / SD / N'
	fi
	printf '\n\n'
} >>bench.txt

DIR=$PWD
cd /tmp

output=$(echo "$output" | grep '^FFT' | tail -n +2)
ffts=$(echo "$output" | awk '{ print $2 }')
mapfile -t FFTS <<<"$ffts"
mapfile -t AFFTS < <(echo "$ffts" | numfmt --from=iec)
mapfile -t MAX_EXPS < <(echo "$output" | awk -F'[][ ]+' '{ print $5 }' | numfmt --from=si)
mapfile -t VARIANTS < <(echo "$output" | sed -n 's/^.*]  //p')

echo -e "\nWarming up GPU...\n"
exp=2976221
"$DIR/$GPUOWL" -prp "$exp" -iters $((ITERS * 10)) -fft 256:3:256 "${ARGS[@]}"
rm -rf -- "$exp" gpuowl.log

for i in "${!MAX_EXPS[@]}"; do
	if [[ -n $MIN && ${AFFTS[i]} -lt $((MIN * 1024)) ]]; then
		continue
	elif [[ -n $MAX && ${AFFTS[i]} -gt $((MAX * 1024)) ]]; then
		break
	fi
	if [[ ${MAX_EXPS[i]} -ge 100 ]]; then
		exp=$(seq $((MAX_EXPS[i] - 100)) "${MAX_EXPS[i]}" | factor | awk 'NF == 2 { print $2 }' | tail -n 1)
		printf "\nTiming FFT length: %s (%s),\tExponent: %'d\n" "${FFTS[i]}" "$(numfmt --to=iec "${AFFTS[i]}")" "$exp"
		variants=(${VARIANTS[i]})
		for j in "${!variants[@]}"; do
			printf "\n\t%'d Variant: %s\n\n" $((j + 1)) "${variants[j]}"
			"$DIR/$GPUOWL" -prp "$exp" -iters "$ITERS" -fft "${variants[j]}" -nospin "${ARGS[@]}" | grep -i 'gpuowl\|loaded\|on-load\|[[:digit:]]\{6,\} \(LL\|P1\|OK\|EE\)\? \+[[:digit:]]\{4,\}\|check\|jacobi\|roundoff\|ROE=\|error\| E :\|exception\|exiting'
			time=''
			if output=$(grep '[[:digit:]]\{7,\} \(LL\|P1\|OK\|EE\)\? \+[[:digit:]]\{5,\}' gpuowl.log | grep "$ITERS"); then
				RE='([[:digit:]]+) us/it'
				if [[ $output =~ $RE ]]; then
					time=${BASH_REMATCH[1]}
				fi
			fi
			mean=''
			max=''
			stddev=''
			z=''
			N=''
			if output=$(grep -i 'roundoff' gpuowl.log); then
				output=$(echo "$output" | tail -n 1)
				RE='mean ([[:digit:]]+(\.[[:digit:]]+)?)'
				if [[ $output =~ $RE ]]; then
					mean=${BASH_REMATCH[1]}
				fi
				RE='max ([[:digit:]]+(\.[[:digit:]]+)?)'
				if [[ $output =~ $RE ]]; then
					max=${BASH_REMATCH[1]}
				fi
				RE='SD ([[:digit:]]+(\.[[:digit:]]+)?)'
				if [[ $output =~ $RE ]]; then
					stddev=${BASH_REMATCH[1]}
				fi
				RE=' z ([[:digit:]]+(\.[[:digit:]]+)?)'
				if [[ $output =~ $RE ]]; then
					z=${BASH_REMATCH[1]}
				fi
				RE='N=([[:digit:]]+)'
				if [[ $output =~ $RE ]]; then
					N=${BASH_REMATCH[1]}
				fi
			elif output=$(grep -i 'ROE=' gpuowl.log); then
				output=$(echo "$output" | tail -n 1)
				RE='ROE=([[:digit:]]+(\.[[:digit:]]+)?) ([[:digit:]]+(\.[[:digit:]]+)?) ([[:digit:]]+)'
				if [[ $output =~ $RE ]]; then
					max=${BASH_REMATCH[1]}
					stddev=${BASH_REMATCH[3]}
					N=${BASH_REMATCH[5]}
				fi
			fi
			{
				printf '%s\t%s\t%s\t%s\t' "${FFTS[i]}" "${variants[j]}" "$exp" "${time:--}"
				if [[ $USE == STATS ]]; then
					printf '%s / %s / %s / %s / %s' "$mean" "$max" "$stddev" "$z" "$N"
				else
					printf '%s / %s / %s' "$max" "$stddev" "$N"
				fi
				echo
			} >>"$DIR/bench.txt"
			rm -rf -- "$exp" gpuowl.log
			# sleep 1
		done
	fi
	echo >>"$DIR/bench.txt"
done
echo >>"$DIR/bench.txt"
