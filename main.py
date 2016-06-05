import utils
import models

__author__ = 'sebastian'

data_folder = "data/"
xlsx_filename = "Liga Dos Orillas 2016 - Categorías Mayores - Partidos.xlsx"
out_filename = "Liga Dos Orillas 2016 - Categorías Mayores - Rankings crudos.xlsx"
log_filename = "log.xlsx"
players_sheetname = "Jugadores"
ranking_sheetname = "Ranking inicial"
tournaments_key = "Partidos"

# Listing tournament sheetnames by increasing date
tournament_sheetnames = utils.get_sheetnames_by_date(data_folder + xlsx_filename, tournaments_key)

# Loading players info list
players = models.PlayersList()
players.load_list(utils.load_sheet_workbook(data_folder + xlsx_filename, players_sheetname))

# Loading initial ranking
initial_ranking = utils.load_ranking_sheet(data_folder + xlsx_filename, ranking_sheetname)

for i, tournament_sheetname in enumerate(tournament_sheetnames):

    tournament = utils.load_tournament_xlsx(data_folder + xlsx_filename, tournament_sheetname)

    old_ranking = models.Ranking("pre_" + tournament.name, tournament.date, tournament.location)

    # Load previous ranking if exists
    if i-1 >= 0:
        old_ranking = utils.load_ranking_sheet(data_folder + out_filename,
                                               tournament_sheetnames[i-1].replace(tournaments_key, "Ranking"))

    # Load initial rankings for new players
    for name in tournament.get_players_names():
        pid = players.get_pid(name)
        if old_ranking.get_entry(pid) is None:
            old_ranking.add_entry(initial_ranking[pid])

    # Create list of players that partipate in the tournament
    pid_participation_list = [players.get_pid(name) for name in tournament.get_players_names()]

    # Creating matches list with pid
    matches = []
    for match in tournament.matches:
        if match.winner_name == "to_add_bonus_points":
            matches.append([-1, players.get_pid(match.loser_name),
                            match.round, match.category])
        else:
            matches.append([players.get_pid(match.winner_name), players.get_pid(match.loser_name),
                            match.round, match.category])

    # TODO make a better way to copy models
    new_ranking = models.Ranking(tournament.name, tournament.date, tournament.location)
    assigned_points_per_match = new_ranking.compute_new_ratings(old_ranking, matches)
    assigned_points_per_best_round = new_ranking.compute_bonus_points(matches)
    assigned_participation_points = new_ranking.add_participation_points(pid_participation_list)

    # Saving new ranking
    utils.save_ranking_sheet(data_folder + out_filename, tournament_sheetname.replace(tournaments_key, "Ranking"),
                             new_ranking, players, True)

    # Saving points assigned in each match
    points_log_to_save = [[players[winner_pid].name, players[loser_pid].name, winner_points, loser_points]
                          for winner_pid, loser_pid, winner_points, loser_points in assigned_points_per_match]

    utils.save_sheet_workbook(data_folder + log_filename,
                              tournament_sheetname.replace(tournaments_key, "Detalles Rating"),
                              ["Ganador", "Perdedor", "Puntos Ganador", "Puntos Perdedor"],
                              points_log_to_save, True)

    # Saving points assigned per best round reached and for participation
    points_log_to_save = [[players[pid].name, points, best_round, category] for pid, points, best_round, category
                          in assigned_points_per_best_round]
    participation_points_log_to_save = [[players[pid].name, points, "Puntos por participar", ""] for pid, points
                                        in assigned_participation_points]

    utils.save_sheet_workbook(data_folder + log_filename,
                              tournament_sheetname.replace(tournaments_key, "Detalles Bonus"),
                              ["Jugador", "Puntos Bonus", "Mejor Ronda", "Categoría"],
                              points_log_to_save + participation_points_log_to_save, True)
