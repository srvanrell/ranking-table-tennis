import glob
import logging
import os
import shutil

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

logger = logging.getLogger(__name__)


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    data_rtt_folder = os.path.join(os.path.dirname(__file__), "data_rtt")

    logger.debug("## Before starting tests...")
    if os.path.exists(data_rtt_folder):
        logger.debug("Removing data folder before tests: remove %", data_rtt_folder)
        shutil.rmtree(data_rtt_folder)


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    data_rtt_folder = os.path.join(os.path.dirname(__file__), "data_rtt")

    logger.debug("## After tests have finalized...")
    if os.path.exists(data_rtt_folder):
        logger.debug("Removing data folder after test: remove %s", data_rtt_folder)
        shutil.rmtree(data_rtt_folder)


def assert_equals_xlsx(reference_folder, output_folder, name_pattern):
    expected_folder_path = os.path.relpath(reference_folder)
    filenames = glob.glob(os.path.join(expected_folder_path, name_pattern))
    filenames = [fn.replace(expected_folder_path + "/", "") for fn in filenames]

    for fn in filenames:
        dfs_expected = pd.read_excel(os.path.join(expected_folder_path, fn), sheet_name=None)
        dfs_output = pd.read_excel(os.path.join(output_folder, fn), sheet_name=None)

        assert sorted(dfs_expected.keys()) == sorted(dfs_output.keys()), "Sheetname differences"

        for name, df in dfs_expected.items():
            logger.info("Verifying: %s : %s", fn, name)
            assert_frame_equal(df, dfs_output[name])


def get_expected_folder_path():
    return os.path.join(os.path.dirname(__file__), "data_up_to_S2022T04")


def get_tournaments_xlsx():
    return "Liga Dos Orillas 2022 - Carga de partidos.xlsx"


def base_run_before_tests():
    example_data = os.path.join(get_expected_folder_path(), get_tournaments_xlsx())
    if not os.path.exists("data_rtt/"):
        os.mkdir("data_rtt")
    shutil.copy2(example_data, "data_rtt/")


def base_cli_run_after_tests():
    from ranking_table_tennis.configs import ConfigManager

    ConfigManager().set_current_config(date="220101")


def load_expected_output(csv_filename, parse_dates=False):
    expected_path = get_expected_folder_path()
    expected_filepath = os.path.join(expected_path, csv_filename)
    if parse_dates:
        return pd.read_csv(
            expected_filepath, index_col=0, parse_dates=["date"], keep_default_na=False
        )
    return pd.read_csv(expected_filepath, index_col=0, keep_default_na=False)


@pytest.fixture(scope="session")
def ref_tournaments_df():
    return load_expected_output("tournaments_df.csv", parse_dates=True)


@pytest.fixture(scope="session")
def ref_players_df():
    return load_expected_output("players_df.csv")


@pytest.fixture(scope="session")
def ref_history_df():
    return load_expected_output("history_df.csv")


@pytest.fixture(scope="session")
def ref_rating_details_df():
    return load_expected_output("rating_details_df.csv", parse_dates=True)


@pytest.fixture(scope="session")
def ref_ranking_df():
    return load_expected_output("ranking_df.csv", parse_dates=True)


@pytest.fixture(scope="session")
def ref_championship_details_df():
    return load_expected_output("championship_details_df.csv")
