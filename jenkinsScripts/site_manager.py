import logging
import argparse
import sys
import os
import datetime
import re
import glob
import tarfile

import utilities
import sqlTools
import siteTools



def restore_site(site_variables, target, date, flex):
    if date:
        site_backup_path = utilities.get_backup_by_date(site_variables['name'], target, date, flex)
        if site_backup_path:
            logging.debug(' --> Backup Path: {}'.format(site_backup_path))
        else:
            logging.error(' --> No backup found')
            return False
    else:
        site_backup_path = utilities.get_latest_backup(site_variables['name'], target)
        if site_backup_path:
            logging.debug(' --> Backup Path: {}'.format(site_backup_path))
        else:
            logging.error(' --> No backup found')
            return False

    if not siteTools.restore(site_variables, site_backup_path):
        return False
    else:
        return True

def restore_database(site_variables, target, date, flex):
    if date:
        db_backup_path = utilities.get_backup_by_date(site_variables['name'], target, date, flex)
        if db_backup_path:
            logging.debug(' --> Backup Path: {}'.format(db_backup_path))
        else:
            logging.error(' --> No backup found')
            return False
    else:
        db_backup_path = utilities.get_latest_backup(site_variables['name'], target)
        if db_backup_path:
            logging.debug(' --> Backup Path: {}'.format(db_backup_path))
        else:
            logging.error(' --> No backup found')
            return False

    if not sqlTools.restore(site_variables, db_backup_path):
        return False
    else:
        return True

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Overwrite a destination site with a source ")

    parser.add_argument('-t', '--target', help='Site or database?')
    parser.add_argument('-a', '--action', help='Action to perform')
    parser.add_argument('-s', '--source', help='The source url')
    parser.add_argument('-d', '--date', help='Date to restore to')
    parser.add_argument('-f', '--flex', action='store_true', help='Look for dates + or - one day of the date provided')
    parser.add_argument('-o', '--overwrite', help='The target url in an overwrite')
    parser.add_argument('-b', '--backup', action='store_true', help='Backup database before overwriting')



    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    #  get source site variables
    source_site_variables = utilities.get_site_variables(args.source)

    logging.info('\n')
    logging.info(' --> Source Site Name: {}'.format(source_site_variables['name']))
    logging.info(' --> Source Site Docroot: {}'.format(source_site_variables['docroot']))
    logging.info(' --> Source Database Server: {}'.format(source_site_variables['server']))
    logging.info(' --> Source Database Name: {}'.format(source_site_variables['database']))

    if args.date:
        logging.debug('DATE: {}'.format(args.date))
    else:
        logging.debug(' --> No date variable present')

    if args.target == 'Site':
        if args.action == 'Backup':
            logging.info('\n')
            logging.info(' ===== BACKING UP SITE =====')
            if not siteTools.backup(source_site_variables):
                logging.info('\n')
                logging.info(' --> Unable to backup site')
                sys.exit(1)
        if args.action == 'Restore':
            logging.info('\n')
            logging.info(' ===== RESTORING SITE =====')
            if not restore_site(source_site_variables, args.target, args.date, args.flex):
                logging.info('\n')
                logging.info(' --> Unable to restore site')
                sys.exit(1)
    if args.target == 'Database':
        if args.action == 'Download':
            logging.info('\n')
            logging.info(' ===== DOWNLOADING DATABASE TO JENKINS WORKSPACE =====')
            if not sqlTools.download(source_site_variables):
                logging.info('\n')
                logging.info(' --> Unable to download database')
                sys.exit(1)
        if args.action == 'Backup':
            logging.info('\n')
            logging.info(' ===== BACKING UP DATABASE =====')
            if not sqlTools.backup(source_site_variables):
                logging.info('\n')
                logging.info(' --> Unable to backup database')
                sys.exit(1)
        if args.action == 'Restore':
            logging.info('\n')
            logging.info(' ===== RESTORING DATABASE =====')
            if not restore_database(source_site_variables, args.target, args.date, args.flex):
                logging.info('\n')
                logging.info(' --> Unable to restore database')
                sys.exit(1)
        if args.action == 'Overwrite':
            logging.info('\n')
            logging.info(' ===== OVERWRITING {} DATABASE WITH {} ====='.format(args.overwrite, args.source))
            #  get target site variables
            target_site_variables = utilities.get_site_variables(args.overwrite)
            #  overwrite database
            if not sqlTools.overwrite(source_site_variables, target_site_variables, args.backup):
                logging.info('\n')
                logging.info(' --> Unable to overwrite database')
                sys.exit(1)
