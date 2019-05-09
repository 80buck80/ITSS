import logging
import argparse
import sys
import os
import time
import glob
from datetime import datetime
import tarfile
import re
import shutil

from shell import cmd
from config import conf
import utilities
import sqlTools

'''
Functions to backup, restore a site, and rsync between two sites
'''

#  backup a sites docroot and database
def backup(site_variables):
    logging.debug(' --> siteTools.py : backup({})'.format(site_variables))

    #  PREP SQL BACK UP FOR TARRING
    #  get sql backup
    if not sqlTools.backup(site_variables):
        logging.info('\n')
        logging.info(' --> Unable to get sql backup')
        return False

    #  get sql backup path
    sqlBackupPath = utilities.get_latest_backup(site_variables['name'], 'Database')
    if not sqlBackupPath:
        logging.info('\n')
        logging.info(' --> No sql backup exists')
        return False

    #  move sql dump into site docroot to be tarred
    os.rename(sqlBackupPath, '{}/{}'.format(site_variables['docroot'], os.path.basename(sqlBackupPath)))

    #  PREP TAR FILE
    #  format date for tar file name
    date = datetime.now().strftime("%Y%m%d_%H%M%S")
    #  get backup directory
    backup_directory = utilities.get_backup_directory(site_variables['name'])
    #  create tar file path
    tarFile = os.path.join(backup_directory, '{}.{}.{}'.format(utilities.clean(site_variables['name']), date, 'tar.gz'))
    logging.debug(' --> Tar Path: {}'.format(tarFile))

    #  BACK UP SITE
    logging.debug('\n')
    logging.debug(' --> Backing up {}...'.format(site_variables['name']))
    with tarfile.open(tarFile, "w:gz") as tar:
        #  add site docroot to tar
        tar.add(site_variables['docroot'], arcname=os.path.basename(site_variables['docroot']))

    #  CLEAN UP
    # remove sql dump file from site docroot
    os.remove(os.path.join(site_variables['docroot'], os.path.basename(sqlBackupPath)))
    #  confirm sql dump was removed from docroot
    if os.path.exists(os.path.join(site_variables['docroot'], os.path.basename(sqlBackupPath))):
        logging.debug('\n')
        logging.debug('WARNING: Failed to remove sql dump from docroot')
    else:
        logging.debug('\n')
        logging.debug(' --> Sql dump removed from docroot')

    #  confirm tar file creation
    if os.path.exists(tarFile):
        logging.info('\n')
        logging.info(' --> Site backed up to: {}'.format(tarFile))
        return True
    else:
        logging.info('\n')
        logging.info('ERROR: Failed to backup site')
        return False

#  overwrite target site docroot with source docroot
def rsync(source_variables, target_variables, delete):
    logging.debug(' --> siteTools.py : rsync({}, {}, {})'.format(source_variables, target_variables, delete))

    #  exclude local.settings.php from the rsync
    if os.path.isfile("{}/sites/default/local.settings.php".format(
            target_variables['docroot'])):
        settings = ("local.settings.php")
    else:
        settings = ("settings.php")

    #  create rsync command
    if delete:
        cmd_text = ("rsync -qaz --delete --exclude={2} --delete {0}/ {1}".format(source_variables['docroot'], target_variables['docroot'], settings))
    else:
        cmd_text = ("rsync -qaz --exclude={2} {0}/ {1}".format(source_variables['docroot'], target_variables['docroot'], settings))

    logging.debug('\n')
    logging.debug(" --> Rsyncing from {} to {}...".format(source_variables['name'], target_variables['name']))

    #  sync dat suckah
    logging.info('\n')
    logging.info(' --> Performing rsync...')
    success, out, err = cmd(cmd_text)
    if not success:
        if err:
            logging.info('\n')
            logging.error(" --> Failed rsync: {0} \n {1}".format(err, out))
            return False
        else:
            logging.info('\n')
            logging.error(" --> Failed\nReason: other")
            return False
    else:
        #  reset site permissions
        if not utilities.reset_permissions(target_variables):
            logging.info('\n')
            logging.info(' --> Failed to reset permissions on site docroot')

        logging.info('\n')
        logging.info(" --> Rsync success")
        return True



#  restore a site from the backup path argument
def restore(site_variables, backup_path):
    logging.debug(' --> siteTools.py : restore({}, {})'.format(site_variables, backup_path))

    logging.info('\n')
    logging.info(' --> Restoring site from {}'.format(backup_path))

    #  untar the backup file
    with tarfile.open(backup_path) as tar:
        tar.extractall(path=os.path.dirname(backup_path))

    #  get path to untarred file
    site_restore_from = os.path.join(os.path.dirname(backup_path), utilities.clean(site_variables['name']))
    logging.debug(' --> Site Restore From: {}'.format(site_restore_from))

    #  build path for sql restore
    for root, directory, files in os.walk(site_restore_from):
        for file in files:
            match = re.search(r"[0-9]*_[0-9]*\.sql", file)
            if match:
                db_restore_from = os.path.join(site_restore_from, file)
                logging.debug(' --> DB Restore From {}:'.format(db_restore_from))
                break

    #  restore database
    if not sqlTools.restore(site_variables, db_restore_from):
        logging.info('\n')
        logging.info(" --> Database unable to be restored")
        return False

    #  remove sql file from site docroot
    os.remove(db_restore_from)

    #  construct dictionarys for rsync fx
    #  we do this to keep consistancy with other scrips calling the rsync fx
    backup_source_variables = {
        'name' : site_variables['name'],
        'docroot' : site_restore_from
    }

    if not rsync(backup_source_variables, site_variables, True):
                logging.info('\n')
                logging.info(" --> Rsync was not successfull")
                return False

    #  remove backup directory
    try:
        shutil.rmtree(site_restore_from)
    except OSError as e:
        logging.error(" --> Error: %s - %s." % (e.filename, e.strerror))

    return True
