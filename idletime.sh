#!/bin/bash

# Copyright © Teal Dulcet
# Outputs system idle time
# wget -qO - https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/idletime.sh | bash -s --
# ./idletime.sh

if [[ $# -ne 0 ]]; then
	echo "Usage: $0" >&2
	exit 1
fi

# Adapted from: https://github.com/tdulcet/Remote-Servers-Status/blob/master/status.sh
# outputduration <seconds>
outputduration() {
	local sec=$1
	local d=$((sec / 86400))
	local h=$(((sec % 86400) / 3600))
	local m=$(((sec % 3600) / 60))
	local s=$((sec % 60))
	local text=''
	if ((d)); then
		text+="$(printf "%'d" "$d") days "
	fi
	if ((d || h)); then
		text+="$h hours "
	fi
	if ((d || h || m)); then
		text+="$m minutes "
	fi
	text+="$s seconds"
	echo "$text"
}

IDLETIME=$(awk '{ print int($2) }' /proc/uptime)
echo -e "System idle time for all processor (CPU) threads since the last boot:\t$(outputduration "$IDLETIME")\n"
