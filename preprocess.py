# -*- coding: utf-8 -*-

import utils
import models

__author__ = 'sebastian'

# Codigo para inicializar dos orillas

data_folder = "data/"

tournament_filenames = ["Liga Dos Orillas 2016 - Categorías Mayores - Partidos 1er Torneo 2016.csv",
                        "Liga Dos Orillas 2016 - Categorías Mayores - Partidos 2do Torneo 2016.csv",
                        "Liga Dos Orillas 2016 - Categorías Mayores - Partidos 3er Torneo 2016.csv"
                        ]
players_info_filename = "Liga Dos Orillas 2016 - Categorías Mayores - Jugadores.csv"
initial_ranking_filename = "Liga Dos Orillas 2016 - Categorías Mayores - Ranking inicial.csv"

# Loading and completing the players list
players = models.PlayersList()
players.load_list(utils.load_csv(data_folder + players_info_filename))

# Loading initial ranking and adding new players with 0
raw_ranking = utils.load_csv(data_folder + initial_ranking_filename)
ranking = models.Ranking("01/01/2016", "ranking inicial")
ranking.load_list([[r[0], r[1]] for r in raw_ranking])

for tournament_filename in tournament_filenames:
    # Loading tournament info
    tournament = utils.load_tournament_csv(data_folder + tournament_filename)

    for name in tournament["players"]:
        if players.get_pid(name) is None:
            players.add_new_player(name)

        pid = players.get_pid(name)

        if ranking.get_entry(pid) is None:
            ranking.add_new_entry(pid)
            print "WARNING: Added player without rating: %s (%d)" % (name, pid)

# Saving complete list of players, including new ones
utils.save_csv(data_folder + players_info_filename,
               ["PID", "Jugador", "Asociación", "Ciudad"],
               sorted(players.to_list(), key=lambda l: l[1]))

# Saving initial rankings for all known players
list_to_save = [[p.pid, ranking[p.pid].rating, p.name, p.association, p.city] for p in players]
utils.save_csv(data_folder + initial_ranking_filename,
               ["PID", "Rating", "Jugador", "Asociación", "Ciudad"],
               sorted(list_to_save, key=lambda l: l[1], reverse=True))
