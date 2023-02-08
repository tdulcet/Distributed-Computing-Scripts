#!/bin/bash

# Copyright © 2020 Teal Dulcet
# Start the correct version of GpuOwl based on the next assignment in the worktodo file
# Run: ./gpuowl [GpuOwl arguments]...

set -e

# GpuOwl directories

# 1. Current version of GpuOwl (master branch)
#    Supports PRP tests and standalone P-1 stage 1 (requires MPrime for stage 2)
DIR1="gpuowl-master"
# 2. GpuOwl v7.2-112
#    Supports PRP tests combined with P-1
DIR2="gpuowl-7.2"
# 3. GpuOwl v6.11 (v6 branch)
#    Supports LL and standalone P-1 tests
DIR3="gpuowl-6"

# GpuOwl arguments

# 1. Current version of GpuOwl (master branch)
ARGS1=( -unsafeMath )
# 2. GpuOwl v7.2-112
ARGS2=( -unsafeMath )
# 3. GpuOwl v6.11 (v6 branch)
ARGS3=( -cleanup -log 10000 )

# GpuOwl version to use for each worktype

# PRP tests that need P-1
GPUOWL_PRP_PM1=2
# PRP tests that do NOT need P-1
GPUOWL_PRP=1
# LL tests
GPUOWL_LL=3
# Standalone P-1 tests
GPUOWL_PM1=3

# worktodo and results files for the PrimeNet script
WorkFile="worktodo.ini"
ResultsFile="results.ini"

# worktodo and results files for GpuOwl
aWorkFile="worktodo.txt"
aResultsFile="results.txt"

# Limit GpuOwl GPU memory usage (MiB)
# maxAlloc=1024

# Device number
DEVICE=0

# GpuOwl arguments for all versions
ARGS=(
-device $DEVICE
# -results "$aResultsFile"
# -use STATS

)

# Automatically restart
RESTART=1

# Ignore-failure
# FAILURE=1

# Time to delay automatic restart after failure (seconds)
TIME=1

# Lock file
LOCK="~lock"

exec 200>"$LOCK"

if ! flock -n 200; then
	echo "Error: This script is already running." >&2
	exit 1
fi

workpattern='^(Test|DoubleCheck|PRP(DC)?|P[Ff]actor|Cert)=((([[:xdigit:]]{32})|[Nn]/[Aa]|0),)?((-?[[:digit:]]+(\.[[:digit:]]+)?|"[[:digit:]]+(,[[:digit:]]+)*")(,|$)){3,9}$'

ARGS+=( "$@" )

if command -v lspci >/dev/null; then
	mapfile -t GPU < <(lspci 2>/dev/null | grep -i 'vga\|3d\|2d' | sed -n 's/^.*: //p')
fi
if [[ -n "$GPU" ]]; then
	echo -e "\nGraphics Processor (GPU):\t${GPU[0]}$([[ ${#GPU[*]} -gt 1 ]] && printf '\n\t\t\t\t%s' "${GPU[@]:1}")"
	# echo -e "Graphics Processor (GPU):\t${GPU[DEVICE]}"
fi

if command -v clinfo >/dev/null; then
	mapfile -t TOTAL_GPU_MEM < <(clinfo --raw | sed -n 's/.*CL_DEVICE_GLOBAL_MEM_SIZE *//p')
	for i in "${!TOTAL_GPU_MEM[@]}"; do
		TOTAL_GPU_MEM[i]=$(( TOTAL_GPU_MEM[i] / 1024 / 1024 ))
	done
elif command -v nvidia-smi >/dev/null && nvidia-smi >/dev/null; then
	mapfile -t TOTAL_GPU_MEM < <(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | grep -iv 'not supported')
fi
if [[ -n "$TOTAL_GPU_MEM" ]]; then
	# echo -e -n "\tGPU Memory (RAM):\t"
	# for i in "${!TOTAL_GPU_MEM[@]}"; do
		# echo -n "$([[ $i -gt 0 ]] && echo ", ")$(printf "%'d" "${TOTAL_GPU_MEM[i]}") MiB ($(numfmt --from=iec --to=iec-i "${TOTAL_GPU_MEM[i]}M")B)"
	# done
	# echo
	echo -e -n "\tGPU Memory (RAM):\t$(printf "%'d" "${TOTAL_GPU_MEM[DEVICE]}") MiB ($(numfmt --from=iec --to=iec-i "${TOTAL_GPU_MEM[DEVICE]}M")B)"
fi
if [[ -z "$maxAlloc" ]]; then
	if [[ -n "$TOTAL_GPU_MEM" ]]; then
		maxAlloc=${TOTAL_GPU_MEM[DEVICE]}
	else
		echo "Warning: Could not determine total GPU Memory (RAM), please install clinfo. Assuming 1024 MiB (1 GiB)."
		maxAlloc=1024
	fi
fi
ARGS+=( -maxAlloc "$(echo "$maxAlloc" | awk '{ printf "%d", $1 * 0.9 }')M" )

DISK_USAGE=$(df -k . | tail -n +2)
if [[ -n "$DISK_USAGE" ]]; then
	DISK_MOUNT=$(echo "$DISK_USAGE" | awk '{ print $6 }')
	TOTAL_DISK=$(echo "$DISK_USAGE" | awk '{ print $2 }')
	AVAILABLE_DISK=$(echo "$DISK_USAGE" | awk '{ print $4 }')
	echo -e "Disk space available:\t\t${DISK_MOUNT}: $(numfmt --from=iec --to=iec-i "${AVAILABLE_DISK}K")B / $(numfmt --from=iec --to=iec-i "${TOTAL_DISK}K")B ($(numfmt --from=iec --to=si "${AVAILABLE_DISK}K")B / $(numfmt --from=iec --to=si "${TOTAL_DISK}K")B)"
fi

echo

trap 'trap - INT; kill -INT "$$"' INT

while true; do
	date

	if [[ -r "$aResultsFile" ]] && mapfile -t aresults < "$aResultsFile" && [[ ${#aresults[*]} -gt 0 ]]; then
		printf "Found %'d new result(s) in '%s'. Moving to '%s'.\n" ${#aresults[*]} "$aResultsFile" "$ResultsFile"
		for result in "${aresults[@]}"; do
			if echo "$result" | grep -q 'gpuowl'; then
				if [[ -r "$WorkFile" ]] && mapfile -t worktodo < "$WorkFile" && [[ ${#worktodo[*]} -gt 0 ]]; then
					if command -v jq >/dev/null; then
						exponent=$(echo "$result" | jq -r '.exponent')
						worktype=$(echo "$result" | jq -r '.worktype')
						status=$(echo "$result" | jq -r '.status')
					else
						exponent=$(echo "$result" | python3 -c 'import sys, json; print(json.load(sys.stdin)["exponent"])')
						worktype=$(echo "$result" | python3 -c 'import sys, json; print(json.load(sys.stdin)["worktype"])')
						status=$(echo "$result" | python3 -c 'import sys, json; print(json.load(sys.stdin)["status"])')
					fi
					RE='^PRP'
					if [[ "$worktype" == 'LL' ]]; then
						if [[ "$status" == 'P' ]]; then
							echo 'New Mersenne Prime!!!! M'"$exponent"' is prime!'
						fi
					elif [[ $worktype =~ $RE ]]; then
						if [[ "$status" == 'P' ]]; then
							echo 'New Probable Prime!!!! '"$exponent"' is a probable prime!'
						fi
					fi
					for i in "${!worktodo[@]}"; do
						if [[ ${worktodo[i]} =~ $workpattern ]]; then
							work_type=${BASH_REMATCH[1]}
							if [[ "$work_type" == "Test" || "$work_type" == "DoubleCheck" ]]; then
								idx=2
							else
								idx=4
							fi
							n=$(echo "${worktodo[i]}" | cut -d, -f $idx)
							if [[ $exponent -eq $n ]]; then
								if [[ "$worktype" == 'LL' ]] && [[ "$work_type" == "Test" || "$work_type" == "DoubleCheck" ]]; then
									unset 'worktodo[i]'
								elif [[ $worktype =~ $RE ]] && [[ "$work_type" == "PRP" || "$work_type" == "PRPDC" ]]; then
									unset 'worktodo[i]'
								elif [[ "$worktype" == 'PM1' ]] && { [[ "$work_type" == "PFactor" || "$work_type" == "Pfactor" ]] || [[ "$status" == 'F' ]]; }; then
									unset 'worktodo[i]'
								fi
							fi
						fi
					done
					printf '%s\n' "${worktodo[@]}" > "$WorkFile"
				fi
			else
				echo "Warning: Unknown result: $result"
			fi
		done
		printf '%s\n' "${aresults[@]}" >> "$ResultsFile"
		> "$aResultsFile"
	else
		echo "No results found."
	fi

	if ! [[ -r "$aWorkFile" ]] || ! mapfile -t aworktodo < "$aWorkFile" || ! [[ ${#aworktodo[*]} -gt 0 ]]; then
		if [[ -r "$WorkFile" ]] && mapfile -t worktodo < "$WorkFile" && [[ ${#worktodo[*]} -gt 0 ]]; then
			printf "Found %'d work to do(s) in the '%s' file. Copying the first one to '%s'.\n" ${#worktodo[*]} "$WorkFile" "$aWorkFile"
			printf '%s\n' "${worktodo[0]}" >> "$aWorkFile"
			mapfile -t aworktodo < "$aWorkFile"
		else
			echo "Error: No work to do. Please run the PrimeNet script or manually add some work to the '$WorkFile' file." >&2
			exit 1
		fi
	else
		printf "Found %'d work to do(s) in the '%s' file.\n" ${#aworktodo[*]} "$aWorkFile"
	fi

	for work in "${aworktodo[@]}"; do
		if [[ $work =~ $workpattern ]]; then
			work_type=${BASH_REMATCH[1]}
			case "$work_type" in
			'Test' )
				work_type_str="Lucas-Lehmer test"
			;;
			'DoubleCheck' )
				work_type_str="Double-check"
			;;
			'PRP' )
				work_type_str="PRP"
			;;
			'PRPDC' )
				work_type_str="PRPDC"
			;;
			'PFactor' | 'Pfactor' )
				work_type_str="P-1"
			;;
			'Cert' )
				work_type_str="Certify"
			;;
			esac
			if [[ "$work_type" == "Test" || "$work_type" == "DoubleCheck" ]]; then
				idx=2
			else
				idx=4
			fi
			n=$(echo "$work" | cut -d, -f $idx)
			printf "Starting %s of the exponent %'d\n" "$work_type_str" "$n"
			case "$work_type" in
			'Test' | 'DoubleCheck' )
				temp=$GPUOWL_LL
			;;
			'PRP' | 'PRPDC' )
				if (( $(echo "$work" | awk -F, '{ print ($7>0) }') )); then
					temp=$GPUOWL_PRP_PM1
				else
					temp=$GPUOWL_PRP
				fi
			;;
			'PFactor' | 'Pfactor' )
				temp=$GPUOWL_PM1
			;;
			* )
				echo "Error: Unsupported worktype for GpuOwl: $work" >&2
				exit 1
			;;
			esac
			dir="DIR$temp"
			args="ARGS${temp}[@]"
			echo -e "with GpuOwl $(<${!dir}/version.inc).\n"
			gpuowl=(nice "./${!dir}/gpuowl" "${!args}" "${ARGS[@]}")
			if [[ -z "$RESTART" ]]; then
				exec "${gpuowl[@]}"
			else
				"${gpuowl[@]}"
				E=$?
				if (( E )); then
					if [[ -z "$FAILURE" ]]; then
						echo "Error: GpuOwl terminated with non-zero exit code: $E" >&2
						echo "If this is a GpuOwl bug, please create an issue: https://github.com/preda/gpuowl/issues" >&2
						exit 1
					fi
					sleep -- "$TIME"
				fi
			fi
			break
		else
			echo "Warning: Unknown worktype. Line ignored: ${work@Q}"
		fi
	done
done

