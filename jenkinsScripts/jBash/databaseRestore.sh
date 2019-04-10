#!/bin/bash

################################################
#
# Restore a sites database from a backup
#
# The tar file is stored in /export/<env>/backup
#
#################################################

echo
# GET siteInfo.sh
source ./utils/jBash/siteInfo.sh

# CHECK IF BACK UP EXISTS, EXIT IF NOT
echo "Looking for backup file in ${BACKUPDIR}..."

if [ -d "$BACKUPDIR" ]
then
    echo Site backup directory found
else
    echo No site backup directory found
    exit 1
fi

# GET MOST RECENT SQL BACK UP
LATESTBACKUP=$(ls -t "$BACKUPDIR" | grep .sql | head -1)

# RESTORE DB
echo "Restoring database with "$LATESTBACKUP"..."
mysql -h "$DBSERVER" -u"$USER"  -p"$PASS" "$SITE" < "$BACKUPDIR"/"$LATESTBACKUP"

# DRUSH
CURRENTDIR=$(pwd)

# cd to docroot
cd "$EXIST"

# update database
echo "Updating database and clearing cache at "$EXIST"..."
drush updb -y
# clear cache
drush cc all

cd "$CURRENTDIR"
echo "Database restored"
echo
