import sys
import os
import yaml
import git
import logging
import re
from jinja2 import *

jinjaEnv = Environment(loader = FileSystemLoader('templates'))

def path_check(from_url):

    ####################################################
    #  Checks if argv[1] has a path with the domain name
    #  If it does, from_url is spit and returned as
    # 'domain' and 'path'
    #
    #  Return:
    #   -  domain and regex for conf file or
    #   -  domain and regex appended to the path for conf file
    #
    #  Function Argument:
    #   - from_url = argv[1]
    ####################################################

    #  SPLIT FROM_URL STRING ONCE BY '/'
    split_url = from_url.split('/', 1)

    #  IF LENGTH IS 1, THERE IS NO PATH
    #  ELSE, THERE IS A PATH
    if len(split_url) == 1:
        return split_url[0], '(.*)', False
    else:
        return split_url[0], split_url[1] + '(.*)', True

def search_redirect_confs(domain):

    ###################################################################
    #  Searches redirects.conf files to match argument
    #
    #  Return:
    #   - False, file_name, domain, and path if no match is found
    #   - True, file_name, domain, and path if match is found
    #
    #  Function Argument:
    #   - domain = to_domain
    #
    ###################################################################

    #  GET LIST OF REDIRECT.CONF FILES
    files = os.listdir("site-inventory/redirects")

    #  REPLACE '.' WITH '_' TO CHECK FOR UNDERSCORES IN THE FILE NAME
    swap_for_underscore = domain.replace(".", "_")

    #  APPEND '.redirects.conf' TO FROM _URL
    file_name = "{0}{1}".format(swap_for_underscore, ".redirects.conf")

    #  LOOK FOR FILE NAME WITH '_'
    if file_name in files:                                                      #
        logging.info(file_name + ' file found')
        return True, file_name

    #  LOOK FOR FILE NAME WITH '.'
    else:
        file_name = "{0}{1}".format(domain, ".redirects.conf")

        if file_name in files:
            logging.info(file_name + ' file found')
            return True, file_name

        else:
            logging.info(file_name + ' file NOT found')
            return False, file_name

def add_redirect(conf_file, domain, path, to_url):

    ####################################################
    #  Creates a <domain>.redirects.conf file and writes
    #  to it a jinja template that defines apache rewrite
    #  rules
    #
    #  Function Argument:
    #   - type = specifies site or alias
    #   - conf_file = redirects.conf file to modify (could be from or to domains)
    #   - domain = the <domain>.redirect.conf file to modify
    #   - path = the path from argv[1] if present
    #   - to_url = argv[1] or argv[2]
    ####################################################

    #  rules STORES LIST OF RULES FROM CONF FILE
    rules = []

    #  SEARCH FOR <domain>.redirects.conf FILE
    found, file_name = search_redirect_confs(conf_file)

    #  CREATE PATH TO SAVE THE FILE TO
    file_path = "{0}{1}".format("site-inventory/redirects/", file_name)

    #  IF CONF FILE IS FOUND READ REDIRECT RULES INTO LIST
    #  ELSE, SITE REIDRECTS = TRUE INS INVENTORY
    if found:
        with open(file_path) as file:
            rules = file.readlines()
    else:
        logging.info('Creating ' + file_name)
        set_site_redirects(conf_file, True)

    #  REPLACE '.' with '\.' FOR APACHE FORMATTING
    domain = domain.replace('.', '\.')
    logging.info('Creating redirect with rewrite rule')

    #  USE JINJA TEMPLATE TO CREATE REDIRECT RULE
    template = jinjaEnv.get_template('redirects.j2')
    render = template.render(from_domain = domain, from_path = path, to = to_url)

    #  IF REDIRECT IS A 'CATCH-ALL', APPEND THE RULE TO THE END OF THE LIST
    #  ELSE, PREPEND THE RULE TO THE LIST
    if path == '(.*)':
        rules.append(render)
    else:
        rules.insert(0, render)

    #  OPEN THE FILE AND WRITE RULES TO IT
    logging.info('Writing redirect to ' + file_name)
    f = open(file_path, 'w')
    for line in rules:
        f.write(line)
    f.close()

def search_for_redirect(conf_file, domain, path, to_url):

    ####################################################
    #  Search for RewriteConditions and RewriteRules
    #  in a <domain>.redirect.conf file
    #
    #  RETURN:
    #   - T/F that the redirect was found in the file
    #   - The file path where the rediret lives
    #   - The jinja template used to find the redirect
    #
    #  Function Argument:
    #   - conf_file = redirects.conf file to find
    #   - domain = redirecting from domain
    #   - path = path of redirecting from if present
    #   - to_url = redirecting to domain and path
    ####################################################

    #  LOOK FOR <DOMAIN>.REDIRECT.CONF FILE
    found, file_name = search_redirect_confs(conf_file)

    #  CREATE FILE PATH IF FOUND, RETURN IF NOT
    if found:
        file_path = "{0}{1}".format("site-inventory/redirects/", file_name)
    else:
        return False, "", ""

    #  GET ALL DATA FROM REDIRECT.CONF FILE
    with open(file_path) as file:
          data = file.read()

    #  CRATE JINJA TEMPLATE TO USE FOR SEARCH
    domain = from_domain.replace('.', '\.')
    template = jinjaEnv.get_template('redirects.j2')
    match = template.render(from_domain = domain, from_path = path, to = to_url)

    #  PARSE FILE DATA TO COMPARE WITH TEMPLATE
    if match in data:
        logging.info('Redirect Rule found in ' + file_name)
        return True, file_path, match
    else:
        logging.info('Redirect Rule NOT found in ' + file_name)
        return False, file_path, match

def remove_redirect(conf_file, domain, path, to_url):

    ####################################################
    #  Removes RewriteConditions and RewriteRules
    #  from a <domain>.redirect.conf file
    #
    #  RETURN:
    #   - T if rewrite removed
    #   - F if not found
    #
    #  Function Argument:
    #   - conf_file = redirects.conf file to find
    #   - domain = redirecting from domain
    #   - path = path of redirecting from if present
    #   - to_url = redirecting to domain and path
    ####################################################

    #  SEARCH FOR REDIRECT RULE IN CONFS FILE - MATCH = RULE IF FOUND
    found, file_path, match = search_for_redirect(conf_file, domain, path, to_url)

    #  IF FOUND, REMOVE RULES FROM REDIRECT.CONF FILE
    if found:
        with open(file_path) as file:
              data = file.read()

        modified_data = data.replace(match, '')

        with open(file_path, 'w+') as file:
            file.write(modified_data)

        return True
    else:
        return False

def set_site_redirects(site, setting):

    ####################################################
    #  Sets the 'redirects' key of a site in inventory to
    #  true or false
    #  Returns:
    #
    #  Function Argument:
    #   - site = site to change
    #   - setting = 1 or 0
    ####################################################

    #  GET A LIST OF SITES AND THE FULL INVENTORY
    sites, inventory = getSites()

    # IF setting = TRUE, SET REDIRECT TO TRUE
    # ELSE, SET REDIRECT TO FALSE
    if setting:
        logging.info('Setting site\'s redirects value to True in inventory')
        inventory['sites'][site]['redirects'] = True
    else:
        logging.info('Setting site\'s redirects value to False in inventory')
        inventory['sites'][site]['redirects'] = False

    #  WRITE CHANGES TO MASTER-SITES.YML
    with open("site-inventory/master-sites.yml", "w") as f:
        try:
            yaml.dump(inventory, f, default_flow_style=False)
        except Exception as e:
            logging.error("Could not write changes to file: %s" % e)
            sys.exit(1)

def search_site_inventory(domain):

    ####################################################
    #  Searches the master-sites.yml file for the domain
    #  argument to see if it exists. We then check if the
    #  domain argument is a site or an alias for another
    #  site
    #
    #  Returns:
    #       - True, True, False: the domain exists, is a site, and not a type: redirect
    #       - True, True, True: the domain exists, is a site, and is a type: redirect
    #       - True, False, False: the domain exists, is an alias, and is not a type: redirect
    #       - False, False, False: the domain does not exist at all
    #       - site = site conf file that will be modified
    #
    #  Function Argument:
    #   - domain = either argv[1] or argv[2]
    #
    ####################################################

    #  GET A LIST OF SITES AND THE FULL INVENTORY
    sites, inventory = getSites()

    #  SEARCH FOR DOMAIN IN INVENTORY
    for site in sites:
        if domain == site:
            if inventory['sites'][site]['type'] == "redirect":
                return True, True, True, site
            else:
                return True, True, False, site
        elif inventory['sites'][site]['aliases']:
            if domain in inventory['sites'][site]['aliases']:
                return True, False, False, site

    #  RETURNS HERE IF NOTHING MATCHES
    return False, False, False, "DNE"

def getInventoryRepo():

    ####################################################
    #  Clones the site-inventory repo to the Jenkins workspace
    #  if it is not already present
    #
    #  Returns:
    #       - the site-inventory repo
    #
    ####################################################

    logging.info('Retrieving site inventory')

    #  IF SITE-INVENTORY DIRECTORY DOES NOT EXIST, CLONE THE REPO
    if not os.path.isdir('site-inventory'):
        git.Repo.clone_from('git@git.untsystem.edu:cws/site-inventory.git', 'site-inventory')

    #  PULL THE REMOTE REPO
    repo = git.Repo('site-inventory')
    repo.git.pull()

    return repo

def addCommitPush(repo, action):

    ####################################################
    #  Adds commits and pushes changes to the remote
    #  site-inventory repo
    #
    #  Arguments:
    #   - repo: the modfied site-inventory repo
    #   - action: True = Redirect added. False = Redirect removed
    ####################################################

    #  ADD FILES TO STAGIN AREA
    logging.info('Adding files to Stagng area...')
    repo.git.add('-A')
    logging.info('Committing changes...')

    #  COMMIT TO LOCAL REPO
    if action:
        repo.git.commit('-m', 'Added redirect from ' + sys.argv[1] + ' to ' + sys.argv[2])
    else:
        repo.git.commit('-m', 'Removed redirect from ' + sys.argv[1] + ' to ' + sys.argv[2])

    # PUSH TO REMOTE REPO
    logging.info('Pushing to repo...')
    repo.git.push()

def getSites():

    ####################################################
    #  Reads site inventory into to a list and dictionary
    #
    #  Returns:
    #   - names: list of site names
    #    - inventory: entire inventory in yaml format
    ####################################################

    names = []

    with open("site-inventory/master-sites.yml", "r") as stream:
        inventory = yaml.load(stream)
        for name in inventory.get("sites", {}):
            names.append(name)

    return names, inventory


if __name__ == '__main__':

    #  CREATE LOGGER
    logging.basicConfig(format='[%(levelname)s][%(asctime)s]: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG)

    #  GET INVENTORY REPO
    inventoryRepo = getInventoryRepo()

    #  REMOVE TRAILING '/' FROM ARGVs IF PRESENT
    clean_argv1 = sys.argv[1].rstrip('/')
    clean_argv2 = sys.argv[2].rstrip('/')

    #  SPLIT DOMAINS FROM PATHS
    from_domain, from_path, from_has_path = path_check(clean_argv1)

    to_domain, to_path, to_has_path = path_check(clean_argv2)

    #  CHECK IF FROM_DOMAIN EXISTS AS A SITE OR ALIAS
    #  AND GET THE CONF FILE NAME IF FOUND
    from_exists, from_is_site, type_is_redirect, conf_file = search_site_inventory(from_domain)

    #  ADDING A REDIRECT
    if sys.argv[3] == 'add':

        logging.debug('Action = add')

        #  CHECK IF FROM_DOMAIN EXISTS
        if from_exists:

            #  CHECK IF FROM_DOMAIN IS A SITE
            if from_is_site and not type_is_redirect:
                if from_has_path:
                    logging.info(from_domain + ' exists as a site and has a path')
                    logging.error('This redirect can be done using the Drupal Redirect module')
                    sys.exit(1)
                else:
                    logging.info(from_domain + ' exists as a site')
            elif from_is_site and type_is_redirect:
                logging.info(from_domain + ' exists as a redirect site')
            #  FROM_DOMAIN IS AN ALIAS
            else:
                logging.info(from_domain + ' exists as an alias')

            #  ADD REDIRECT RULE
            add_redirect(conf_file, from_domain, from_path, clean_argv2)

            #  ADD, COMMIT, AND PUSH CHANGES TO SITE-INVENTORY REPO
            addCommitPush(inventoryRepo, True)

        #  FROM_DOMAIN DOES NOT EXIST
        else:
            logging.error(from_domain + ' does not exist - Can not create redirect from a site or alias that does not exist')
            sys.exit(1)

    #  REMOVING A REDIRECT
    if sys.argv[3] == 'remove':

        logging.debug('Action = remove')

        #  FROM_DOMAIN IS A SITE
        if from_is_site and not type_is_redirect:
            if from_has_path:
                logging.info(from_domain + ' exists as a site and has a path')
                logging.error('This redirect can be removed using the Drupal Redirect module')
                sys.exit(1)
            else:
                #  REMOVE A REDIRECT FROM CONF FILE
                logging.info('Removing redirect...')
                removed = remove_redirect(from_domain, from_domain, from_path, clean_argv2)

        #  FROM_DOMAIN IS AN ALIAS
        else:
            #  REMOVE A REDIRECT FROM CONF FILE
            logging.info('Removing redirect...')
            removed = remove_redirect(conf_file, from_domain, from_path, clean_argv2)

        #  IF REDIRECT RULE REMOVED, PUSH CHANGES TO GIT REPO
        #  ELSE, EXIT SCRIPT
        if removed:
            #  ADD, COMMIT, AND PUSH CHANGES TO SITE-INVENTORY REPO
            logging.info("Redirect removed, pushing changes to inventory")
            addCommitPush(inventoryRepo, False)
        else:
            logging.info('Redirect rules not found')
            logging.error('Redirect was unable to be removed')
            sys.exit(1)
