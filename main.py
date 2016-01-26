__author__ = 'sebastian'

import utils

# ---------------------------------------------------------------------------
# Reading files created with create_csv_files.py
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

