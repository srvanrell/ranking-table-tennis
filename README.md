# ranking-table-tennis

Ranking system for table tennis players.

The system keeps a record of championship points and rating points.

Championship points aim at tracking the tournament achievements of players.
Their computation is based on the best rounds reached by players in each tournament.

Rating points aim at tracking the relative skill level of players.
Their computation is based on the outcomes of one-versus-one matches.

## Installation

This system has been developed for a Linux environment.

### Using uv (recommended)

    uv venv [-p 3.12]
    uv sync

Install the package globally (not recommended):

    uv pip install ranking-table-tennis

### Using pip (single user)

    pip install --user ranking-table-tennis

Uninstallation

    pip uninstall ranking-table-tennis

### Authentication for gspread

To start using the upload spreadsheets capabilities, gspread requires authentication.
Please, follow the [recommended steps](https://docs.gspread.org/en/latest/oauth2.html) to get your system ready to upload.

## Update

Using uv (recommended):

    uv sync

Using pip (single user):

    pip install --user --upgrade ranking-table-tennis

## Usage

The commands must be run in a bash terminal. Use `uv run ...` if you have installed with uv.

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

Install locally from source (editable mode):

    uv sync --group test
    uv run pytest

Install with pip (editable mode):

    pip install --editable ".[test]"
    pytest

Update version at `pyproject.toml` and push it to github. We follow date versions like `vYYYY.MM.DD`

Once it is merged on master you must tag the commit so a github actions will be triggered to do the rest:

    uv build
    uv publish
