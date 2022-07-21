import ranking_table_tennis.compute_rankings
from ranking_table_tennis.configs import cfg
import pickle
import os
from pandas.testing import assert_frame_equal


def test_compute_rankings_outputs_players_and_histories():
    # Run complete compute_rankings unattended
    ranking_table_tennis.compute_rankings.main()

    # Load output
    output_filename = os.path.join(cfg.io.data_folder, "players.pk")
    players_output = pickle.load(open(output_filename, "rb"))

    # Load expected output
    expected_path = os.path.join(os.path.dirname(__file__), "data_up_to_S2022T04")
    expected_filename = os.path.join(expected_path, "players.pk")
    players_expected = pickle.load(open(expected_filename, "rb"))

    assert_frame_equal(players_output.players_df, players_expected.players_df)
    assert_frame_equal(players_output.history_df, players_expected.history_df)


def test_compute_rankings_outputs_tournaments():
    # Run complete compute_rankings unattended
    # ranking_table_tennis.compute_rankings.main()

    # Load output
    output_filename = os.path.join(cfg.io.data_folder, "tournaments.pk")
    tournaments_output = pickle.load(open(output_filename, "rb"))

    # Load expected output
    expected_path = os.path.join(os.path.dirname(__file__), "data_up_to_S2022T04")
    expected_filename = os.path.join(expected_path, "tournaments.pk")
    tournaments_expected = pickle.load(open(expected_filename, "rb"))

    assert_frame_equal(tournaments_output.tournaments_df, tournaments_expected.tournaments_df)


def test_compute_rankings_outputs_rankings():
    # Run complete compute_rankings unattended
    # ranking_table_tennis.compute_rankings.main()

    # Load output
    output_filename = os.path.join(cfg.io.data_folder, "rankings.pk")
    rankings_output = pickle.load(open(output_filename, "rb"))

    # Load expected output
    expected_path = os.path.join(os.path.dirname(__file__), "data_up_to_S2022T04")
    expected_filename = os.path.join(expected_path, "rankings.pk")
    rankings_expected = pickle.load(open(expected_filename, "rb"))

    assert_frame_equal(rankings_output.ranking_df, rankings_expected.ranking_df)
    assert_frame_equal(rankings_output.rating_details_df, rankings_expected.rating_details_df)
    assert_frame_equal(
        rankings_output.championship_details_df, rankings_expected.championship_details_df
    )
