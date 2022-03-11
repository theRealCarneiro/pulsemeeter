import os
import sys
import pathlib
from setuptools import setup

try:
    import pulsemeeter
except ImportError as ex:
    print(f'ERROR: {ex.name} not installed, please run \'pip install requirements.txt\' inside source directory')


VERSION = pulsemeeter.__version__
README = (pathlib.Path(__file__).parent / "README.md").read_text()
DATA_FILES = [('share/licenses/pulsemeeter/', ['LICENSE']),]
REQUIREMENTS = []

with open('requirements.txt') as file:
    for line in file:
        REQUIREMENTS.append(line.rstrip())

for directory, _, filenames in os.walk(u'share'):
    dest = directory[6:]
    if filenames:
        files = [os.path.join(directory, filename) for filename in filenames]
        DATA_FILES.append((os.path.join('share', dest), files))

setup(
    name='pulsemeeter',
    version=VERSION,
    description='A pulseaudio audio routing application',
    long_description=README,
    long_description_content_type="text/markdown",
    author='Gabriel Carneiro',
    author_email='therealcarneiro@gmail.com',
    license="MIT",
    license_files='LICENSE',
    classifiers=[
        "Environment :: X11 Applications",
        "License :: OSI Approved :: MIT License",
    ],
    url='https://github.com/theRealCarneiro/pulsemeeter',
    packages=['pulsemeeter','pulsemeeter.interface','pulsemeeter.socket','pulsemeeter.backends'],
    install_requires=REQUIREMENTS,
    data_files=DATA_FILES,
    entry_points={
        "console_scripts": [
            "pulsemeeter = pulsemeeter.__main__:main",
        ],
    },

    python_requires=">=3.5",
    scripts=[
        'scripts/pmctl',
    ],
    include_package_data=True
)
