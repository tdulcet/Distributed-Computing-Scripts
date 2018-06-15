#!/bin/bash

# Teal Dulcet
# wget https://raw.github.com/tdulcet/Distributed-Computing-Scripts/master/folding.sh -qO - | bash -s --
# ./folding.sh [Username] [Team number] [Passkey] [Power]
# ./folding.sh $USER 0 "" medium
# ./folding.sh anonymous

# sudo dpkg -P fahclient
# sudo dpkg -P fahcontrol
# sudo dpkg -P fahviewer

DIR="folding"
if [[ "$#" -gt 4 ]]; then
	echo "Usage: $0 [Username] [Team number] [Passkey] [Power]" >&2
	exit 1
fi
USERID=${1:-$USER}
TEAM=${2:-0}
PASSKEY=${3:-}
POWER=${4:-medium}
RE='^[0-9]+$'
if ! [[ $TEAM =~ $RE ]]; then
	echo "Usage: [Team number] must be a number" >&2
	exit 1
fi
RE='^[a-fA-F0-9]{32}$'
if ! [[ -z "$PASSKEY" || $PASSKEY =~ $RE ]]; then
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
if [[ -d "$DIR" ]] && command -v FAHClient >/dev/null; then
	echo "Error: Folding@home is already downloaded and installed" >&2
	exit 1
fi
mkdir "$DIR"
cd "$DIR"
echo -e "Downloading Folding@home\n"
wget https://fah.stanford.edu/file-releases/public/release/fahclient/debian-testing-64bit/v7.4/fahclient_7.4.4_amd64.deb
wget https://fah.stanford.edu/file-releases/public/release/fahcontrol/debian-testing-64bit/v7.4/fahcontrol_7.4.4-1_all.deb
wget https://fah.stanford.edu/file-releases/public/release/fahviewer/debian-testing-64bit/v7.4/fahviewer_7.4.4_amd64.deb
echo -e "\nInstalling Folding@home"
echo -e "Please enter your password when prompted.\n"

# Adapted from: https://www.linuxquestions.org/questions/blog/bittner-195120/howto-automate-interactive-debian-package-installations-debconf-preseeding-2879/
# dpkg-deb -e fahclient_7.4.4_amd64.deb control_files/
# grep -e '^Template:' -e '^Type:' -e '^Default:' control_files/templates | xargs | sed -e 's/\s*Template: /\nFAHClient\t/g' -e 's/\s*Type: */\t/g' -e 's/\s*Default: */\t/g' > FAHClient.conf
sudo debconf-set-selections <<< "FAHClient	fahclient/user	string	$USERID
FAHClient	fahclient/team	string	$TEAM
FAHClient	fahclient/passkey	string	$PASSKEY
FAHClient	fahclient/power	select	$POWER
FAHClient	fahclient/autostart	boolean	true"

sudo dpkg -i --force-depends fahclient_7.4.4_amd64.deb
sudo dpkg -i --force-depends fahcontrol_7.4.4-1_all.deb
sudo dpkg -i --force-depends fahviewer_7.4.4_amd64.deb
# sudo apt-get install -f
