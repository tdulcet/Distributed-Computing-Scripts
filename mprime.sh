#!/bin/bash

# Teal Dulcet
# wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mprime.sh -qO - | bash -s --
# ./mprime.sh [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]
# ./mprime.sh "$USER" "$HOSTNAME" 150 10
# ./mprime.sh ANONYMOUS

DIR="mprime"
FILE="p95v307b9.linux64.tar.gz"
SUM="d47d766c734d1cca4521cf7b37c1fe351c2cf1fbe5b7c70c457061a897a5a380"
if [[ $# -gt 4 ]]; then
	echo "Usage: $0 [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run (mins)]" >&2
	exit 1
fi
USERID=${1:-$USER}
COMPUTER=${2:-$HOSTNAME}
TYPE=${3:-150}
TIME=${4:-10}
RE='^([024568]|1(0[0124]|5[012345]|6[01])?)$'
if ! [[ $TYPE =~ $RE ]]; then
	echo "Usage: [Type of work] is not a valid number" >&2
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
if [[ -d "$DIR" ]]; then
	echo "Error: Prime95 is already downloaded" >&2
	exit 1
fi
if ! command -v expect >/dev/null; then
	echo -e "Installing Expect"
	echo -e "Please enter your password if prompted.\n"
	sudo apt-get update -y
	sudo apt-get install expect -y
fi
TIME=$(echo "$TIME" | awk '{ printf "%g", $1 * 60 }')

MEMINFO=$(</proc/meminfo)
TOTAL_PHYSICAL_MEM=$(echo "$MEMINFO" | awk '/^MemTotal:/ {print $2}')
echo -e "\nTotal memory (RAM):\t\t$(printf "%'d" $((TOTAL_PHYSICAL_MEM / 1024))) MiB ($(printf "%'d" $((((TOTAL_PHYSICAL_MEM * 1024) / 1000) / 1000))) MB)\n"

if ! mkdir "$DIR"; then
	echo "Error: Failed to create directory $DIR" >&2
	exit 1
fi
cd "$DIR"
DIR=$PWD
echo -e "Downloading Prime95\n"
wget https://www.mersenne.org/ftp_root/gimps/$FILE
if [[ "$(sha256sum $FILE | head -c 64)" != "$SUM" ]]; then
	echo "Error: sha256sum does not match" >&2
	echo "Please run \"rm -r $DIR\" make sure you are using the latest version of this script and try running it again" >&2
	echo "If you still get this error, please create an issue: https://github.com/tdulcet/Distributed-Computing-Scripts/issues" >&2
	exit 1
fi
echo -e "\nDecompressing the files\n"
tar -xzvf $FILE
echo -e "\nOptimizing Prime95 for your computer\nThis may take a while…\n"
./mprime -b
echo -e "\nSetting up Prime95\n"
if [[ -e ../mprime.exp ]]; then
	cp ../mprime.exp .
else
	wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mprime.exp -q
fi
sed -i '/^expect {/a \\t"stage 2 memory in GB (*):" { sleep 1; send -- "'"$(echo "$TOTAL_PHYSICAL_MEM" | awk '{ printf "%g", ($1 * 0.8) / 1024 / 1024 }')"'\\r"; exp_continue }' mprime.exp
expect mprime.exp -- "$USERID" "$COMPUTER" "$TYPE"
echo -e "\nStarting Prime95\n"
nohup ./mprime &
echo -e "\nSetting it to start if the computer has not been used in the specified idle time and stop it when someone uses the computer\n"
#crontab -l | { cat; echo "cd '$DIR' && nohup ./mprime &"; } | crontab -
crontab -l | { cat; echo "* * * * * if who -s | awk '{ print \$2 }' | (cd /dev && xargs -r stat -c '\%U \%X') | awk '{if ('\"\${EPOCHSECONDS:-\$(date +\%s)}\"'-\$2<$TIME) { print \$1\"\t\"'\"\${EPOCHSECONDS:-\$(date +\%s)}\"'-\$2; ++count }} END{if (count>0) { exit 1 }}' >/dev/null; then pgrep -x mprime >/dev/null || (cd '$DIR' && exec nohup ./mprime &); else pgrep -x mprime >/dev/null && killall mprime; fi"; } | crontab -
