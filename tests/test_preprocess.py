import pytest
from ranking_table_tennis import preprocess
from ranking_table_tennis.configs import cfg
from ranking_table_tennis import utils
import pickle
import os
from pandas.testing import assert_frame_equal


@pytest.fixture(scope="module", autouse=True)
def my_fixture():
    """To be run once before all tests"""
    preprocess.main()


def test_preprocess_outputs_players_and_histories(players_df):
    # Load output from preprocess
    output_filename = os.path.join(cfg.io.data_folder, "players.pk")
    players_output = pickle.load(open(output_filename, "rb"))

    assert_frame_equal(players_output.players_df, players_df)
    assert players_output.history_df.empty


def test_preprocess_outputs_tournaments(tournaments_df):
    # Load output from preprocess
    tournaments_output = utils.load_from_pickle(cfg.io.tournaments_pickle)

    # winner and loser Players ID are not assignated during preprocessing
    tournaments_df = tournaments_df.copy()
    tournaments_df.winner_pid = None
    tournaments_df.loser_pid = None

    print(tournaments_df.head())
    print(tournaments_output.tournaments_df.head())
    assert_frame_equal(tournaments_output.tournaments_df, tournaments_df)
