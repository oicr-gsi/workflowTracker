"""
   This package is for handling requests to github repo.
   it should initialize and respond to different requests
"""
import re
from dataclasses import dataclass
import subprocess
import json
import base64

@dataclass
class githubRepo:
    organization: str
    token: str
    max_repos: int = 1000

    """ Return shortest, prefix-free name for a workflow """
    @staticmethod
    def get_raw_name(names: list, settings: dict) -> str:
        raw_name = min((word for word in names if word), key=len)
        if 'prefixes' in settings.keys():
            for prx in settings['prefixes'].values():
                raw_name = raw_name.replace(prx, "")
                raw_name = raw_name.rstrip("_")
        return raw_name.lower()

    """ Format curl command """
    def get_curl_command(self, request: str, req_type="repos") -> str:
        curl_cmd = f'curl -L \
        -H "Accept: application/vnd.github+json" \
        -H "Authorization: Bearer {self.token}" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        https://api.github.com/{req_type}/{self.organization}/{request}'
        return curl_cmd

    """ Get a simple dict keyed by repo name with urls """
    def get_repo_list(self) -> dict:
        repos = {}
        for i in range(1, int(self.max_repos/100)):
            repo_request = self.get_curl_command(f'repos?page={i}\&per_page=100', "orgs")
            rp_string = subprocess.check_output(repo_request, shell=True).decode().strip()
            rp_data = json.loads(rp_string)
            if len(rp_data) < 1 or not isinstance(rp_data, list):
                break

            for rw in rp_data:
                if isinstance(rw, dict) and 'name' in rw.keys() and 'html_url' in rw.keys():
                    repos[rw['name']] = rw['html_url']
        return repos

    """ Get file content as an array of strings """
    def get_file_content(self, workflow_repo: str, file: str) -> bytes | None:
        file_request = self.get_curl_command(f'{workflow_repo}/contents/{file}')
        f_string = subprocess.check_output(file_request, shell=True).decode().strip()
        f_data = json.loads(f_string)
        if 'content' in f_data.keys():
            return base64.b64decode(f_data["content"])
        else:
            return None

    """ Get all tags from a Repository """
    def get_repo_tags(self, workflow_repo: str) -> list:
        tags_request = self.get_curl_command(f'{workflow_repo}/tags')
        t_string = subprocess.check_output(tags_request, shell=True).decode().strip()
        t_data = json.loads(t_string)
        tags = []
        for t in t_data:
            if isinstance(t, dict) and 'name' in t.keys():
                tag_check = re.search("\d+\.\d+\.\d+", t['name'])
                if tag_check is not None:
                    tags.append(t['name'])
        return tags

    """ Get the latest tag from a Repository, be aware of possible letters at the end """
    def get_latest_tag(self, workflow_repo: str) -> str | None:
        tags = self.get_repo_tags(workflow_repo)
        if len(tags) > 0:
            latest = ['0', '0', '0']
            for t in tags:
                nums = t.split(".")
                try:
                    res = [int(latest[x]) - int(nums[x]) for x in range(0, len(latest))]
                except ValueError:
                    print("WARNING: We do not compare tags containing letters")
                    res = [0, 0, 0]
                for check in res:
                    if check == 0:
                        continue
                    elif check < 0:
                        latest = nums
                        break
                    else:
                        break
            return ".".join(latest)
        else:
            return None

    """ 
       Function for making a data for matching workflows to repos, calls a couple of functions and writes to dict
       This implementation returns a dict keyed with rawName (short name of the workflow stripped of all prefixes)
    """
    def get_cross_match_data(self, settings: dict, cross_matches: dict):
        repo_list = self.get_repo_list()
        if isinstance(repo_list, dict):
            for repo in repo_list.keys():
                try:
                    wf_data = self.get_file_content(repo, "vidarrbuild.json")
                    if wf_data is not None:
                        wf_info = json.loads(wf_data)
                        cross_matches[self.get_raw_name(wf_info['names'], settings)] = {'repo': repo_list[repo],
                                                                                        'wdl':  wf_info['wdl']}
                except:
                    print(f'Failed to retrieve data for repo {repo}')

