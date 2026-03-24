# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`ranking-table-tennis` is a CLI tool for managing table tennis player rankings. It maintains two parallel metrics:
- **Rating Points**: Relative skill levels based on head-to-head match outcomes (Elo-style)
- **Championship Points**: Tournament achievements based on best rounds reached

Data flows through a 3-step pipeline: **preprocess → compute → publish**

## Commands

### Setup
```bash
uv venv && uv sync --group test
```

### Running the CLI
```bash
uv run rtt preprocess   # Load tournaments, query missing player info
uv run rtt compute      # Calculate ratings and championship points
uv run rtt publish      # Generate formatted output spreadsheets
uv run rtt automatic    # Run all steps non-interactively (to be used in prodction only)
```

### Testing
Golden datasets are used to test that no change in the output is introduced.
```bash
uv run pytest -vv tests                          # Run all tests
uv run pytest -vv tests/test_models.py           # Run a single test file
uv run pytest -vv tests -k "test_name"           # Run a specific test
make test-coverage                               # Tests with coverage report
```

### Linting and Formatting
```bash
uv run ruff check .      # Lint
uv run ruff format .     # Format
uv run mypy .            # Type checking
```

### Build and Publish
```bash
uv build
uv publish
```

## Architecture

### Pipeline Stages

1. **Preprocess** (`preprocess.py` / `preprocess_unattended.py`): Downloads tournament data from Google Sheets/Excel, queries user for missing player info (affiliation, city), assigns initial rating points for new players, saves intermediate state as pickle files.

2. **Compute** (`compute_rankings.py`): Loads pickled data, processes matches to compute winner/loser outcomes, applies rating changes using expected result tables, computes championship points from best rounds, handles promotions/sanctions/categories, updates rankings.

3. **Publish** (`publish.py` + `helpers/publisher.py`): Generates formatted Excel and Markdown output with rankings, match details, championship breakdowns, and interactive Plotly visualizations.

### Core Models (`ranking_table_tennis/models/`)

- **`Players`**: Player database with pid, name, affiliation, city. Normalizes names (title case, unicode). Tracks tournament participation history.
- **`Tournaments`**: Tournament data with match records (player_a, player_b, sets_a, sets_b, round, category). Generates tids in format `S{YYYY}T{##}`. Computes best rounds per player per category.
- **`Rankings`**: The core calculation model. Tracks rating points and championship points per player. Dynamically generates columns for multi-category support. Implements `compute_new_ratings()`, `compute_championship_points()`, `update_categories()`, `promote_players()`, `apply_sanction()`.

### Configuration System (`ranking_table_tennis/configs.py`)

Uses **Hydra** with date-ranged YAML files (e.g., `config_220101_220723.yaml`) so different rule sets apply to different date ranges. `ConfigManager` selects the appropriate config based on tournament date. CSV tables define points per round (`points_per_round.csv`) and expected match results (`expected_result.csv`, `unexpected_result.csv`).

### Helper Modules (`ranking_table_tennis/helpers/`)

- `excel.py`: Excel I/O (load/save tournaments, players, rankings via openpyxl/pandas)
- `gspread.py`: Google Sheets integration (OAuth2 via oauth2client)
- `publisher.py`: All output sheet generation logic
- `plotter.py`: Plotly-based interactive visualizations
- `pickle.py`: Intermediate data serialization between pipeline stages
- `initial_rating.py`: Suggests initial ratings for new players
- `temp_players.py`: Manages resumable state during interactive preprocessing

### Intermediate Data

Pickle files store state between pipeline stages, enabling the pipeline steps to run independently. The `preprocess` step saves pickles; `compute` reads them and saves updated pickles; `publish` reads the final state.

### Versioning

Uses date-based versioning (`YYYY.MM.DD`). To release: update `pyproject.toml`, merge to master, tag the commit — GitHub Actions publishes to PyPI automatically.
Don't make a release unless the user ask explicitly about it.
