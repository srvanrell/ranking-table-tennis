import os
import shutil

from setuptools import find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install


def readme():
    with open("README.md") as f:
        return f.read()


def copy_config_files():
    import ranking_table_tennis as rtt

    pkg_path = os.path.join(os.path.dirname(rtt.__file__), "config")
    user_config_path = os.path.join("data_rtt", "config")
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


setup(
    name="ranking_table_tennis",
    version="2022.4.9",
    description="A ranking table tennis system",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="http://github.com/srvanrell/ranking-table-tennis",
    author="Sebastian Vanrell",
    author_email="srvanrell@gmail.com",
    packages=find_packages(),
    entry_points={
        "console_scripts": ["rtt=ranking_table_tennis.command_line:main"],
    },
    include_package_data=True,
    install_requires=[
        "gspread==5.*",
        "oauth2client==4.*",
        "PyYAML>=5.4.1",
        "urllib3==1.*",
        "openpyxl>=3.0.6,<3.1.0",
        "Unidecode==1.*",
        "pandas==1.3.*",
        "gspread-dataframe==3.*",
        "tabulate==0.8.*",
        "matplotlib==3.*",
        "omegaconf==2.2.*",
    ],
    cmdclass={
        "develop": PostDevelopCommand,
        "install": PostInstallCommand,
    },
    extras_require={
        "dev": ["pre-commit==2.18.*", "pytest==7.1.*", "pytest-shell-utilities==1.5.*", "tox==3.*"]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.6",
    zip_safe=False,
)
