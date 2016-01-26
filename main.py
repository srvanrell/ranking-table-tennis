__author__ = 'sebastian'

import utils

# -----------------------------
# Fake list of players (0 to 9)
# ------------------------------
players_list = [[i, "Player %d" % i, "player%d@mail.com" % i] for i in range(10)]
utils.save_csv("lista_jugadores.csv",
               ["player_id", "name", "mail"],
               players_list)


# -------------------------------------------
# Fake list of matches in a single tournament
# -------------------------------------------
# Player 1 win over Player 0
# Player 2 win over Player 1 and Player 0
# and so on ...
#
# match_round can be 'z', 'o', 'q', 's', '2', '1'
# they correspond to zone, octave-finals, quarter-finals, semifinal, second, first
#
# Each match contains winner_id, loser_id, match_round
matches_list = [[i, j, 'q'] for i in range(10) for j in range(i)]
# Creating a csv file with the list of matches
utils.save_csv("lista_partidos.csv",
               ["winner_id", "loser_id", "match_round"],
               matches_list)


# -----------------
# Fake ranking list
# -----------------
# player_id, rating
old_ranking = [[i, 1000+24*i] for i in range(10)]
# Creating a csv file with the old ranking
utils.save_csv("ranking_viejo.csv",
               ["player_id", "rating"],
               old_ranking)


# ---------------------------------------------------------------------------
# Reading files created above to load list_players, list_matches, old_ranking
#
old_ranking = utils.load_csv("ranking_viejo.csv")
players_list = utils.load_csv("lista_jugadores.csv")
matches_list = utils.load_csv("lista_partidos.csv")

print old_ranking

new_ranking = utils.get_new_ranking(old_ranking, matches_list)

print new_ranking


# Saving new ranking
utils.save_csv("ranking_nuevo.csv",
               ["player_id", "rating"],
               new_ranking)

