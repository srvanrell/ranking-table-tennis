from conftest import base_cli_run_after_tests, base_run_before_tests
from pandas.testing import assert_frame_equal

from ranking_table_tennis import helpers
from ranking_table_tennis.configs import ConfigManager


def test_cli_compute_run_before_tests(shell):
    """To be run once before all tests"""
    base_run_before_tests()
    ret = shell.run("rtt", "preprocess", "--offline")
    assert ret.returncode == 0
    print(ret.stdout)
    # Repeat twice, it should provide consistent results
    for _ in range(2):
        ret = shell.run("rtt", "compute")
        assert ret.returncode == 0
        print(ret.stdout)
    base_cli_run_after_tests()


def test_cli_compute_outputs_players_and_histories(players_df, history_df):
    cfg = ConfigManager().current_config
    # Load output
    players_output = helpers.load_from_pickle(cfg.io.pickle.players)

    assert_frame_equal(players_output.players_df, players_df)
    assert_frame_equal(players_output.history_df, history_df)


def test_cli_compute_outputs_tournaments(tournaments_df):
    cfg = ConfigManager().current_config
    # Load output
    tournaments_output = helpers.load_from_pickle(cfg.io.pickle.tournaments)

    assert_frame_equal(tournaments_output.tournaments_df, tournaments_df)


def test_cli_compute_outputs_rankings(ranking_df, rating_details_df, championship_details_df):
    cfg = ConfigManager().current_config
    # Load output
    rankings_output = helpers.load_from_pickle(cfg.io.pickle.rankings)

    assert_frame_equal(rankings_output.ranking_df, ranking_df)
    assert_frame_equal(rankings_output.rating_details_df, rating_details_df)
    assert_frame_equal(rankings_output.championship_details_df, championship_details_df)
