from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install
import os
import shutil


def readme():
    with open('README.rst') as f:
        return f.read()


# Loads some names from config.yaml
user_config_path = os.path.expanduser("~") + "/.config/ranking_table_tennis"


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        import ranking_table_tennis as rtt
        pkg_path = os.path.dirname(rtt.__file__) + '/config'
        files = os.listdir(pkg_path)
        for f in files:
            shutil.copy(os.path.join(pkg_path, f), user_config_path)
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        import ranking_table_tennis as rtt
        pkg_path = os.path.dirname(rtt.__file__) + '/config'
        files = os.listdir(pkg_path)
        for f in files:
            shutil.copy(os.path.join(pkg_path, f), user_config_path)
        install.run(self)


setup(name='ranking_table_tennis',
      version='2019.3',
      description='A ranking table tennis system',
      url='http://github.com/srvanrell/ranking-table-tennis',
      author='Sebastian Vanrell',
      author_email='srvanrell@gmail.com',
      license='MIT',
      packages=['ranking_table_tennis'],
      scripts=['bin/rtt'],
      include_package_data=True,
      install_requires=[
          'gspread>=3.1.0',
          'oauth2client>=4.1.2',
          'PyYAML>=3.12',
          'urllib3>=1.23',
          'openpyxl>=2.4.2',
          'Unidecode>=1.0.22',
          'pandas>=0.20.3'
      ],
      cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
      },
      zip_safe=False)

