from unittest import TestCase

from ranking_table_tennis import models
import pandas as pd


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
            points_to_winner_and_loser = models.Rankings._points_to_assign(rating_winner, rating_loser)
            self.assertListEqual(points_to_winner_and_loser, output)

    def test__points_to_assign_unexpected_result(self):
        diff_to_test = [0, 25, 50, 100, 150, 200, 300, 400, 500, 1000]
        output_points = [9, 11, 13, 15, 18, 21, 24, 28, 32, 40]
        for diff, points in zip(diff_to_test, output_points):
            rating_winner, rating_loser = 1000, 1000 + diff
            output = [points, points]
            points_to_winner_and_loser = models.Rankings._points_to_assign(rating_winner, rating_loser)
            self.assertListEqual(points_to_winner_and_loser, output)


class TestTournaments(TestCase):
    def test_compute_best_rounds(self):
        tid = "S2099T01"
        dict_tour_entry = {"sheet_name": "nada", "tournament_name": "nada", "date": "2099 01 01", "location": "nanana",
                           "player_a": "Star, Ringo", "player_b": "Lennon, John", "sets_a": 3, "sets_b": 0,
                           "round": "octavos", "category": "segunda"}
        tour_df = pd.DataFrame(dict_tour_entry, index=[0])
        tournaments = models.Tournaments(tour_df)

        best_rounds = tournaments.compute_best_rounds(tid)
        output = {('segunda', 'Star, Ringo'): 'octavos', ('segunda', 'Lennon, John'): 'octavos'}

        self.assertDictEqual(best_rounds, output)
