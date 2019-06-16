#!/bin/bash

# Teal Dulcet
# wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/boinc.sh -qO - | bash -s --
# ./boinc.sh <URL> <E-mail> <Password>
# ./boinc.sh <URL> <Account Key>
# ./boinc.sh "https://www.worldcommunitygrid.org" "$USER" <Password>
# ./boinc.sh "https://www.worldcommunitygrid.org" <Account Key>

# cd /usr/bin
# boinccmd --project "https://www.worldcommunitygrid.org" detach

# sudo apt-get purge boinc-client boinc-manager -y

if [[ "$#" -ne 2 && "$#" -ne 3 ]]; then
	echo "Usage: $0 <URL> <E-mail> <Password> or $0 <URL> <Account Key>" >&2
	exit 1
fi
URL=$1
echo -e "URL:\t\t$URL"
if [[ "$#" -eq 3 ]]; then
	EMAIL=$2
	PASSWORD=$3
	echo -e "E-mail:\t\t$EMAIL"
	echo -e "Password:\t$PASSWORD\n"
elif [[ "$#" -eq 2 ]]; then
	KEY=$2
	echo -e "Account Key:\t$KEY\n"
fi
if command -v boinccmd >/dev/null; then
	echo "Error: Boinc is already installed" >&2
	exit 1
fi
echo -e "Downloading and installing Boinc"
echo -e "Please enter your password when prompted.\n"
sudo apt-get update -y
sudo apt-get install boinc -y
echo -e "\nSetting up Boinc\n"
cd /usr/bin
if [[ "$#" -eq 3 ]]; then
	if ! KEY=$(boinccmd --lookup_account "$URL" "$EMAIL" "$PASSWORD" | sed -n 's/^.*account key: //p') || [[ -z "$KEY" ]]; then
		echo "Error: Account not found" >&2
		exit 1
	fi
fi
boinccmd --project_attach "$URL" "$KEY"
