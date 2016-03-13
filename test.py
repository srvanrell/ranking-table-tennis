__author__ = 'sebastian'
# -*- coding: utf-8 -*-

# Codigo para inicializar dos orillas

import utils
import models

players_info_filename = "jugadores_dos_orillas.csv"

tournament_filenames = ["Liga Dos Orillas 2016 - Ranking Mayores - 1er Torneo 2016.csv",
                        "Liga Dos Orillas 2016 - Ranking Mayores - 2do Torneo 2016.csv",
                        "Liga Dos Orillas 2016 - Ranking Mayores - 3er Torneo 2016.csv"
                        ]

for tournament_filename in tournament_filenames:
    # Loading tournament info
    tournament = utils.load_tournament_csv(tournament_filename)

    # Loading and completing the players list
    players = models.PlayersList()
    players.load_list(utils.load_csv(players_info_filename))

    for name in tournament["players"]:
        if players.get_pid(name) is None:
            players.add_new_player(name)
    
    # TODO sort list by name to easily detect duplicates
    utils.save_csv(players_info_filename, 
                   ["PID", "Jugador", "Asociación", "Ciudad"], 
                   players.to_list())

# Loading players list
players = models.PlayersList()
players.load_list(utils.load_csv(players_info_filename))

list_to_save = [[p[0], 0, p[1], p[3]] for p in players.to_list()]

ranking_filename = "Liga Dos Orillas 2016 - Ranking Mayores - inicial.csv"
raw_ranking = utils.load_csv(ranking_filename)

print raw_ranking
ranking = models.Ranking("01/01/2016", "ranking inicial")
ranking.load_list([[r[0], r[1]] for r in raw_ranking])
print ranking

#utils.save_csv(ranking_filename, ["PID", "Rating", "Jugador", "Ciudad"], list_to_save)
#tournament2_filename = "Liga Dos Orillas - Torneos Disputados 2016 - 2do Torneo 2016.csv"
#tournament2 = utils.load_tournament_csv(tournament2_filename)



#ratings = [[pid, 1000, name] for pid, name, asociation in players]

#utils.save_csv("ranking_inicial_dos_orillas.csv", ["player_id", "rating", "name"], ratings)

