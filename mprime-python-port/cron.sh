#!/bin/bash
# Usage: ./cron.sh
crontab -l | { cat; echo "* * * * * if who -s | awk '{ print \$2 }' | (cd /dev && xargs -r stat -c '\%U \%X') | awk '{if ('\"\$(date +\%s)\"'-\$2<$TIME) { print \$1\"\t\"'\"\$(date +\%s)\"'-\$2; ++count }} END{if (count>0) { exit 1 }}' > /dev/null; then pgrep mprime > /dev/null || (cd $DIR && nohup ./mprime &); else pgrep mprime > /dev/null && killall mprime; fi"; } | crontab -
