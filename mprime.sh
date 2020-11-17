#!/bin/bash

# Teal Dulcet
# wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mprime.sh -qO - | bash -s --
# ./mprime.sh [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
# ./mprime.sh "$USER" "$HOSTNAME" 100 10
# ./mprime.sh ANONYMOUS

DIR="mprime"
FILE="p95v303b6.linux64.tar.gz"
SUM="EE54B56062FEB05C9F80963A4E3AE8555D0E59CA60DDBCBA65CE05225C9B9A79"
if [[ $# -gt 4 ]]; then
	echo "Usage: $0 [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]" >&2
	exit 1
fi
USERID=${1:-$USER}
COMPUTER=${2:-$HOSTNAME}
TYPE=${3:-150}
TIME=${4:-10}
RE='^([024568]|1(0[0124]|5[0123]|6[01])?)$'
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
	echo -e "Please enter your password when prompted.\n"
	sudo apt-get update -y
	sudo apt-get install expect -y
fi
TIME=$(echo "$TIME" | awk '{ printf "%g", $1 * 60 }')
if ! mkdir "$DIR"; then
	echo "Error: Failed to create directory $DIR" >&2
	exit 1
fi
cd "$DIR"
DIR=$PWD
echo -e "Downloading Prime95\n"
wget https://www.mersenne.org/ftp_root/gimps/$FILE
if [[ ! "$(sha256sum $FILE | head -c 64 | tr 'a-z' 'A-Z')" == "$SUM" ]]; then
	echo "Error: sha256sum does not match" >&2
	echo "Please run \"rm -r '$DIR'\" and try running this script again" >&2
	exit 1
fi
echo -e "\nDecompressing the files\n"
tar -xzvf $FILE
echo -e "\nSetting up Prime95\n"
if [[ -e ../mprime.exp ]]; then
	expect ../mprime.exp -- "$USERID" "$COMPUTER" "$TYPE"
else
	expect <(wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mprime.exp -qO -) -- "$USERID" "$COMPUTER" "$TYPE"
fi
echo -e "\nStarting Prime95\n"
nohup ./mprime &
echo -e "\nSetting it to start if the computer has not been used in the specified idle time and stop it when someone uses the computer\n"
#crontab -l | { cat; echo "cd \"$DIR\" && nohup ./mprime &"; } | crontab -
crontab -l | { cat; echo "* * * * * if who -s | awk '{ print \$2 }' | (cd /dev && xargs -r stat -c '\%U \%X') | awk '{if ('\"\${EPOCHSECONDS:-\$(date +\%s)}\"'-\$2<$TIME) { print \$1\"\t\"'\"\${EPOCHSECONDS:-\$(date +\%s)}\"'-\$2; ++count }} END{if (count>0) { exit 1 }}' >/dev/null; then pgrep mprime >/dev/null || (cd \"$DIR\" && nohup ./mprime &); else pgrep mprime >/dev/null && killall mprime; fi"; } | crontab -
