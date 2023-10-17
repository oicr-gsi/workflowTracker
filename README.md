# workflowTracker

these scripts are for getting information from both Bitbucket analysis-config repository and
github repositories of our production workflows. THe aim is to run automatic updates and produce
reports in .json and .html formats. Developed in Python 3.10, these script will run using any of
3.10+ python modules available on GSI Univa cluster.

![HTML output](./table_screenshot.png)

# Installation

Designed to be modularized, workflowTacker should be used on Univa network-enabled nodes as a module
However, if you want to install it locally the first thing to do is 

'''
   pip install -r requirements.txt
'''

workflowTracker uses a few modules which are not a part of regular python installation.

# Captured Information

The main script calls variaous functions to bring together several pieces of information:

* workflow name (Workflow/Alias)
* RUO Tags (versions of workflows used)
* Clinical Tags
* Github Repo URL
* Data and Software (Code) modules used by a workflow
* RUO olives
* Clinical Olives

All of this information is organized in a Python dictionary and dumped as a .json

# Running the script

The script should be run as 

'''
  python3 workflow_tracker.py
'''

Following options are available:

* -s Settings file in TOML format (Default is config.toml)
* -o Output json, data dump       (Default is gsi_workflows.json)
* -p Output HTML page             (Default is gsi_workflows.html)

Settings file specify various configuration parameters and at this point has 4 sections:

* repo        - information related to repos for olives and workflows
* instances   - this is to specify our shesmu instances (clinical and research) - there may be changes in a future
* prefixes    - prefixes for resolving workflow names
* aliases     - similar to prefixes, but this is to address non-obvious name conventions (the most glaring example is bmpp)

Script will run collecting workflow names as they are featured in Vidarr, then it will proceed to collect olives and finally,
process workflows. After bringing all of these data together, the script will output .json and .html reports

# Authentication

It is important to have a working SSH key for communicating with Bitbucket and a token for communication with Github.
Generate your ssh key pair with 

'''
  ssh-keygen -t rsa
'''

and then use it with git:

'''
   export GIT_SSH_COMMAND="ssh -i ~/.ssh/keys/my_key"
   git clone ssh://git@bitbucket.oicr.on.ca/gsi/analysis-config.git   
'''

As for Github, the token should be generated according to the instruction on the [github website](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens). Token goes into .toml file, so permissions ifor this file should be set to 660.

# Running as a cron job

The main goal here is to run automatic updates, and the most practical way to do it is to use crontab.
