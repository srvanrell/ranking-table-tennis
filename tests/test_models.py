from unittest import TestCase

from ranking_table_tennis import models
import pandas as pd
import numpy as np


# class TestPlayers(TestCase):
#     def test_get_pid(self):
#         players = models.Players()
#         players.add_new_player("Roberto, Carlos")
#         print(players)
#         self.fail()


class TestRankingOLD(TestCase):
    def test__points_to_assign_expected_result(self):
        diff_to_test = [0, 25, 50, 100, 150, 200, 300, 400, 500, 1000]
        output_points = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        for diff, points in zip(diff_to_test, output_points):
            rating_winner, rating_loser = 1000 + diff, 1000
            output = [points, points]
            points_to_winner_and_loser = models.Rankings._points_to_assign(
                rating_winner, rating_loser
            )
            self.assertListEqual(points_to_winner_and_loser, output)

    def test__points_to_assign_unexpected_result(self):
        diff_to_test = [0, 25, 50, 100, 150, 200, 300, 400, 500, 1000]
        output_points = [9, 11, 13, 15, 18, 21, 24, 28, 32, 40]
        for diff, points in zip(diff_to_test, output_points):
            rating_winner, rating_loser = 1000, 1000 + diff
            output = [points, points]
            points_to_winner_and_loser = models.Rankings._points_to_assign(
                rating_winner, rating_loser
            )
            self.assertListEqual(points_to_winner_and_loser, output)


class TestTournaments(TestCase):
    def test_compute_best_rounds(self):
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

        best_rounds = tournaments.compute_best_rounds(tid)
        output = {("segunda", "Star, Ringo"): "octavos", ("segunda", "Lennon, John"): "octavos"}

        self.assertDictEqual(best_rounds, output)


class TestRankings(TestCase):
    def test_merge_preserve_left_index(self):
        df1 = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]}, index=[0, 1, 2])
        df2 = pd.DataFrame({"C": [7, 8, 9], "B": [5, 6, 22]}, index=[10, 11, 12])

        df3 = pd.DataFrame({"A": [2, 3], "B": [5, 6], "C": [7, 8]}, index=[1, 2])
        df_inner = models.Rankings.merge_preserve_left_index(df1, df2, on="B", how="inner")
        assert df3.equals(df_inner)

        df4 = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [np.nan, 7, 8]}, index=[0, 1, 2])
        df_left = models.Rankings.merge_preserve_left_index(df1, df2, on="B", how="left")
        assert df4.equals(df_left)

    def test_merge_preserve_left_none_name_index(self):
        df1 = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]}, index=[0, 1, 2])
        df2 = pd.DataFrame({"C": [7, 8, 9], "B": [5, 6, 22]}, index=[10, 11, 12])

        df_inner = models.Rankings.merge_preserve_left_index(df1, df2, on="B", how="left")

        assert df1.index.equals(df_inner.index)
        assert df1.index.name == df_inner.index.name
