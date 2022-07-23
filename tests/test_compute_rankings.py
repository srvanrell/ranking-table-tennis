import pytest
from ranking_table_tennis import preprocess, compute_rankings
from ranking_table_tennis.configs import cfg
from ranking_table_tennis import utils
from pandas.testing import assert_frame_equal


@pytest.fixture(scope="module", autouse=True)
def my_fixture():
    """To be run once before all tests"""
    preprocess.main()
    compute_rankings.main()


def test_compute_rankings_outputs_players_and_histories(players_df, history_df):
    # Load output
    players_output = utils.load_from_pickle(cfg.io.players_pickle)

    assert_frame_equal(players_output.players_df, players_df)
    assert_frame_equal(players_output.history_df, history_df)


def test_compute_rankings_outputs_tournaments(tournaments_df):
    # Load output
    tournaments_output = utils.load_from_pickle(cfg.io.tournaments_pickle)

    assert_frame_equal(tournaments_output.tournaments_df, tournaments_df)


def test_compute_rankings_outputs_rankings(ranking_df, rating_details_df, championship_details_df):
    # Load output
    rankings_output = utils.load_from_pickle(cfg.io.rankings_pickle)

    assert_frame_equal(rankings_output.ranking_df, ranking_df)
    assert_frame_equal(rankings_output.rating_details_df, rating_details_df)
    assert_frame_equal(rankings_output.championship_details_df, championship_details_df)
