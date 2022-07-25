import os
import shutil

from conftest import assert_equals_xlsx, get_expected_folder_path
from pandas.testing import assert_frame_equal

from ranking_table_tennis import helpers
from ranking_table_tennis.configs import get_cfg

cfg = get_cfg()


def test_cli_aaa_run_before_tests(shell):
    """To be run once before all tests"""
    example_data = os.path.join(get_expected_folder_path(), cfg.io.tournaments_filename)
    shutil.copy2(example_data, cfg.io.data_folder)
    # Repeat twice, it should provide consistent results
    for _ in range(2):
        ret = shell.run("rtt", "preprocess", "--offline")
        assert ret.returncode == 0


def test_cli_preprocess_xlsx_output():
    """Compare xlsx preprocessed between expected and output folder"""
    assert_equals_xlsx(get_expected_folder_path(), cfg.io.data_folder, cfg.io.tournaments_filename)


def test_cli_preprocess_outputs_players_and_histories(players_df):
    # Load output from preprocess
    players_output = helpers.load_from_pickle(cfg.io.players_pickle)

    assert_frame_equal(players_output.players_df, players_df)
    assert players_output.history_df.empty


def test_cli_preprocess_outputs_tournaments(tournaments_df):
    # Load output from preprocess
    tournaments_output = helpers.load_from_pickle(cfg.io.tournaments_pickle)

    assert_frame_equal(tournaments_output.tournaments_df, tournaments_df)
