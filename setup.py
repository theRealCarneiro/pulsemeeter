import os
from setuptools import setup


DATA_FILES = [('share/licenses/pulsemeeter/', ['LICENSE']), ]

for directory, _, filenames in os.walk('share'):
    dest = directory[6:]
    if filenames:
        files = [os.path.join(directory, filename) for filename in filenames]
        DATA_FILES.append((os.path.join('share', dest), files))

setup(data_files=DATA_FILES)
