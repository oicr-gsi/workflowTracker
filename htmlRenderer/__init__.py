"""
   This module provides functions for converting json to html and formatting
   it either as a table or complete HTML page. All hardcoded stuff is here!
"""
from json2html import *
from bs4 import BeautifulSoup as Bs
import datetime


"""
   Return date wrapped in div
"""
def today_date() -> str:
    today = datetime.date.today()
    formatted_today = today.strftime("%A %d. %B %Y")
    return formatted_today


"""
   Return JSON rendered into HTML table
"""
def convert2page(input_data: dict):
    html = "<!DOCTYPE html><html><head><meta charset=\"UTF-8\"><title>Production Workflows</title> \
           <style> table {border-collapse: separate; border-spacing: 0;} \
           th {position: sticky; top: 0; padding: 4px; background-color: #009879; color: #ffffff; border-bottom: 2px solid #ddd; text-align: left;} \
           td {padding: 4px; text-align: left; border-bottom: 1px solid #ddd; }</style> \
           </head><body>" + convert2table(input_data) + "<div><h3>Updated on" + today_date() + "</h3></div></body></html>"

    soup = Bs(html, "html.parser")
    return soup.prettify()

"""
   Using data from input, re-wrap the data into a hash and return HTML
"""
def convert2table(inputs: dict) -> dict:
    rewrapped = []
    for wf in inputs.keys():
        rewrapped.append({"Workflow/alias": wf,
                        "RUO Tags": inputs[wf]['research']['tags'] if 'research' in inputs[wf].keys() else [],
                        "Clinical Tags": inputs[wf]['clinical']['tags'] if 'clinical' in inputs[wf].keys() else [],
                        "Latest Tag": inputs[wf]['latest_tag'] if inputs[wf]['latest_tag'] else " ",
                        "Repository": f'<a href=\"{inputs[wf]["url"]}\">{inputs[wf]["url"]}</a>' if inputs[wf]['url'] else " ",
                        "Software Modules": inputs[wf]['code_modules'],
                        "Data Modules": inputs[wf]['data_modules'],
                        "RUO Olives": inputs[wf]['research']['olives'] if 'research' in inputs[wf].keys() else [],
                        "Clinical Olives": inputs[wf]['clinical']['olives'] if 'clinical' in inputs[wf].keys() else []})
    return json2html.convert(json=rewrapped, table_attributes="id=\"info-table\" class=\"styled-table\"", escape=False)
