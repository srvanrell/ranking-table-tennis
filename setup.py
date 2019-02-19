from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install
from subprocess import check_call
import os
import shutil


def readme():
    with open('README.rst') as f:
        return f.read()


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self):
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        develop.run(self)

# Loads some names from config.yaml
user_config_path = os.path.expanduser("~") + "/.config/ranking_table_tennis/config.yaml"


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        import ranking_table_tennis as rtt
        # check_call("cp ranking_table_tennis/config/config.yaml ~/.config/ranking_table_tennis/config.yaml".split())
        shutil.copy(os.path.dirname(rtt.__file__) + "/config/config.yaml", user_config_path)
        install.run(self)


setup(name='ranking_table_tennis',
      version='2018.6',
      description='A ranking table tennis system',
      url='http://github.com/srvanrell/ranking-table-tennis',
      author='Sebastian Vanrell',
      author_email='srvanrell@gmail.com',
      license='MIT',
      packages=['ranking_table_tennis'],
      scripts=['bin/preprocess.py',
               'bin/compute_rankings.py',
               'bin/publish.py'],
      include_package_data=True,
      install_requires=[
          'gspread==3.1.0',
          'oauth2client==4.1.2',
          'PyYAML==3.12',
          'urllib3>=1.23',
          'openpyxl==2.4.2',
          'Unidecode==1.0.22'
      ],
      cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
      },
      zip_safe=False)
