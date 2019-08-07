from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install
import os
import shutil


def readme():
    with open('README.rst') as f:
        return f.read()


def copy_config_files():
    import ranking_table_tennis as rtt
    pkg_path = os.path.join(os.path.dirname(rtt.__file__), 'config')
    user_config_path = os.path.expanduser(os.path.join("~", ".config/ranking_table_tennis"))
    if not os.path.exists(user_config_path):
        os.makedirs(user_config_path)
    for file in os.listdir(pkg_path):
        shutil.copy(os.path.join(pkg_path, file), user_config_path)


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        copy_config_files()
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        copy_config_files()
        install.run(self)


setup(name='ranking_table_tennis',
      version='2019.4.3',
      description='A ranking table tennis system',
      url='http://github.com/srvanrell/ranking-table-tennis',
      author='Sebastian Vanrell',
      author_email='srvanrell@gmail.com',
      packages=['ranking_table_tennis'],
      scripts=['bin/rtt'],
      include_package_data=True,
      install_requires=[
          'gspread>=3.1.0',
          'oauth2client>=4.1.2',
          'PyYAML>=3.12',
          'urllib3>=1.23',
          'openpyxl>=2.4.2,<2.6',
          'Unidecode>=1.0.22',
          'pandas>=0.20.3'
      ],
      cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
      },
      classifiers=[
          'License :: OSI Approved :: MIT License'
      ],
      zip_safe=False)

