import ranking_table_tennis.preprocess
from ranking_table_tennis.configs import cfg
import pickle
import os
from pandas.testing import assert_frame_equal


def test_preprocess_outputs_players_and_histories():
    # Run complete preprocess unattended and offline
    ranking_table_tennis.preprocess.main()

    # Load output from preprocess
    output_filename = os.path.join(cfg.io.data_folder, "players.pk")
    players_output = pickle.load(open(output_filename, "rb"))

    # Load expected output
    expected_path = os.path.join(os.path.dirname(__file__), "data_up_to_S2022T04")
    expected_filename = os.path.join(expected_path, "players.pk")
    players_expected = pickle.load(open(expected_filename, "rb"))

    assert_frame_equal(players_output.players_df, players_expected.players_df)
    assert players_output.history_df.empty


def test_preprocess_outputs_tournaments():
    # Run complete preprocess unattended and offline
    # ranking_table_tennis.preprocess.main()

    # Load output from preprocess
    output_filename = os.path.join(cfg.io.data_folder, "tournaments.pk")
    tournaments_output = pickle.load(open(output_filename, "rb"))

    # Load expected output
    expected_path = os.path.join(os.path.dirname(__file__), "data_up_to_S2022T04")
    expected_filename = os.path.join(expected_path, "tournaments.pk")
    tournaments_expected = pickle.load(open(expected_filename, "rb"))

    # winner and loser Players ID are not assignated during preprocessing
    tournaments_expected.tournaments_df.winner_pid = None
    tournaments_expected.tournaments_df.loser_pid = None
    assert_frame_equal(tournaments_output.tournaments_df, tournaments_expected.tournaments_df)
