import os
import shutil

from conftest import get_expected_folder_path
from pandas.testing import assert_frame_equal

from ranking_table_tennis import helpers
from ranking_table_tennis.configs import get_cfg

cfg = get_cfg()


def test_cli_aaa_run_before_tests(shell):
    """To be run once before all tests"""
    example_data = os.path.join(get_expected_folder_path(), cfg.io.tournaments_filename)
    shutil.copy2(example_data, cfg.io.data_folder)
    ret = shell.run("rtt", "preprocess", "--offline")
    assert ret.returncode == 0
    # Repeat twice, it should provide consistent results
    for _ in range(2):
        ret = shell.run("rtt", "compute")
        assert ret.returncode == 0


def test_compute_rankings_outputs_players_and_histories(players_df, history_df):
    # Load output
    players_output = helpers.load_from_pickle(cfg.io.players_pickle)

    assert_frame_equal(players_output.players_df, players_df)
    assert_frame_equal(players_output.history_df, history_df)


def test_compute_rankings_outputs_tournaments(tournaments_df):
    # Load output
    tournaments_output = helpers.load_from_pickle(cfg.io.tournaments_pickle)

    assert_frame_equal(tournaments_output.tournaments_df, tournaments_df)


def test_compute_rankings_outputs_rankings(ranking_df, rating_details_df, championship_details_df):
    # Load output
    rankings_output = helpers.load_from_pickle(cfg.io.rankings_pickle)

    assert_frame_equal(rankings_output.ranking_df, ranking_df)
    assert_frame_equal(rankings_output.rating_details_df, rating_details_df)
    assert_frame_equal(rankings_output.championship_details_df, championship_details_df)
