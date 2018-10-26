#!/usr/bin/python3

import sys
import subprocess as sh
from pyvirtualdisplay import Display
import requests
import exp

def check_continue(prompt):
    inp = input("{} Continue (y/[n])?".format(prompt))
    if len(inp) > 0 and ('y' in inp or 'Y' in inp):
        return True
    return False

def check_required_files():
    ls = sh.check_output('git ls-files', shell=True).decode('utf-8')
    ls = ls.split("\n")
    return 'NAME.txt' in ls

def check_repo_clean():
    cmd = 'git status -s --ignore-submodules'
    ls = sh.check_output(cmd, shell=True)
    if len(ls) == 0:
        return True
    else:
        return check_continue("Ensure your files are committed.")

def upload(score):
    url = "http://6829fa18.csail.mit.edu/registerPS3"
    name = ''
    with open('NAME.txt', 'r') as f:
        name = f.read()
    
    try:
        resp = requests.post(url,
            json = {
                'team': name,
                'score': score,
            },
            timeout=5,
        )
        if resp.status_code != 200:
            err = next(resp.iter_lines()).decode("utf-8")
            print("ERROR: server response: " + err)
            return
    except Exception as e:
        print("Could not contact contest server: " + str(e))
        return

    print("Check your results at http://6829fa18.csail.mit.edu/teams/{}/report.html".format(name))
    print("Check the leaderboard at http://6829fa18.csail.mit.edu/leaderboard.html")

s = check_required_files()
if not s:
    print("Ensure you have committed NAME.txt")
    sys.exit(1)

display = Display(visible=0, size=(1000,800))
display.start()
results = exp.start_all()
display.stop()
upload(results["score"])

