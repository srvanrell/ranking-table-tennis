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

    utils.save_csv(players_info_filename, 
                   ["PID", "Nombre", "Asociación", "Ciudad"], 
                   players.to_list())


#tournament2_filename = "Liga Dos Orillas - Torneos Disputados 2016 - 2do Torneo 2016.csv"
#tournament2 = utils.load_tournament_csv(tournament2_filename)


#allplayers = list(set(tournament1["players"]).union(set(tournament2["players"])))

#players = [[num+1, player, "Asociación"] for num, player in enumerate(allplayers)]
#ratings = [[pid, 1000, name] for pid, name, asociation in players]

#utils.save_csv("jugadores_dos_orillas.csv", ["player_id", "name", "association"], players)
#utils.save_csv("ranking_inicial_dos_orillas.csv", ["player_id", "rating", "name"], ratings)

