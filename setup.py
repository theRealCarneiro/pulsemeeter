import os
from babel.messages import frontend as babel
from setuptools import setup
from setuptools.command.build_py import build_py as _build_py

IS_ZIP = os.environ.get("ZIP_BUILD") == "1"


def gather_data_files(source_dir, target_dir, pattern=''):
    datafiles = []
    for directory, _, filenames in os.walk(source_dir):
        if filenames:
            files = [os.path.join(directory, filename) for filename in filenames if pattern in filename]
            datafiles.append((os.path.join(target_dir, directory), files))

    return datafiles


class BuildWithTranslations(_build_py):
    def run(self):
        self.run_command("compile_catalog")

        mo_files = gather_data_files('locale', 'share', '.mo')
        self.distribution.data_files.extend(mo_files)

        super().run()


DATA_FILES = [('share/licenses/pulsemeeter/', ['LICENSE']), ]
DATA_FILES += gather_data_files('share', '')

setup(
    data_files=DATA_FILES,

    cmdclass={
        'build_py': BuildWithTranslations,
        # 'build_zip': BuildWithTranslations,
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
