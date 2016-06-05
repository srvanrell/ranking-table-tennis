# -*- coding: utf-8 -*-

import utils
import models

__author__ = 'sebastian'

# Codigo para inicializar dos orillas

data_folder = "data/"
xlsx_filename = "Liga Dos Orillas 2016 - Categorías Mayores - Partidos.xlsx"
out_filename = "Liga Dos Orillas 2016 - Categorías Mayores - Partidos.xlsx"
players_sheetname = "Jugadores"
ranking_sheetname = "Ranking inicial"
tournaments_key = "Partidos"

# Listing tournament sheetnames by increasing date
tournament_sheetnames = utils.get_sheetnames_by_date(data_folder + xlsx_filename, tournaments_key)

# Loading and completing the players list
players = models.PlayersList()
players.load_list(utils.load_sheet_workbook(data_folder + xlsx_filename, players_sheetname))

# Loading initial ranking and adding new players with 0
ranking = utils.load_ranking_sheet(data_folder + xlsx_filename, ranking_sheetname)

for tournament_sheetname in tournament_sheetnames:
    # Loading tournament info
    tournament = utils.load_tournament_xlsx(data_folder + xlsx_filename, tournament_sheetname)

    for name in tournament.get_players_names():
        if players.get_pid(name) is None:
            association = input("Enter the association of %s:\n" % name)
            city = input("Enter the city of %s:\n" % name)
            # Assign a pid for the new given player and add it to the list
            players.add_new_player(name, association, city)
            print(players[players.get_pid(name)])

        pid = players.get_pid(name)

        if ranking.get_entry(pid) is None:
            initial_rating = int(input("Enter the initial ranting points for %s:\n" % name))
            ranking.add_new_entry(pid, initial_rating)
            print(ranking[pid])

# Saving complete list of players, including new ones
utils.save_sheet_workbook(data_folder + out_filename, players_sheetname,
                          ["PID", "Jugador", "Asociación", "Ciudad", "Último Torneo"],
                          sorted(players.to_list(), key=lambda l: l[1]),
                          True)

# Saving initial rankings for all known players
utils.save_ranking_sheet(data_folder + out_filename, ranking_sheetname, ranking, players, True)
