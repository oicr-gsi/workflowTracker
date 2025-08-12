"""
   This script relies on settings in config.toml file
   * extract the list of workflows (vidarr .gsiWorkflow files)
   * extract all gsiOlive files, parse them to extract wf names, their versions and modules
   * find all wf repos, if missing - construct from a gsiWorkflow name
   * bring all info together and format into HTML or tsv. Also, dump a json file
"""
import collections
import tomli
import argparse
import json
import os
from git import Git
import gsiWorkflow
import gsiOlive
import gsiRepository as rP
import htmlRenderer

settings = {}

"""
     We operate with Workflow entries, which are dataclasses
     
     Research Tag(s): [],
     Clinical Tag(s): []
     Latest Tag:
     Repo:
     Research Olives: []
     Clinical Olives: []
     Code Modules: []
     Data Modules: []
"""

"""
   Load settings file and return a dict with obtained values
"""
def load_config(path):
    try:
        with open(path, "rb") as f:
            toml_dict = tomli.load(f)
            print("Loaded configuration file")
    except tomli.TOMLDecodeError:
        print("Failed to load settings, invalid format")
    return toml_dict

"""
   update local copy of the repo, cd in it checkout main branch and pull
"""
def update_source(path: str, main_branch: str):
    try:
        g = Git(path)
        g.checkout(main_branch)
        g.pull()
    except:
        print("failed to update sources")

"""
    From the list of names, pick the shortest and strip it of all known prefixes
    also check if we have all lowercase name (if camelCase name found)
"""
def get_raw_name(names: list, to_match: list):
    for name in names:
        if 'prefixes' in settings.keys():
            for prx in settings['prefixes'].values():
                raw_name = name.removesuffix(prx)
                raw_name = raw_name.rstrip("_")
                if raw_name.lower() in to_match:
                    return raw_name.lower()
                elif raw_name in to_match:
                    return raw_name
    return None

"""
    Join metadata from olives with gsiWorkflow-derived information, return hash
"""
def join_metadata(olive_data: dict, repo_data: dict, wf: str) -> dict:
    """ Join instance-specific modules with wdl-derived modules, keep things unique """
    merged_data = {}
    d_modules = set()
    c_modules = set()
    try:
        for inst in (settings['instances'].values()):
            if inst in olive_info[wf].keys():
                vetted_olives = [os.path.basename(o) for o in olive_info[wf][inst]['olives']]
                d_modules = olive_data[inst]['data_modules'].union(repo_data['data_modules'])
                c_modules = olive_data[inst]['code_modules'].union(repo_data['code_modules'])
                merged_data[inst] = {'olives': vetted_olives,
                                     'tags': list(olive_data[inst]['tags'])}
        merged_data['latest_tag'] = repo_data['latest_tag']
        merged_data['url'] = repo_data['url']
        merged_data['data_modules'] = list(d_modules)
        merged_data['code_modules'] = list(c_modules)
    except:
        print(f'ERROR: Failed to merge gsiOlive and repo data for {wf}')

    return merged_data

""" 
   ====================== Main entrance point to the script =============================
   pass (or not) the following:
   -s settings: path to the TOML file with all settings
   -o output json file
   -p output HTML page 
   
   we have defaults for everything
   at the end, script prints out data as a table and dumps data in a json
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run parsing script to generate gsiWorkflow status table')
    parser.add_argument('-s', '--settings', help='Settings file in TOML format', required=False, default="config.toml")
    parser.add_argument('-o', '--output-json', help='Output json', required=False, default="gsi_workflows.json")
    parser.add_argument('-p', '--output-page', help='Output page, HTML', required=False, default="gsi_workflows.html")
    args = parser.parse_args()

    settings_path = args.settings
    output_json = args.output_json
    output_page = args.output_page
    ''' A. Load settings and Update local copy of the repo'''
    settings = load_config(settings_path)
    try:
        update_source(settings["repo"]["local_olive_dir"], settings["repo"]["main"])
    except:
        print("ERROR: Failed to update local repo copy from the web")

    ''' B. Load gsiWorkflow names from .vidarrworkflow files without prefixes into a dict keyed by instance '''
    instances = []
    wf_names = {}
    olive_files = {}
    if "instances" in settings.keys():
        for i in settings["instances"].keys():
            instances.append(settings["instances"][i])
        prefixes = []
        if "prefixes" in settings.keys():
            prefixes = settings['prefixes'].values()
        wf_names = gsiWorkflow.extract_wf_names(settings["repo"]["local_olive_dir"], instances, prefixes)
    else:
        print("ERROR: There are no instances to check, fix your settings")

    ''' C. collect and process olives, extract modules and tags '''
    olive_files = {}
    olive_info = {}
    if 'aliases' in settings.keys():
        olive_files = gsiOlive.collect_olives(settings["repo"]["local_olive_dir"], instances, settings['aliases'])
    else:
        olive_files = gsiOlive.collect_olives(settings["repo"]["local_olive_dir"], instances, {})
    olive_info = gsiOlive.extract_olive_info(olive_files, wf_names)

    vetted_data = {}
    ''' D. If configured, try getting list of repos from github (a dict keyed by gsiWorkflow name with no prefixes)'''
    if 'organization' in settings['repo'].keys() and 'token' in settings['repo'].keys():
        org = settings['repo']['organization']
        token = settings['repo']['token']
        myRepo = rP.githubRepo(org, token)
        repo_list = myRepo.get_repo_list()
        if len(repo_list) == 0:
            print("ERROR: Could not retrieve the list of repositories, check the queue and token are Ok")
        repo_info = {}
        ''' E. use repo list, load vidarrbuild.json and wdl and return a hash with names and modules '''
        for repo in repo_list.keys():
            print(f'Processing repository [{repo}]...')
            try:
                wf_data = myRepo.get_file_content(repo, "vidarrbuild.json")
                wf_info = json.loads(wf_data)
                wf_id = get_raw_name(wf_info['names'], olive_info.keys())
                if wf_id in olive_info.keys() and len(olive_info[wf_id]) != 0 or \
                   wf_id.lower() in olive_info.keys() and len(olive_info[wf_id.lower()]) != 0:
                    wf_wdl = myRepo.get_file_content(repo, wf_info['wdl'])
                    wf_wdl_lines = str(wf_wdl, encoding='utf-8').split("\n")
                    wf_latest = myRepo.get_latest_tag(repo)
                    wf_modules = gsiWorkflow.parse_workflow(repo, wf_wdl_lines)
                    repo_info[wf_id] = {'url': repo_list[repo],
                                        'latest_tag': wf_latest,
                                        'data_modules': wf_modules['data_modules'],
                                        'code_modules': wf_modules['code_modules']}
                else:
                    print(f'WARNING: Skipping [{repo}] as it is not currently in use...')
            except TypeError:
                print(f'WARNING: Repo [{repo}] Does not have information expected for a gsiWorkflow')
            except:
                print(f'ERROR: Collection of information for [{repo}] failed')

        if len(repo_info) == 0:
            print("ERROR: Information from gsiWorkflow repositories could not be collected")

        ''' F. Join two pieces of information, repo-derived info and gsiOlive-derived info '''
        for wf_id in olive_info.keys():
            if wf_id in repo_info.keys():
                vetted_data[wf_id] = join_metadata(olive_info[wf_id], repo_info[wf_id], wf_id)
            elif wf_id.lower() in repo_info.keys():
                vetted_data[wf_id] = join_metadata(olive_info[wf_id], repo_info[wf_id.lower()], wf_id)
            else:
                print(f'ERROR: Was not able to collect data for [{wf_id}]')
    else:
        print("ERROR: Repo credentials are not configured, no update from github is possible")

''' G. Dump the data into json file and generate a HTML page '''
if len(vetted_data) > 0:
    vetted_od = collections.OrderedDict(sorted(vetted_data.items()))
    with open(output_json, "w") as wfj:
        json.dump(vetted_od, wfj)

    html_page = htmlRenderer.convert2page(vetted_od)
    '''Return either HTML table or entire page'''
    with open(output_page, 'w') as op:
        op.write(html_page)
else:
    print("ERROR: Was not able to collect up-to-date information, examine this log and make changes")

"""
   ERROR: Was not able to collect data for [pbcmProjectMedipsPipe] - this is due to a repo being Private, not Public
   ERROR: Was not able to collect data for [providencePipeline] - this may be ignored
"""

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
