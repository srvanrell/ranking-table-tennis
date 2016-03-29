# -*- coding: utf-8 -*-

import utils
import models

__author__ = 'sebastian'

# Codigo para inicializar dos orillas

data_folder = "data/"
xlsx_filename = "Liga Dos Orillas 2016 - Categorías Mayores - excel.xlsx"
out_filename = "Liga Dos Orillas 2016 - Categorías Mayores - excel.xlsx"
players_sheetname = "Jugadores"
ranking_sheetname = "Ranking inicial"
tournament_sheetnames = ["Partidos 1er Torneo 2016",
                         "Partidos 2do Torneo 2016",
                         "Partidos 3er Torneo 2016"
                         ]

tournament_filenames = ["Liga Dos Orillas 2016 - Categorías Mayores - Partidos 1er Torneo 2016.csv",
                        "Liga Dos Orillas 2016 - Categorías Mayores - Partidos 2do Torneo 2016.csv",
                        "Liga Dos Orillas 2016 - Categorías Mayores - Partidos 3er Torneo 2016.csv"
                        ]
players_info_filename = "Liga Dos Orillas 2016 - Categorías Mayores - Jugadores.csv"
initial_ranking_filename = "Liga Dos Orillas 2016 - Categorías Mayores - Ranking inicial.csv"

# Loading and completing the players list
players = models.PlayersList()
# players.load_list(utils.load_csv(data_folder + players_info_filename))
players.load_list(utils.load_sheet_workbook(data_folder + xlsx_filename, players_sheetname))


# Loading initial ranking and adding new players with 0
# raw_ranking = utils.load_csv(data_folder + initial_ranking_filename)
raw_ranking = utils.load_sheet_workbook(data_folder + xlsx_filename, ranking_sheetname)
ranking_list = [[rr[0], rr[2], rr[3]] for rr in raw_ranking]
ranking = models.Ranking("ranking inicial", "01/01/2016", "no aplica")
ranking.load_list(ranking_list)

for tournament_sheetname in tournament_sheetnames:
    # Loading tournament info
    # tournament = utils.load_tournament_csv(data_folder + tournament_filename)
    tournament = utils.load_tournament_xlsx(data_folder + xlsx_filename, tournament_sheetname)

    for name in tournament["players"]:
        if players.get_pid(name) is None:
            players.add_new_player(name)

        pid = players.get_pid(name)

        if ranking.get_entry(pid) is None:
            ranking.add_new_entry(pid)
            print("WARNING: Added player without rating: %s (%d)" % (name, pid))

# Saving complete list of players, including new ones
# utils.save_csv(data_folder + players_info_filename,
#                ["PID", "Jugador", "Asociación", "Ciudad"],
#                sorted(players.to_list(), key=lambda l: l[1]))

utils.save_sheet_workbook(data_folder + out_filename, players_sheetname,
                          ["PID", "Jugador", "Asociación", "Ciudad"],
                          sorted(players.to_list(), key=lambda l: l[1]),
                          True)

# Saving initial rankings for all known players
list_to_save = [[p.pid, ranking[p.pid].get_total(), ranking[p.pid].rating, ranking[p.pid].bonus,
                 p.name, p.association, p.city] for p in players]

# utils.save_sheet_workbook(data_folder + out_filename, ranking_sheetname,
#                           ["PID", "Total puntos", "Nivel de juego", "Puntos bonus", "Jugador", "Asociación", "Ciudad"],
#                           sorted(list_to_save, key=lambda l: l[1], reverse=True))
utils.save_ranking_sheet(data_folder + out_filename, ranking_sheetname, ranking, players, True)

# utils.save_csv(data_folder + initial_ranking_filename,
#                ["PID", "Total puntos", "Nivel de juego", "Puntos bonus", "Jugador", "Asociación", "Ciudad"],
#                sorted(list_to_save, key=lambda l: l[1], reverse=True))
