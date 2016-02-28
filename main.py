__author__ = 'sebastian'
# -*- coding: utf-8 -*-

import utils

# ---------------------------------------------------------------------------
# Reading files created with create_csv_files.py
#
old_ranking = utils.load_csv("ranking_inicial_dos_orillas.csv")
players_list = utils.load_csv("jugadores_dos_orillas.csv")

tournament1_filename = "Liga Dos Orillas - Torneos Disputados 2016 - 1er Torneo 2016.csv"
tournament1 = utils.load_tournament_csv(tournament1_filename)

partidos = []
for winner_name, loser_name, match_round, category in tournament1["matches"]:
    partidos.append([utils.name2playerid(winner_name, players_list)-1,
                    utils.name2playerid(loser_name, players_list)-1,
                    match_round])


matches_filename1 = "partidos_torneo1_dosorillas2016.csv"
utils.save_csv(matches_filename1,
               ["winner", "loser", "match_round"],
               partidos)

matches_list = utils.load_csv(matches_filename1)

new_ranking = utils.get_new_ranking(old_ranking, matches_list)

# Saving new ranking
utils.save_csv("ranking_torneo1_dos_orillas.csv",
               ["player_id", "rating", "name"],
               new_ranking)


# Calculos del segundo torneo

old_ranking = utils.load_csv("ranking_torneo1_dos_orillas.csv")
players_list = utils.load_csv("jugadores_dos_orillas.csv")

tournament2_filename = "Liga Dos Orillas - Torneos Disputados 2016 - 2do Torneo 2016.csv"
tournament2 = utils.load_tournament_csv(tournament2_filename)

partidos = []
for winner_name, loser_name, match_round, rrr in tournament2["matches"]:
    partidos.append([utils.name2playerid(winner_name, players_list)-1,
                    utils.name2playerid(loser_name, players_list)-1,
                    match_round])


matches_filename2 = "partidos_torneo2_dosorillas2016.csv"
utils.save_csv(matches_filename2,
               ["winner", "loser", "match_round"],
               partidos)

matches_list = utils.load_csv(matches_filename2)

# print old_ranking

new_ranking = utils.get_new_ranking(old_ranking, matches_list)

# print new_ranking


# Saving new ranking
utils.save_csv("ranking_torneo2_dos_orillas.csv",
               ["player_id", "rating", "name"],
               new_ranking)

