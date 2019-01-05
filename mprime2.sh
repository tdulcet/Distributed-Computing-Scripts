#!/bin/bash

# Teal Dulcet
# wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mprime2.sh -qO - | bash -s --
# ./mprime2.sh <Computer number> [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]
# ./mprime2.sh <N> "$USER" "$HOSTNAME" 100 10
# ./mprime2.sh <N> ANONYMOUS

DIR="mprime"
FILE="p95v294b8.linux64.tar.gz"
SUM="A0C86DBC1F5259DC7FCBB7CD1AC82EEE618A4538B2A6D3AFE60F96BFE36D82A4"
if [[ "$#" -lt 1 || "$#" -gt 5 ]]; then
	echo "Usage: $0 <Computer number> [PrimeNet User ID] [Computer name] [Type of work] [Idle time to run]" >&2
	exit 1
fi
N=$1
USERID=${2:-$USER}
COMPUTER=${3:-$HOSTNAME}
TYPE=${4:-100}
TIME=${5:-10}
RE='^[0-9]+$'
if ! [[ $N =~ $RE ]]; then
	echo "Usage: <Computer number> must be a number" >&2
	exit 1
fi
RE='^([024568]|1(0[0124]|5[0124]|6[01])?)$'
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
if ! command -v expect >/dev/null; then
	echo -e "Installing Expect"
	echo -e "Please enter your password when prompted.\n"
	sudo apt-get update -y
	sudo apt-get install expect -y
fi
TIME=$(echo "$TIME" | awk '{ printf "%g", $1 * 60 }')
if [[ -d "$DIR" && -x "$DIR/mprime" ]]; then
	echo -e "Prime95 is already downloaded\n"
	cd "$DIR"
	DIR=$(pwd)
else
	if ! mkdir "$DIR"; then
		echo "Error: Failed to create directory $DIR" >&2
		exit 1
	fi
	cd "$DIR"
	DIR=$(pwd)
	echo -e "Downloading Prime95\n"
	wget https://www.mersenne.org/ftp_root/gimps/$FILE
	if [[ ! "$(sha256sum $FILE | head -c 64 | tr 'a-z' 'A-Z')" = "$SUM" ]]; then
		echo "Error: sha256sum does not match" >&2
		echo "Please run \"rm -r $DIR\" and try running this script again" >&2
		exit 1
	fi
	echo -e "\nDecompressing the files\n"
	tar -xzvf $FILE
fi
echo -e "\nSetting up Prime95\n"
expect <(wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/mprime2.exp -qO -) -- "$USERID" "$COMPUTER" "$TYPE" "$N"
echo -e "\nStarting Prime95\n"
nohup ./mprime -A$N &
echo -e "\nSetting it to start if the computer has not been used in the specified idle time and stop it when someone uses the computer\n" | fold -s -w "$(tput cols)"
#crontab -l | { cat; echo "cd $DIR && nohup ./mprime -A$N &"; } | crontab -
crontab -l | { cat; echo "* * * * * if who -s | awk '{ print \$2 }' | (cd /dev && xargs -r stat -c '\%U \%X') | awk '{if ('\"\$(date +\%s)\"'-\$2<$TIME) { print \$1\"\t\"'\"\$(date +\%s)\"'-\$2; ++count }} END{if (count>0) { exit 1 }}' > /dev/null; then pgrep mprime > /dev/null || (cd $DIR && nohup ./mprime -A$N &); else pgrep mprime > /dev/null && killall mprime; fi"; } | crontab -
