import logging
import argparse
import sys
import os

import utilities
import sqlTools
import siteTools


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Overwrite a destination site with a source ")

    parser.add_argument('-s', '--source', help='The source url')
    parser.add_argument('-t', '--target', help='The target url')
    parser.add_argument('-b', '--backup', action='store_true', help='Backup destination site')
    parser.add_argument('-m', '--mysql', action='store_true', help='Overwrite source database with destination')
    parser.add_argument('-r', '--rsync', action='store_true', help='Rsync source files to destination')
    parser.add_argument('-d', '--delete', action='store_true', help='Delete option for rsync')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    #  get source site variables
    source_site_variables = utilities.get_site_variables(args.source)

    logging.info('\n')
    logging.info(' --> Source Site Name: {}'.format(source_site_variables['name']))
    logging.info(' --> Source Site Docroot: {}'.format(source_site_variables['docroot']))
    logging.info(' --> Source Database Server: {}'.format(source_site_variables['server']))
    logging.info(' --> Source Database Name: {}'.format(source_site_variables['database']))

    #  get target site variables
    target_site_variables = utilities.get_site_variables(args.target)

    logging.info('\n')
    logging.info(' --> Target Site Name: {}'.format(target_site_variables['name']))
    logging.info(' --> Target Site Docroot: {}'.format(target_site_variables['docroot']))
    logging.info(' --> Target Database Server: {}'.format(target_site_variables['server']))
    logging.info(' --> Target Database Name: {}'.format(target_site_variables['database']))

    #  back up the target site before overwriting anything
    if args.backup:
        logging.info('\n')
        logging.info(" ===== BACKING UP TARGET SITE =====")
        if not siteTools.backup(target_site_variables):
            logging.info('\n')
            logging.info(' --> Unable to backup site')
            sys.exit(1)

    #  overwrite target database with source
    if args.mysql:
        logging.info('\n')
        logging.info(" ===== OVERWRITING TARGET DATABASE ===== ")
        if not sqlTools.overwrite(source_site_variables, target_site_variables, False):
            logging.info('\n')
            logging.info(' --> Unable to overwrite database')
            sys.exit(1)

    #  rsync source files to target
    if args.rsync:
        logging.info('\n')
        logging.info(" ===== RSYNCING SOURCE TO TARGET =====")
        if not siteTools.rsync(source_site_variables, target_site_variables, args.delete):
            logging.info('\n')
            logging.info(' --> Unable to sync sites')
            sys.exit(1)
