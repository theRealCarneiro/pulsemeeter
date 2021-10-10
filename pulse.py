import os
import json
import sys
import subprocess
import re
class Pulse:

    def __init__(self, config):
        sink_list = cmd("pactl list sinks short")
        for i in range(1, len(config['vi']) + 1):
            if(config['vi'][str(i)]['name'] != ''):
                if not re.search(config['vi'][str(i)]['name'], sink_list):
                    sink = config['vi'][str(i)]['name']
                    os.popen(f"./pulsemeeter.sh init sink {sink}")

        source_list = cmd("pactl list sources short")
        for i in range(1, len(config['b']) + 1):
            if(config['b'][str(i)]['name'] != ''):
                if not re.search(config['b'][str(i)]['name'], source_list):
                    source = config['b'][str(i)]['name']
                    os.popen(f"./pulsemeeter.sh init source {source}")

def cmd(command):
    sys.stdout.flush()
    MyOut = subprocess.Popen(command.split(' '), 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT)
    stdout,stderr = MyOut.communicate()
    return stdout.decode()
