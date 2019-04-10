#!/bin/bash

###################################################
#
# Gets the following site information:
#
# URL
# Environment
# Docroot
# Database server
#
##################################################

echo "       SITE INFO          "

#CLEAN URL ARGUMENT
SITE=$(echo "$1" | grep -Po '[a-zA-Z0-9-]*(-dev|-stg)?\.*[a-zA-Z0-9]*(-dev|-stg)?\.unt\.edu')

# swap . for _
SITE=$(echo "$SITE" | sed 's/[.-]/\_/g')
echo "Site URL: $SITE"

# GET SITE ENVIRONMNET
ENV=$(echo "$SITE" | grep -Eo '\_dev|\_stg')
ENV=$(echo "$ENV" | sed 's/\_//g')

# check if site is in prd environment
if [ -z "$ENV" ]
then
        ENV=prd
fi

echo "Site environment: $ENV"

# BUILD ENV PATH
ENVPATH="/export/$ENV/virtual/"

#for testing:
#ENVPATH="/export/prd/backups/archive-dump/20190307152239"

# CHECK IF DOCROOT EXISTS
EXIST=$(find "$ENVPATH" -maxdepth 1 -name "$SITE")

# if docroot dne, exit program
if [ -z "$EXIST" ]
then
         echo "ERROR: Site docroot DOES NOT EXIST"
         exit 1
else
         echo "Site docroot: "$EXIST""
fi

# GET BACKUP DIRECTORY
BACKUPDIR="/export/"$ENV"/backups/"$SITE""

# GET SQL DATABASE and SERVER FROM local.setting.php
DBSERVER=$(cat "$EXIST"/sites/default/local.settings.php | grep -Po '(db\d*|mysql)(\.|-)(dev|stg|prd|fail)\.cws\.(gabdcn|dpdcn)\.unt\.edu')

if [ -z ${DBSERVER} ]
then
  echo "Could not retrieve database server from local.settings.php"
  exit 1
else
  echo "Site database server: "$DBSERVER""
fi

 # mysql u & p
 USER=root
 PASS=m@n1c077i

echo
