#!/bin/bash

################################################
#
# Download sql dump to Jenkins Workspace
#
#################################################

echo
# GET siteInfo.sh
source ./utils/jBash/siteInfo.sh

echo Downloading database backup...
d=`date +%F`
DUMP=$SITE\_$d.sql
mysqldump -h "$DBSERVER" -u"$USER"  -p"$PASS" --add-drop-database --databases "$SITE" > "$DUMP"

if [ -s "$DUMP" ]
then
	echo "Database dump saved to Jenkins workspace"
else
	echo "SQL download failed"
	exit 1

fi
