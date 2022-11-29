import os
import re
import sys
import json
import subprocess


def snake_case(s):
    return '_'.join(
        re.sub('([A-Z][a-z]+)', r' \1',
        re.sub('([A-Z]+)', r' \1',
        s.replace('-', ' '))).split()).lower()


def index(s, i):
    try:
        return s.index(i)
    except ValueError:
        return 999999


def split_line(li):
    li = li.replace("\"", '').replace('\'', '')

    hsi = index(li, '#')
    sci = index(li, ':')
    eqi = index(li, '=')

    tokens = None

    if hsi < sci:
        tokens = li.split('#', 2)
        tokens[0] = 'index'
    elif (sci < eqi):
        tokens = li.split(':', 1)
    else:
        tokens = li.split('=', 2)

    return tokens


def volume(s):
    o = {}
    vl = s.replace(',', '\n').split('\n')
    for i in vl:
        channel = i.split(':', 1)
        tmp = channel[1].split('/')
        o[channel[0].strip()] = {
            'value': int(tmp[0].strip()),
            'value_percent': tmp[1].strip(),
            'db': tmp[2].strip()
        }

    return o


def jsonify(i, j):
    kv = split_line(i)
    key = kv[0].strip()
    if key and len(kv) > 1:

        # properties
        if kv[1][0] == ';':
            kv[1] = kv[1].replace(';', '\n\t')
            j[snake_case(key)] = tokenize(kv[1])

        elif key == 'Volume':
            j[snake_case(key)] = volume(kv[1])

        elif key == 'Mute':
            j[snake_case(key)] = False if kv[1] == 'no' else True

        elif key == 'Base Volume':
            tmp = kv[1].split('/')
            j[snake_case(key)] = {
                'value': int(tmp[0].strip()),
                'value_percent': tmp[1].strip(),
                'db': tmp[2].strip()
            }

        elif key == 'Flags':
            j[snake_case(key)] = kv[1].split(' ')[1:-1]

        else:
            val = kv[1].strip()
            if val.isdigit():
                val = int(val)
            j[snake_case(key)] = val


def tokenize(s):

    s = s.replace('\n\t\t', ';')
    lineArr = s.split('\n\t')
    if lineArr[0] == '':
        lineArr = lineArr[1:]
    o = {}

    for i in lineArr:
        jsonify(i, o)

    return o


def get_devices(device_type):
    sink_blocks = cmd(f'pactl list {device_type}').split('\n\n')
    sink_arr = []
    for i in sink_blocks:
        sink_arr.append(tokenize(i))
    return sink_arr


def cmd(command):
    myenv = os.environ.copy()
    myenv['LC_ALL'] = 'C'
    sys.stdout.flush()
    p = subprocess.Popen(command.split(' '),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=myenv)
    stdout, stderr = p.communicate()
    # if p.returncode:
        # LOG.warning(f'cmd \'{command}\' returned {p.returncode}')
    return stdout.decode()
