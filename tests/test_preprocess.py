import pytest
from conftest import assert_equals_xlsx, base_run_before_tests, get_expected_folder_path
from pandas.testing import assert_frame_equal

from ranking_table_tennis import helpers, preprocess
from ranking_table_tennis.configs import ConfigManager


@pytest.fixture(scope="module", autouse=True)
def run_before_tests():
    """To be run once before all tests"""
    base_run_before_tests()
    # Repeat twice, it should provide consistent results
    for _ in range(2):
        preprocess.main()


def test_preprocess_xlsx_output():
    """Compare xlsx preprocessed between expected and output folder"""
    cfg = ConfigManager().current_config
    assert_equals_xlsx(
        get_expected_folder_path(), cfg.io.data_folder, cfg.io.xlsx.tournaments_filename
    )


def test_preprocess_outputs_players_and_histories(players_df):
    cfg = ConfigManager().current_config
    # Load output from preprocess
    players_output = helpers.load_from_pickle(cfg.io.pickle.players)

    assert_frame_equal(players_output.players_df, players_df)
    assert players_output.history_df.empty


def test_preprocess_outputs_tournaments(tournaments_df):
    cfg = ConfigManager().current_config
    # Load output from preprocess
    tournaments_output = helpers.load_from_pickle(cfg.io.pickle.tournaments)

    assert_frame_equal(tournaments_output.tournaments_df, tournaments_df)
