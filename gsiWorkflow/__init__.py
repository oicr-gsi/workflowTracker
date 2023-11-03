"""
   This is a package for handling Workflow instances.
   class Workflow holds names extracted from repo, modules extracted from wdl
   instance - independent
"""
import re
import os
import glob

"""
   Vet a Workflow path. extract basename, remove extension. Get rid of prefixes
"""
def _vet_wf_name(path: str, prefixes: list):
    base_name = os.path.basename(path)
    base_name = base_name.rstrip("vidarrworkflow")
    base_name = base_name.rstrip(".")
    for prf in prefixes:
        base_name = base_name.replace(prf, "")
        base_name = base_name.rstrip("_")
    return base_name


""" 
   Static method for getting Workflow names from .vidarrworkflow files
"""
def extract_wf_names(repo_dir: str, instances_list: list, prefixes: list):
    if repo_dir and os.path.isdir(repo_dir):
        wf_hash = {}
        for inst in instances_list:
            wf_names = []
            subdir = "/".join([repo_dir, "vidarr", inst, "workflows/"])
            wf_files = glob.glob("/".join([subdir, "*.vidarrworkflow"]))
            print(f'INFO: We have {len(wf_files)} vidarrworkflow files for {inst}')
            for wf in wf_files:
                wf_names.append(_vet_wf_name(wf, prefixes))
            if len(wf_names) > 0:
                wf_hash[inst] = set(wf_names)
        return wf_hash
    else:
        return None

"""
   Subroutine useful both for Olive and Workflow files, extract modules into a hash
"""
def parse_module_strings(m_strings: list):
    data_modules = []
    code_modules = []
    not_mods = re.compile('[$()|}{]')
    for m_string in m_strings:
        wf_check = re.search(":\s*\"(.+)\"", m_string)
        if wf_check is not None:
            next_mod_string = wf_check
        else:
            next_mod_string = re.search("\"(.+)\"", m_string)
        if next_mod_string is not None:
            modules = next_mod_string.group(1).split(" ")
            for mod in modules:
                vetted_mod = mod.replace("\"", "")
                if not_mods.search(vetted_mod) is None and re.search("/", vetted_mod) is not None:
                    if re.search("hg\d+|mm\d+|hs\d+", vetted_mod) is not None:
                        data_modules.append(vetted_mod)
                    else:
                        code_modules.append(vetted_mod)
    return {'data_modules': data_modules, 'code_modules': code_modules}


"""
   Parse Workflow wdl file (extract modules) 
"""
def parse_workflow(workflow: str, wf_lines: list):
    module_lines = []
    for w_line in wf_lines:
        next_mod_string = re.search("module.*", w_line)
        if next_mod_string is not None:
            if re.search("/", w_line) is not None:
                module_lines.append(w_line)
    if len(module_lines) == 0:
        print(f'WARNING: No module lines for {workflow}')
    return parse_module_strings(module_lines)

