import glob
import os
import shutil

import pandas as pd
import pytest


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    data_rtt_folder = os.path.join(os.path.dirname(__file__), "data_rtt")

    print("\n## Before starting tests\n")
    if os.path.exists(data_rtt_folder):
        print(f"\nRemoving data folder before tests: remove {data_rtt_folder}")
        shutil.rmtree(data_rtt_folder)


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    from ranking_table_tennis.configs import get_cfg

    cfg = get_cfg()

    print("\n## After tests have finalized\n")
    print(f"\nRemoving data folder after test: remove {cfg.io.data_folder}")
    shutil.rmtree(cfg.io.data_folder)


def assert_equals_xlsx(reference_folder, output_folder, name_pattern):
    expected_folder_path = os.path.relpath(reference_folder)
    filenames = glob.glob(os.path.join(expected_folder_path, name_pattern))
    filenames = [fn.replace(expected_folder_path + "/", "") for fn in filenames]

    for fn in filenames:
        dfs_expected = pd.read_excel(os.path.join(expected_folder_path, fn), sheet_name=None)
        dfs_output = pd.read_excel(os.path.join(output_folder, fn), sheet_name=None)

        assert sorted(dfs_expected.keys()) == sorted(dfs_output.keys()), "Sheetname differences"

        for name, df in dfs_expected.items():
            assert df.equals(dfs_output[name]), f"Mismatch on {name} sheet"


def get_expected_folder_path():
    return os.path.join(os.path.dirname(__file__), "data_up_to_S2022T04")


def load_expected_output(csv_filename, parse_dates=False):
    expected_path = get_expected_folder_path()
    expected_filepath = os.path.join(expected_path, csv_filename)
    if parse_dates:
        return pd.read_csv(
            expected_filepath, index_col=0, parse_dates=["date"], keep_default_na=False
        )
    return pd.read_csv(expected_filepath, index_col=0, keep_default_na=False)


@pytest.fixture(scope="session")
def tournaments_df():
    return load_expected_output("tournaments_df.csv", parse_dates=True)


@pytest.fixture(scope="session")
def players_df():
    return load_expected_output("players_df.csv")


@pytest.fixture(scope="session")
def history_df():
    return load_expected_output("history_df.csv")


@pytest.fixture(scope="session")
def rating_details_df():
    return load_expected_output("rating_details_df.csv", parse_dates=True)


@pytest.fixture(scope="session")
def ranking_df():
    return load_expected_output("ranking_df.csv", parse_dates=True)


@pytest.fixture(scope="session")
def championship_details_df():
    return load_expected_output("championship_details_df.csv")
