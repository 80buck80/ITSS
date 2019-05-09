import logging
import argparse
import sys
import os
import time
import glob
from datetime import datetime

import utilities
from shell import cmd

'''
Functions to download, backup, restore, and overwrite site databases
'''

#  download an sql dump into Jenkins workspace directory
def download(site_variables):
    logging.debug(' --> sqlTools.py : download({})'.format(site_variables))

    #  configure time stamp for backup file name
    date = datetime.now().strftime("%Y%m%d_%H%M%S")
    #  constuct backup file name
    dumpName = '{}.{}.sql'.format(site_variables['database'], date)

    #  build shell command
    command = 'mysqldump -h {} -u{} -p{} --add-drop-database --databases {} > {}/{}'.format(site_variables['server'],
    site_variables['username'],
    site_variables['password'],
    site_variables['database'],
    os.getcwd(),
    dumpName)

    #  get sql dump
    logging.info('\n')
    logging.info(' --> Downloading database...')
    success, out, err = cmd(command)
    if not success:
        if err:
            logging.info('\n')
            logging.info("Failed sqldump: {0} \n {1}".format(err, out))
            return False
        else:
            logging.info('\n')
            logging.info("Failed\nReason: other")
            return False
    else:
        logging.info('\n')
        logging.info(' --> Database downloaded to Jenkins workspace')
        return True



#  get an sqldump from a sites database server
def backup(site_variables):
    logging.debug(' --> sqlTools.py : backup(site_variables)')

    #  get backup directory
    backup_directory = utilities.get_backup_directory(site_variables['name'])


    #  configure time stamp for backup file name
    date = datetime.now().strftime("%Y%m%d_%H%M%S")
    #  constuct backup file name
    dumpName = '{}.{}.sql'.format(site_variables['database'], date)

    #  build shell command
    command = 'mysqldump -h {} -u{} -p{} --add-drop-database --databases {} > {}/{}'.format(site_variables['server'],
    site_variables['username'],
    site_variables['password'],
    site_variables['database'],
    backup_directory,
    dumpName)

    #  get sql dump
    logging.info('\n')
    logging.info(' --> Backing up database for {}...'.format(site_variables['name']))
    success, out, err = cmd(command)
    if not success:
        if err:
            logging.info('\n')
            logging.info("Failed sqldump: {0} \n {1}".format(err, out))
            return False
        else:
            logging.info('\n')
            logging.info("Failed\nReason: other")
            return False
    else:
        logging.info('\n')
        logging.info(' --> Database backup created at: {}/{}'.format(backup_directory, dumpName))
        return True

#  resore a database with the backup path argument as a source
def restore(site_variables, backup_path):
    logging.debug(' --> sqlTools.py : restore({},{})'.format(site_variables, backup_path))


    #  construct sql command
    command = 'mysql -h {} -u{} -p{} {} < {}'.format(site_variables['server'],
                                                     site_variables['username'],
                                                     site_variables['password'],
                                                     site_variables['database'],
                                                     backup_path)
    #  restore the database
    logging.info('\n')
    logging.info(' --> Restoring database from {}'.format(backup_path))
    success, out, err = cmd(command)
    if not success:
        if err:
            logging.info('\n')
            logging.info("Failed sql restore: {0} \n {1}".format(err, out))
            return False
        else:
            logging.info('\n')
            logging.info("Failed\nReason: other")
            return False
    else:
        logging.info('\n')
        logging.info(' --> Database restored')

    #  use drush to update the overwritten database
    if not utilities.drush_updb(site_variables):
        logging.info('\n')
        logging.info(' --> Database not updated via Drush')

    #  use drush to clear site cache
    if not utilities.drush_cc_all(site_variables):
        logging.info('\n')
        logging.info(' --> Site cache not cleared via Drush')

    return True


#  overwrite the destination database with a source database
def overwrite(source_site_variables, dest_site_variables, backup_option):
    logging.debug(' --> sqlTools.py : overwrite({}, {})'.format(source_site_variables, dest_site_variables))


    #  backup destination database before overwriting
    if backup_option:
        logging.debug("\n")
        logging.debug(" --> Backing up destination database")
        if not backup(dest_site_variables):
            logging.info('\n')
            logging.info(' --> Destination database unable to be backed up')
            return False

    #  backup source database to use in overwrite
    logging.debug("\n")
    logging.debug(" --> Getting source database to use in overwrite")
    if not backup(source_site_variables):
        logging.info('\n')
        logging.info(' --> Source database unable to be backed up')
        return False

    #  get path to source sql dump
    logging.debug("\n")
    logging.debug(" --> Getting path to source sql dump")
    source_sql_dump = utilities.get_latest_backup(source_site_variables['name'], 'Database')
    if not source_sql_dump:
        logging.info('\n')
        logging.info(' --> Source database does not have a back up')
        return False

    #  use sed to change DROP DATABASE from source to destination
    command = 'sed -i "s/{}/{}/g" "{}"'.format(source_site_variables['database'],
                                                dest_site_variables['database'],
                                                source_sql_dump)

    success, out, err = cmd(command)
    if not success:
        if err:
            logging.info("\n")
            logging.info(" --> Failed to change DROP DATABASE name from source to destination: {0} \n {1}".format(err, out))
            return False
        else:
            logging.info("\n")
            logging.info(" --> Failed\nReason: other")
            return False
    else:
        logging.debug("\n")
        logging.debug(' --> Changed DROP DATABASE name from source to destination in sql dump')

    #  overwrite destination database with souce database
    logging.info('\n')
    logging.info(' --> Overwritting database...')
    command = 'mysql -h {} -u{} -p{} {} < {}'.format(dest_site_variables['server'],
                                                     dest_site_variables['username'],
                                                     dest_site_variables['password'],
                                                     dest_site_variables['database'],
                                                     source_sql_dump)

    success, out, err = cmd(command)
    if not success:
        if err:
            logging.info("\n")
            logging.info(" --> Failed sql overwrite: {0} \n {1}".format(err, out))
            return False
        else:
            logging.info("\n")
            logging.info(" --> Failed\nReason: other")
            return False
    else:
        logging.info("\n")
        logging.info(' --> Database overwritten')

    #  remove source sql dump file
    command = 'rm {}'.format(source_sql_dump)

    success, out, err = cmd(command)
    if not success:
        if err:
            logging.info(" --> Failed to remove source sql dump: {0} \n {1}".format(err, out))
            return False
        else:
            logging.info(" --> Failed\nReason: other")
            return False
    else:
        logging.debug("\n")
        logging.debug(' --> Removed source sql dump file')

    #  use drush to update the overwritten database
    if not utilities.drush_updb(dest_site_variables):
        logging.info('\n')
        logging.info(' --> Database not updated via Drush')

    #  use drush to clear site cache
    if not utilities.drush_cc_all(dest_site_variables):
        logging.info('\n')
        logging.info(' --> Site cache not cleared via Drush')

    return True
