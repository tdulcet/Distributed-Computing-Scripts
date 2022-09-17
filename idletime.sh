#!/bin/bash

# Teal Dulcet
# Outputs system idle time
# wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/idletime.sh -qO - | bash -s --
# ./idletime.sh

if [[ $# -ne 0 ]]; then
	echo "Usage: $0" >&2
	exit 1
fi

# Adapted from: https://github.com/tdulcet/Remote-Servers-Status/blob/master/status.sh
# getSecondsAsDigitalClock <seconds>
getSecondsAsDigitalClock() {
	local sec_num=$1
	local d=$(( sec_num / 86400 ))
	local h=$(( (sec_num % 86400) / 3600 ))
	local m=$(( (sec_num % 86400 % 3600) / 60 ))
	local s=$(( sec_num % 86400 % 3600 % 60 ))
	local text=''
	if [[ $d -ne 0 ]]; then
		text+="$(printf "%'d" "$d") days "
	fi
	if [[ $d -ne 0 || $h -ne 0 ]]; then
		text+="$h hours "
	fi
	if [[ $d -ne 0 || $h -ne 0 || $m -ne 0 ]]; then
		text+="$m minutes "
	fi
	text+="$s seconds"
	echo "$text"
}

IDLETIME=$(awk '{ print int($2) }' /proc/uptime)
echo -e "System idle time for all processor (CPU) threads since the last boot:\t$(getSecondsAsDigitalClock "$IDLETIME")\n"
