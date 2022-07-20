from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
import os
import shutil


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
        "console_scripts": ["rtt2=ranking_table_tennis.command_line:main"],
    },
    include_package_data=True,
    install_requires=[
        "gspread>=3.6.0",
        "oauth2client>=4.1.2",
        "PyYAML>=5.4.1",
        "urllib3>=1.23",
        "openpyxl>=3.0.4,<3.0.6",
        "Unidecode>=1.0.22",
        "pandas>=1.0.5,<1.3",
        "xlrd>=1.0.0,<2.0",
        "gspread-dataframe>=1.0.4",
        "tabulate>=0.8.7",
        "matplotlib>=3.1.0",
        "omegaconf",
    ],
    cmdclass={
        "develop": PostDevelopCommand,
        "install": PostInstallCommand,
    },
    extras_require={"dev": ["pre-commit==2.18.*"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.6",
    zip_safe=False,
)
