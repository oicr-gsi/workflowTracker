"""
   Functions for handling Olive data
"""
import glob
import os
import re
import subprocess
import gsiWorkflow

"""
   Find olives, return dict with lists of files
"""
@staticmethod
def collect_olives(repo_dir: str, instances_list: list, aliases: dict) -> dict:
    if repo_dir and os.path.isdir(repo_dir):
        olive_hash = {}
        for inst in instances_list:
            subdir = "/".join([repo_dir, "shesmu", inst])
            olive_files = glob.glob("/".join([subdir, "vidarr*.shesmu"]))
            if len(olive_files) == 0 and inst in aliases.keys():
                subdir = "/".join([repo_dir, "shesmu", aliases[inst]])
                olive_files = glob.glob("/".join([subdir, "vidarr*.shesmu"]))
            print(f'INFO: We have {len(olive_files)} .shesmu files for {inst}')
            if len(olive_files) > 0:
                olive_hash[inst] = []
            for oli in olive_files:
                olive_hash[inst].append(oli)
        return olive_hash
    else:
        return None


"""
   A simple subroutine for merging two hashes with Olive info
"""
@staticmethod
def merge_info(existing_hash: dict, new_hash: dict) -> dict:
    if len(existing_hash) != 0:
        new_hash['olives'].extend(existing_hash['olives'])
        new_hash['data_modules'] = new_hash['data_modules'].union(existing_hash['data_modules'])
        new_hash['code_modules'] = new_hash['code_modules'].union(existing_hash['code_modules'])
        new_hash['tags'] = new_hash['tags'].union(existing_hash['tags'])
    return new_hash



"""
   Extract modules and tags from olives matched to workflows, return only non-empty data for olives which are active
   We need to read Run lines to extract matching names, otherwise there is an issue with olives with names different
   from vidarr names.
"""
@staticmethod
def extract_olive_info(olive_files: dict, workflow_names: dict, aliases: dict) -> dict:
    olive_info = {}

    for instance in workflow_names.keys():
        if instance in olive_files.keys():
            olive_data = parse_olives(olive_files[instance])
        else:
            print(f'WARNING: There are no Olive files for instance [{instance}]')
            continue
        for wf in workflow_names[instance]:
            ''' Match with Olive, get a dict with wf tags and modules '''
            for oli in olive_data:
                if isinstance(oli, dict) and 'names' in oli.keys():
                    for name in oli['names']:
                        matched_name = re.search(wf, name)
                        if matched_name is not None:
                            if wf not in olive_info.keys():
                                olive_info[wf] = {}
                            olive_info[wf][instance] = merge_info(olive_info[wf][instance], oli) if instance in olive_info[wf].keys() else oli
                            break
            if wf not in olive_info.keys() or instance not in olive_info[wf].keys():
                print(f'WARNING: It was not possible to match instances for Workflow [{wf}]and Olive')

    return olive_info

"""
   Parse Olive: return a dict with modules and tags
   
   {
     olives = []
     tags = []
     data_modules = set
     code_modules = set
   }
"""
@staticmethod
def parse_olives(olive_files: list) -> dict:
    """ Return a list of Olive data structure(s) """
    parsed_olives = []
    ''' extract versions of the Workflow, names and modules'''
    for m_olive in olive_files:
        vetted_tags = []
        vetted_names = []
        try:
            run_lines = subprocess.check_output(f"grep 'Run ' '{m_olive}'", shell=True).decode().strip()
            run_lines = run_lines.split("\n")
            if not isinstance(run_lines, list):
                run_lines = [run_lines]
        except subprocess.CalledProcessError:
            print(f'WARNING: No Run lines in the Olive {m_olive}')
            run_lines = []

        for rl in run_lines:
            next_tag = re.search("v(\d+_\d+_*\d*\w*)$", rl)
            next_name = re.search("(\S+)_v\d+_\d+_*\d*\w*$", rl)
            if next_tag is not None:
                vetted_tags.append(next_tag.group(1).replace("_", "."))
            if next_name is not None:
                vetted_names.append(next_name.group(1))

        try:
            module_lines = subprocess.check_output(f"grep -i module '{m_olive}'", shell=True).decode().strip()
            module_lines = module_lines.split("\n")
            if not isinstance(module_lines, list):
                module_lines = [module_lines]
        except subprocess.CalledProcessError:
            print(f'WARNING: No Module lines in the Olive {m_olive}')
            module_lines = []
        module_list = gsiWorkflow.parse_module_strings(module_lines)
        parsed_olives.append({'olives': [m_olive],
                              'tags': set(vetted_tags),
                              'names': set(vetted_names),
                              'data_modules': set(module_list['data_modules']),
                              'code_modules': set(module_list['code_modules'])})
    if len(parsed_olives) > 0:
        return parsed_olives
    else:
        print(f'WARNING: Failed to process Olive Files')
        return None
