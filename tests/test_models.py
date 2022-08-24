import numpy as np
import pandas as pd

from ranking_table_tennis import models
from ranking_table_tennis.configs import ConfigManager


def test_points_to_assign_expected_result():
    ConfigManager().set_current_config(date="220101")
    diff_to_test = [0, 25, 50, 100, 150, 200, 300, 400, 500, 1000]
    output_points = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    for diff, points in zip(diff_to_test, output_points):
        rating_winner, rating_loser = 1000 + diff, 1000
        output = (points, points)
        points_to_winner_and_loser = models.Rankings()._points_to_assign(
            rating_winner, rating_loser
        )
        assert points_to_winner_and_loser == output


def test_points_to_assign_unexpected_result():
    ConfigManager().set_current_config(date="220101")
    diff_to_test = [0, 25, 50, 100, 150, 200, 300, 400, 500, 1000]
    output_points = [9, 11, 13, 15, 18, 21, 24, 28, 32, 40]
    for diff, points in zip(diff_to_test, output_points):
        rating_winner, rating_loser = 1000, 1000 + diff
        output = (points, points)
        points_to_winner_and_loser = models.Rankings()._points_to_assign(
            rating_winner, rating_loser
        )
        assert points_to_winner_and_loser == output


def test_compute_best_rounds():
    tid = "S2099T01"
    dict_tour_entry = {
        "sheet_name": "nada",
        "tournament_name": "nada",
        "date": "2099 01 01",
        "location": "nanana",
        "player_a": "Star, Ringo",
        "player_b": "Lennon, John",
        "sets_a": 3,
        "sets_b": 0,
        "round": "octavos",
        "category": "segunda",
    }
    tour_df = pd.DataFrame(dict_tour_entry, index=[0])
    tournaments = models.Tournaments(tour_df)
    # Hack to fix this test
    tournaments.tournaments_df.winner_pid = 100
    tournaments.tournaments_df.loser_pid = 200

    best_rounds = tournaments.compute_best_rounds(tid, players=None)
    expected_output = pd.DataFrame(
        {
            "name": ["Star, Ringo", "Lennon, John"],
            "pid": [100, 200],
            "category": ["segunda", "segunda"],
            "best_round": ["octavos", "octavos"],
        }
    )

    assert best_rounds.equals(expected_output)


def test_merge_preserve_left_index():
    df1 = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]}, index=[0, 1, 2])
    df2 = pd.DataFrame({"C": [7, 8, 9], "B": [5, 6, 22]}, index=[10, 11, 12])

    df3 = pd.DataFrame({"A": [2, 3], "B": [5, 6], "C": [7, 8]}, index=[1, 2])
    df_inner = models.Rankings.merge_preserve_left_index(df1, df2, on="B", how="inner")
    assert df3.equals(df_inner)

    df4 = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [np.nan, 7, 8]}, index=[0, 1, 2])
    df_left = models.Rankings.merge_preserve_left_index(df1, df2, on="B", how="left")
    assert df4.equals(df_left)


def test_merge_preserve_left_none_name_index():
    df1 = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]}, index=[0, 1, 2])
    df2 = pd.DataFrame({"C": [7, 8, 9], "B": [5, 6, 22]}, index=[10, 11, 12])

    df_inner = models.Rankings.merge_preserve_left_index(df1, df2, on="B", how="left")

    assert df1.index.equals(df_inner.index)
    assert df1.index.name == df_inner.index.name
