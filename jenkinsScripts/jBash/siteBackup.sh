#!/bin/bash

################################################
#
# Creates a tar file containing a site's docroot
# and database dump
#
# The tar file is stored in /export/<env>/backup
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


# GET DATABASE DUMP
DUMP=""$SITE".sql"

echo Getting database dump...
mysqldump -h "$DBSERVER" -u"$USER"  -p"$PASS" --add-drop-database --databases "$SITE" > "$BACKUPDIR"/"$DUMP"

if [ -s "$BACKUPDIR"/"$DUMP" ]
then
	echo "SQL backup created..."
else
	echo "SQL backup failed"
	rm "$BACKUPDIR"/"$DUMP"
	exit 1

fi


# TAR THE DOCROOT AND DATABASE DUMP
TARNAME="$BACKUPDIR"/"$SITE".$(date +%Y-%m-%d.%H-%M-%S).tar.gz
echo Creating tar of "$SITE" docroot and database dump...
tar czf "$TARNAME" -C "$ENVPATH" "$SITE" -C "$BACKUPDIR" "$DUMP"
rm "$BACKUPDIR"/"$DUMP"

echo Backup successful
echo Site backup path: "$BACKUPDIR"
echo
