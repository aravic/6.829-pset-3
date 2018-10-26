#!/usr/bin/python3

import sys
from pyvirtualdisplay import Display
import requests
import exp
import os
import network

def check_required_files():
    return os.path.exists("NAME.txt")

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
scaled_trace = "scaled_submit_trace.dat"
network.trace_with_target("traces/Verizon1.dat", scaled_trace, 2)
print '\nRunning experiment...this may take several minutes to complete. Please do not exit!\n'
results = exp.start_all(scaled_trace, "10.0.0.1")
display.stop()
os.remove(scaled_trace)
upload(results["score"])
os.system("killall Xvfb > /dev/null 2>&1")
