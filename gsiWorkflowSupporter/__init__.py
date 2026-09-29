"""
   This package is for handling requests to github repo.
   it should initialize and respond to different requests
"""
import re

class GsiWorkflowSupporter:
    deployed_workflows = []
    supported_workflows = []
    table_path = ""

    def __init__(self, deployed_workflows: list, table_path: str):
        self.deployed_workflows = sorted(deployed_workflows)
        self.table_path = table_path
        self.supported_workflows = GsiWorkflowSupporter.get_wf_list(table_path)

    ''' Return a list of supported workflows from current checking olive '''
    @staticmethod
    def get_wf_list(table_path: str) -> list:
        supported_workflows = []
        try:
            with open(table_path) as op:
                supported_workflows = list(line.strip() for line in op if re.match(r"\S+_v\d+_\d+_*\d*\w*$", line))
        except Exception:
            print("ERROR: Failed to extract supported workflows from current check olive")
        return sorted(supported_workflows)

    ''' Return true if lists are identical and false if they are not (we expect both to be sorted)'''
    def lists_identical(self) -> bool:
        return self.supported_workflows == self.deployed_workflows

    ''' In case we have deployed workflows which are not the same as in supported olive, update the olive code '''
    @staticmethod
    def update_table(deployed_workflows: list, table_path: str):
        try:
            with open(table_path, "w") as updating_olive:
                updating_olive.writelines(line + "\n" for line in deployed_workflows)
        except:
            print("ERROR: An update process failed for alerting olive")

    ''' Function to handle the check and update (if needed) '''
    def process_update(self):
        if not self.lists_identical():
            GsiWorkflowSupporter.update_table(self.deployed_workflows, self.table_path)
