#!/bin/bash

# Copyright © 2020 Teal Dulcet
# wget -qO - https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/folding.sh | bash -s --
# ./folding.sh [Username] [Team number] [Passkey] [Power] [AccountToken]
# ./folding.sh "$USER" 0 "" medium "YOUR_TOKEN_HERE"
# ./folding.sh anonymous

# sudo dpkg -P fahclient
# sudo dpkg -P fahcontrol
# sudo dpkg -P fahviewer

DIR="folding"
if [[ $# -gt 5 ]]; then
	echo "Usage: $0 [Username] [Team number] [Passkey] [Power] [AccountToken]" >&2
	exit 1
fi
USERID=${1:-$USER}
TEAM=${2:-0}
PASSKEY=${3:-}
POWER=${4:-medium}
TOKEN=${5:-}
RE='^[0-9]+$'
if ! [[ $TEAM =~ $RE ]]; then
	echo "Usage: [Team number] must be a number" >&2
	exit 1
fi
RE='^[[:xdigit:]]{32}$'
if ! [[ -z $PASSKEY || $PASSKEY =~ $RE ]]; then
	echo "Usage: [Passkey] must be blank or a 32 digit hexadecimal number" >&2
	exit 1
fi
RE='^(light|medium|full)$'
if ! [[ $POWER =~ $RE ]]; then
	echo "Usage: [Power] is not valid" >&2
	exit 1
fi
echo -e "Username:\t$USERID"
echo -e "Team number:\t$TEAM"
echo -e "Passkey:\t$PASSKEY"
echo -e "Power:\t\t$POWER\n"
if [[ -z $TOKEN ]]; then
	echo "AccountToken is not set, using default settings"
else
	echo "AccountToken:\t\t$TOKEN"
if [[ -e idletime.sh ]]; then
	bash -- idletime.sh
else
	wget -qO - https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/idletime.sh | bash -s
fi
if [[ -d $DIR ]] && command -v fah-client >/dev/null; then
	echo "Error: Folding@home is already downloaded and installed" >&2
	exit 1
fi
if ! mkdir "$DIR"; then
	echo "Error: Failed to create directory $DIR" >&2
	exit 1
fi
cd "$DIR"
echo -e "Downloading Folding@home\n"
wget https://download.foldingathome.org/releases/public/fah-client/debian-10-64bit/release/fah-client_8.4.9_amd64.deb

echo -e "\nInstalling Folding@home"
echo -e "Please enter your password if prompted.\n"
if ! sudo mkdir -p /etc/fah-client; then
    echo "Error: Failed to create config directory" >&2
    exit 1
fi

MACHINE_NAME=$(hostname)

echo -e "Generating configuration file..."
sudo bash -c "cat > /etc/fah-client/config.xml" <<EOF
<config>
  <user v='$USERID'/>
  <team v='$TEAM'/>
  <passkey v='$PASSKEY'/>
  <power v='$POWER'/>
  <account-token v='$TOKEN'/>
  <machine-name v='$MACHINE_NAME'/>
</config>
EOF

if [[ $? -ne 0 ]]; then
	echo "Error: Failed to write configuration file" >&2
	exit 1
fi
sudo dpkg -i --force-depends fahclient_8.4.9_amd64.deb
sudo systemctl restart fah-client

if [[ -z $TOKEN ]]; then
	echo -e "Account Token is not set, edit /etc/fah-client/config.xml to add your token."
	echo -e "You can find your token here: https://v8-4.foldingathome.org/account/settings"
	
# sudo apt-get install -f
