import pytest
import os
import pandas as pd


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    pass


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    pass


def load_expected_output(csv_filename, parse_dates=False):
    expected_path = os.path.join(os.path.dirname(__file__), "data_up_to_S2022T04")
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
