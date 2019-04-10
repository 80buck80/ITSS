#!/bin/bash

################################################
#
# Restores a site from the most recent backup
# tar file
#
#################################################

echo
# GET siteInfo.sh
source ./utils/jBash/siteInfo.sh

# CHECK IF BACK UP EXISTS, EXIT IF NOT
echo "Looking for backup file in ${BACKUPDIR}..."

if [ -d "$BACKUPDIR" ]
then
    echo Site backup found
else
    echo No site backup found
    exit 1
fi

# GET MOST RECENT SITE BACK UP AND EXTRACT IT
LATESTBACKUP=$(ls -t "$BACKUPDIR" | grep .tar.gz | head -1)
echo Extracting most recent back up: "$LATESTBACKUP"
tar xzf "$BACKUPDIR"/"$LATESTBACKUP" -C "$BACKUPDIR"

#check if files were extracted, if not exit
if [ -e "$BACKUPDIR"/"$SITE" ]
then
    echo Succesfull extraction
else
    echo Files were unable to be extracted
    exit 1
fi

# REMOVE DOCROOT
echo Removing docroot: "$EXIST"
rm -r "$EXIST"

# check if docroot was removed, if not exit
if [ ! -e "$EXIST" ]
then
    echo Succesfully removed docroot...
else
    echo The docroot was not able to be removed
    exit 1
fi

# MOVE BACKUP TO /export/<env>/virtual
echo Importing site backup...

# move backup docroot
rsync -zr "$BACKUPDIR"/"$SITE" "$ENVPATH"

# check if backup docroot was moved, if not exit
 if [ -e "$EXIST" ]
 then
     # remove docroot backup directory
     rm -r "$BACKUPDIR"/"$SITE"
     echo Succesfully imported backup docroot...
 else
     echo The backup docroot was not able to be imported
     exit 1
fi

# IMPORT DATABASE FROM DUMP
echo Importing database...


mysql -h "$DBSERVER" -u"$USER" -p"$PASS" "$SITE" < "$BACKUPDIR"/"$SITE".sql

echo Successfully imported database...

# remove db dump file from backup directory
rm "$BACKUPDIR"/"$SITE".sql

# SET PERMISSIONS
echo Setting permissions....

CURRENTDIR=$(pwd)

cd "$EXIST"

chown -R root:www-data .
find . -type d -exec chmod 750 '{}' \;
find . -type f -exec chmod 740 '{}' \;
setfacl -Rbk sites/all sites/default/files
find sites/all sites/default/files -type d -exec chmod 2770 '{}' \;
find sites/all sites/default/files -type f -exec chmod 760 '{}' \;

# CLEAR DRUPAL CACHE
echo Clearing Drupal cache...
drush cc all

cd "$CURRENTDIR"

echo Restore complete
echo
