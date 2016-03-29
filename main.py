import utils
import models

__author__ = 'sebastian'

data_folder = "data/"
xlsx_filename = "(nueva versión) Liga Dos Orillas 2016 - Categorías Mayores.xlsx"
out_filename = "prueba.xlsx"
log_filename = "log.xlsx"
players_sheetname = "Jugadores"
ranking_sheetname = "Ranking inicial"
tournament_sheetnames = ["Partidos 1er Torneo 2016",
                         "Partidos 2do Torneo 2016",
                         "Partidos 3er Torneo 2016"
                         ]

players_info_filename = "Liga Dos Orillas 2016 - Categorías Mayores - Jugadores.csv"
ranking_filename = "Liga Dos Orillas 2016 - Categorías Mayores - Ranking inicial.csv"

tournament_filenames = ["Liga Dos Orillas 2016 - Categorías Mayores - Partidos 1er Torneo 2016.csv",
                        "Liga Dos Orillas 2016 - Categorías Mayores - Partidos 2do Torneo 2016.csv",
                        "Liga Dos Orillas 2016 - Categorías Mayores - Partidos 3er Torneo 2016.csv"
                        ]

# Loading players info list
players = models.PlayersList()
# players.load_list(utils.load_csv(data_folder + players_info_filename))
players.load_list(utils.load_sheet_workbook(data_folder + xlsx_filename, players_sheetname))

# Loading initial ranking
initial_ranking = models.Ranking()
# initial_ranking.load_list(utils.load_ranking_csv(data_folder + ranking_filename))
initial_ranking.load_list(utils.load_ranking_sheet(data_folder + xlsx_filename, ranking_sheetname))

for i, tournament_sheetname in enumerate(tournament_sheetnames):

    # tournament = utils.load_tournament_csv(data_folder + tournament_filename)
    tournament = utils.load_tournament_xlsx(data_folder + xlsx_filename, tournament_sheetname)

    old_ranking = models.Ranking("old_" + tournament["name"],
                                 tournament["date"], tournament["location"])

    # Load previous ranking if exists
    if i-1 >= 0:
        old_ranking_list = utils.load_ranking_sheet(data_folder + xlsx_filename,
                                                    tournament_sheetnames[i-1].replace("Partidos", "Ranking"))
        # old_ranking_list = utils.load_ranking_csv(data_folder + tournament_filenames[i-1].replace("Partidos", "Ranking"))
        old_ranking.load_list(old_ranking_list)

    # Load initial rankings for new players
    for name in tournament["players"]:
        pid = players.get_pid(name)
        if old_ranking.get_entry(pid) is None:
            old_ranking.add_entry(initial_ranking[pid])

    # Creating matches list with pid
    matches = []
    for winner_name, loser_name, match_round, category in tournament["matches"]:
        matches.append([players.get_pid(winner_name),
                        players.get_pid(loser_name),
                        match_round, category])

    # TODO make a better way to copy models
    new_ranking = models.Ranking(tournament["name"], tournament["date"], tournament["location"])
    new_ranking.tournament_name.replace("old_", "")
    assigned_points_per_match = new_ranking.compute_new_ratings(old_ranking, matches)
    assigned_points_per_best_round = new_ranking.compute_bonus_points(matches)

    # Saving new ranking
    list_to_save = [[e.pid, e.get_total(), e.rating, e.bonus, players[e.pid].name, players[e.pid].association,
                     players[e.pid].city] for e in new_ranking]

    # utils.save_sheet_workbook(data_folder + out_filename, tournament_sheetname.replace("Partidos", "Ranking"),
    #                     ["PID", "Total puntos", "Nivel de juego", "Puntos bonus", "Jugador", "Asociación", "Ciudad"],
    #                           sorted(list_to_save, key=lambda l: l[1], reverse=True))
    utils.save_ranking_sheet(data_folder + out_filename, tournament_sheetname.replace("Partidos", "Ranking"),
                             new_ranking, players)
    # utils.save_csv(data_folder + tournament_filename.replace("Partidos", "Ranking"),
    #                ["PID", "Total puntos", "Nivel de juego", "Puntos bonus", "Jugador", "Asociación", "Ciudad"],
    #                sorted(list_to_save, key=lambda l: l[1], reverse=True))

    # Saving points assigned in each match
    points_log_to_save = [[players[winner_pid].name, players[loser_pid].name, winner_points, loser_points]
                          for winner_pid, loser_pid, winner_points, loser_points in assigned_points_per_match]

    utils.save_sheet_workbook(data_folder + log_filename, tournament_sheetname.replace("Partidos", "Detalles Rating"),
                              ["Ganador", "Perdedor", "Puntos Ganador", "Puntos Perdedor"],
                              points_log_to_save)

    # utils.save_csv(data_folder + tournament_filename.replace("Partidos", "Detalles Puntos Rating"),
    #                ["Ganador", "Perdedor", "Puntos Ganador", "Puntos Perdedor"],
    #                points_log_to_save)

    # Saving points assigned per best round reached
    points_log_to_save = [[players[pid].name, points, best_round, category] for pid, points, best_round, category
                          in assigned_points_per_best_round]

    utils.save_sheet_workbook(data_folder + log_filename, tournament_sheetname.replace("Partidos", "Detalles Bonus"),
                              ["Jugador", "Puntos Bonus", "Mejor Ronda", "Categoría"],
                              points_log_to_save)

    # utils.save_csv(data_folder + tournament_filename.replace("Partidos", "Detalles Puntos Bonus"),
    #                ["Jugador", "Puntos Bonus", "Mejor Ronda", "Categoría"],
    #                points_log_to_save)
