import pytest
from conftest import base_run_before_tests
from pandas.testing import assert_frame_equal

from ranking_table_tennis import compute_rankings, helpers, preprocess
from ranking_table_tennis.configs import ConfigManager


@pytest.fixture(scope="module", autouse=True)
def run_before_tests():
    """To be run once before all tests"""
    base_run_before_tests()
    preprocess.main()
    # Repeat twice, it should provide consistent results
    for _ in range(2):
        compute_rankings.main()


def test_compute_rankings_outputs_players_and_histories(ref_players_df, ref_history_df):
    cfg = ConfigManager().current_config
    # Load output
    players_output = helpers.load_from_pickle(cfg.io.pickle.players)

    assert_frame_equal(players_output.players_df, ref_players_df)
    assert_frame_equal(players_output.history_df, ref_history_df)


def test_compute_rankings_outputs_tournaments(ref_tournaments_df):
    cfg = ConfigManager().current_config
    # Load output
    tournaments_output = helpers.load_from_pickle(cfg.io.pickle.tournaments)

    assert_frame_equal(tournaments_output.tournaments_df, ref_tournaments_df)


def test_compute_rankings_outputs_rankings(
    ref_ranking_df, ref_rating_details_df, ref_championship_details_df
):
    cfg = ConfigManager().current_config
    # Load output
    rankings_output = helpers.load_from_pickle(cfg.io.pickle.rankings)

    assert_frame_equal(rankings_output.ranking_df, ref_ranking_df)
    assert_frame_equal(rankings_output.rating_details_df, ref_rating_details_df)
    assert_frame_equal(rankings_output.championship_details_df, ref_championship_details_df)
