#!/bin/bash

################################################
#
# Create a database backup of a site
#
# The backup is stored in /export/<env>/backup
#
#################################################

echo
# GET siteInfo.sh
source ./utils/jBash/siteInfo.sh

# CREATE backups DIRECTORY IF DOES NOT  EXIST
if [ ! -d "$BACKUPDIR" ]
then
	mkdir "$BACKUPDIR"
fi


# GET DATABASE BACKUP
DUMP=""$SITE".$(date +%Y-%m-%d.%H-%M-%S).sql"

echo Creating database backup...
mysqldump -h "$DBSERVER" -u"$USER"  -p"$PASS" --add-drop-database --databases "$SITE" > "$BACKUPDIR"/"$DUMP"

if [ -s "$BACKUPDIR"/"$DUMP" ]
then
	echo "SQL backup created at "$BACKUPDIR"/"$DUMP""
else
	echo "SQL backup failed"
	rm "$BACKUPDIR"/"$DUMP"
	exit 1

fi
