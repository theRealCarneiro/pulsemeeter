import os
from setuptools import setup
from babel.messages import frontend as babel
from setuptools.command.build_py import build_py as _build_py


class build_with_translations(_build_py):
    def run(self):
        self.run_command("compile_catalog")
        super().run()


DATA_FILES = [('share/licenses/pulsemeeter/', ['LICENSE']), ]

for directory, _, filenames in os.walk('share'):
    dest = directory[6:]
    if filenames:
        files = [os.path.join(directory, filename) for filename in filenames]
        DATA_FILES.append((os.path.join('share', dest), files))

# package .mo files
for directory, _, filenames in os.walk('locale'):
    if filenames:
        files = [os.path.join(directory, filename) for filename in filenames if '.mo' in filename]
        DATA_FILES.append((os.path.join('share', directory), files))

setup(
    data_files=DATA_FILES,
    cmdclass={
        'build_py': build_with_translations,
        'compile_catalog': babel.compile_catalog,
        'extract_messages': babel.extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': babel.update_catalog
    },
    message_extractors={
        'src': [
            ('**/*.py', 'python', None),
        ],
    },
)
