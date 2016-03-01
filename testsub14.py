__author__ = 'sebastian'
# -*- coding: utf-8 -*-

# Codigo para inicializar dos orillas

import utils

tournament1_filename = "Liga Dos Orillas - Torneos Disputados 2016 - 1er Torneo 2016 sub14.csv"
tournament2_filename = "Liga Dos Orillas - Torneos Disputados 2016 - 2do Torneo 2016 sub14.csv"

tournament1 = utils.load_tournament_csv(tournament1_filename)
tournament2 = utils.load_tournament_csv(tournament2_filename)

allplayers = list(set(tournament1["players"]).union(set(tournament2["players"])))

players = [[num+1, player, "Asociación"] for num, player in enumerate(allplayers)]
ratings = [[pid, 500, name] for pid, name, asociation in players]

utils.save_csv("jugadores_sub14_dos_orillas.csv", ["player_id", "name", "association"], players)
utils.save_csv("ranking_inicial_sub14_dos_orillas.csv", ["player_id", "rating", "name"], ratings)

