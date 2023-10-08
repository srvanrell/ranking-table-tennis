from setuptools import find_packages, setup


def readme():
    with open("README.md") as f:
        return f.read()


setup(
    name="ranking_table_tennis",
    version="2023.10.8",
    description="A ranking table tennis system",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="http://github.com/srvanrell/ranking-table-tennis",
    author="Sebastian Vanrell",
    author_email="srvanrell_gmail_com",
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
        "hydra-core==1.2.*",
        "plotly==5.*",
    ],
    extras_require={
        "dev": [
            "pre-commit==2.18.*",
            "pytest==7.1.*",
            "pytest-shell-utilities==1.5.*",
            "tox==3.*",
            "pyclean==2.2.*",
            "pytest_profiling==1.7.*",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.6",
    zip_safe=False,
)
