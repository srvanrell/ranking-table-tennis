# ranking-table-tennis

Ranking system for table tennis players.

The system keeps a record of championship points and rating points.

Championship points aim at tracking the tournament achievements of players.
Their computation is based on the best rounds reached by players in each tournament.

Rating points aim at tracking the relative skill level of players. 
Their computation is based on the outcomes of one-versus-one matches.

## Installation

This system has been developed for a Linux environment.

System-wide installation

    sudo pip3 install ranking-table-tennis

Single-user installation (recommended)

    pip3 install --user ranking-table-tennis

Uninstallation

    [sudo] pip3 uninstall ranking-table-tennis
    
## Update

System-wide update

    sudo pip3 install -U ranking-table-tennis
    
Single-user update (recommended)

    pip3 install --user -U ranking-table-tennis

## Usage

The commands must be run in a bash terminal.

1. Fill a sheet with the tournament matches. It must be saved in the Tournaments spreadsheet (xlsx).

   Players and Initial Ranking sheets must be in the same spreadsheet (it is used as a database).

2. Run `rtt preprocess`. 

   The scripts will read the Tournament spreadsheet and will ask for missing information of new players (city, affiliation, initial rating points, and category).
   This information will be saved in the Players and Initial Ranking sheets.

3. Run `rtt compute`.

   It will ask for the tournament that you want to process. 0 will compute all from the beggining.
   The outcome will be saved in the Ranking spreadsheet.

4. Run `rtt publish`.

   It will ask for the index of the tournament that you want to publish. 
The outcome will be saved in a new spreadsheet.

## Development

Install locally from source (source directory will immediately affect the installed package
without needing to re-install): 
    
    pip3 install --user --editable .
    
Update version at `setup.py` and then create a source distribution

    python3 setup.py sdist bdist_wheel
    
Upload to PyPI
    
    twine upload dist/* 
    
Upload to TestPyPI

    twine upload --repository-url https://test.pypi.org/legacy/ dist/*
