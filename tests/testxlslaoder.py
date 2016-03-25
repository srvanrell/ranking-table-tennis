# -*- coding: utf-8 -*-

import utils
import models

data_folder = "../data/"

league_filename = "Liga Dos Orillas 2016 - Categorías Mayores.xlsx"

# utils.load_league_workbook(data_folder + league_filename)

a = utils.load_sheet_workbook(data_folder + league_filename, "Jugadores")

# Loading players info list
players = models.PlayersList()
players.load_list(a)

print players.to_list()

