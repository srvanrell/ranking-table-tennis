# import sys
# print sys.path

import utils
import models

data_folder = "../data/"

league_filename = "(nueva versión) Liga Dos Orillas 2016 - Categorías Mayores.xlsx"

# utils.load_league_workbook(data_folder + league_filename)

a = utils.load_sheet_workbook(data_folder + league_filename, "Jugadores")

# Loading players info list
players = models.PlayersList()
players.load_list(a)

# print(players)

# Loading initial ranking
initial_ranking = models.Ranking()

raw_ranking = utils.load_sheet_workbook(data_folder + league_filename, "Ranking inicial")
initial_ranking.load_list([[r[0], r[2], r[3]] for r in raw_ranking])

# print(initial_ranking)

snames = utils.get_ordered_sheet_names(data_folder + league_filename, "Partidos")
# print(snames)

to_order = []
for i, s in enumerate(snames):
    t = utils.load_tournament_xlsx(data_folder + league_filename, s)
    to_order.append((6 - i, t["date"]))

print(sorted(to_order, key=lambda p: p[1]))

utils.save_sheet_workbook(data_folder + "pruebaa.xlsx", "nombre", ["aa", "bb"], [[1, 2], ["e", 4]], overwrite=True)
