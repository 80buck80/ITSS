#!/bin/bash

################################################
#
# This will overwrite the destination database
# with the source database
#
# The tar file is stored in /export/<env>/backup
#
#################################################

echo

# SPLIT ARGUMENT BY COMMA
IFS=',' args=(${1})


# GET SITE INFO FROM SOURCE
source ./utils/jBash/siteInfo.sh ${args[0]}
sourceSite="$SITE"
sourceDB="$DBSERVER"
echo
# echo ${sourceSite}
# echo ${sourceDB}

# GET SITE INFO FROM DESTINATION
source ./utils/jBash/siteInfo.sh ${args[1]}
destSite="$SITE"
destDB="$DBSERVER"
destDocroot="$EXIST"

# BACK UP DESTINATION DATABASE
echo "Backing up ${destSite} database..."
source ./utils/jBash/databaseBackup.sh ${args[1]} > /dev/null
echo "${destSite} database backed up"

echo

 # GET SQL DUMP OF SOURCE
echo "Getting database dump of ${sourceSite}..."
source ./utils/jBash/databaseDownload.sh ${args[0]} > /dev/null
echo "Database dumped"
echo
# SET DROP DATABASE IN DUMP FILE TO DESTINATION DB
dump=$(echo *.sql)
sed -i "s/$sourceSite/$destSite/g" "$dump"

# OVERWRITE DESTINATION DB WITH SOURCE DB
echo "Overwritting destination database with source database..."
mysql -h "$destDB" -u"$USER"  -p"$PASS" "$destSite" < "$dump"

# DRUSH
CURRENTDIR=$(pwd)

# cd to docroot
cd "$destDocroot"

# update database
echo "Updating database and clearing cache at "$destDocroot"..."
drush updb -y
# clear cache
drush cc all

cd "$CURRENTDIR"
rm "$dump"

echo "Destination database successfully overwritten"
