#!/usr/bin/env python
import directory
import logging
import preflight
import argparse

logging.basicConfig(level=logging.INFO)

# CREATE A LIST OF SITE ENVIRONMENTS (<site>-dev, <site>-stg, <site>)
def buildSiteNames(site):

    siteGroups = []
    siteGroups.append(site)
    urlSplit = siteGroups[0].split(".")
    siteGroups.append('{}{}'.format(urlSplit[0], '-stg.unt.edu'))
    siteGroups.append('{}{}'.format(urlSplit[0], '-dev.unt.edu'))
    return siteGroups

# ADD OR REMOVE ADMINS TO SITE GROUPS
def manageSiteGroups(lc, action, admin, sites):
    if action == "Add":
        # add admin to prd, stg, and dev sites in AD
        for site in sites:
            if not directory.add_member_to_group(ldap_con=lc,
                                                 member=admin,
                                                 group="{}-admin".format(site)):
                logging.warning(" --> {} already exists in {}-admin".format(admin, site))

            else:
                logging.info(" --> {} added to {}-admin".format(admin, site))
    elif action == "Remove":
        # remove admin from prd, stg, and dev sites in AD
        for site in sites:
            if not directory.remove_member_from_group(ldap_con=lc,
                                                      member=admin,
                                                      group="{}-admin".format(site)):
                logging.warning(" --> {} does not exist in {}-admin".format(admin, site))
            else:
                logging.info(" --> {} removed from {}-admin".format(admin, site))

def manageWebadmin(lc, action, admin):
    if action == "Add":
        # add admin to prd, stg, and dev sites in AD
        if not directory.add_member_to_group(ldap_con=lc,
                                             member=admin,
                                             group="cws-webadmin-tool"):
            logging.warning(" --> {} already exists in cws-webadmin-tool".format(admin))
        else:
            logging.info(" --> {} added to cws-webadmin-tool".format(admin))
    elif action == "Remove":
        if not directory.remove_member_from_group(ldap_con=lc,
                                                  member=admin,
                                                  group="cws-webadmin-tool"):
            logging.warning(" --> {} does not exist in cws-webadmin-tool".format(admin))
        else:
            logging.info(" --> {} removed from cws-webadmin-tool".format(admin))

def manageGit(lc, action, admin):
    if action == "Add":
        # add admin to prd, stg, and dev sites in AD
        if not directory.add_member_to_group(ldap_con=lc,
                                             member=admin,
                                             group="cws-webusers-git"):
            logging.warning(" --> {} already exists in cws-webusers-git".format(admin))
        else:
            logging.info(" --> {} added to cws-webusers-git".format(admin))
    elif action == "Remove":
        if not directory.remove_member_from_group(ldap_con=lc,
                                                  member=admin,
                                                  group="cws-webusers-git"):
            logging.warning(" --> {} does not exist in cws-webusers-git".format(admin))
        else:
            logging.info(" --> {} removed from cws-webusers-git".format(admin))


# def adUtils(action, target, admin, site):
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--action', help='Add or Remove member from a group')
    parser.add_argument('-t', '--target', help='Groups to add or remove user from')
    parser.add_argument('-e', '--admin', help='Euid to add to groups')
    parser.add_argument('-s', '--site', help='Site group to add euid to')

    args = parser.parse_args()

    logging.info(' --> Action: {}'.format(args.action))
    logging.info(' --> Target: {}'.format(args.target))
    logging.info(' --> EUID: {}'.format(args.admin))
    logging.info(' --> Site: {}'.format(args.site))

    with directory.ldap_connection() as lc:

        # create list of sites (prd, stg, dev) if target is not webadmin groups
        if args.target != "Webadmin" and args.target != "Git":
            siteGroups = buildSiteNames(args.site)

        # adds euid to site groups, cws-webadmin-tool, and cws-webusers-git groups
        if args.target == "All":
            # add euid to site groups
            manageSiteGroups(lc, args.action, args.admin, siteGroups)
            manageWebadmin(lc, args.action, args.admin)
            manageGit(lc, args.action, args.admin)

        elif args.target == "Site":
            # add euid to site groups
            manageSiteGroups(lc, args.action, args.admin, siteGroups)

        elif args.target == "Webadmin":
            manageWebadmin(lc, args.action, args.admin)

        elif args.target == "Git":
            manageGit(lc, args.action, args.admin)
