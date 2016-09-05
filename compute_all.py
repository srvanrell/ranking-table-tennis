import utils
import models
from utils import cfg

__author__ = 'sebastian'

##########################################
# Script to run after preprocess.py
# Input: xlsx tournaments database
#        config.yaml
# Output: xlsx rankings database
#         xlsx log file
#
# It looks for unknown or unrated players.
# It will ask for information not given 
# and saves the result into the same xlsx
##########################################

tournaments_xlsx = cfg["io"]["data_folder"] + cfg["io"]["tournaments_filename"]
rankings_xlsx = cfg["io"]["data_folder"] + cfg["io"]["rankings_filename"]
log_xlsx = cfg["io"]["data_folder"] + cfg["io"]["log_filename"]

# Listing tournament sheetnames by increasing date
tournament_sheetnames = utils.get_sheetnames_by_date(tournaments_xlsx, cfg["sheetname"]["tournaments_key"])

# Loading players info list
players = models.PlayersList()
players.load_list(utils.load_sheet_workbook(tournaments_xlsx, cfg["sheetname"]["players"]))

# Loading initial ranking
initial_ranking = utils.load_ranking_sheet(tournaments_xlsx, cfg["sheetname"]["initial_ranking"])

for tid, tournament_sheetname in enumerate(tournament_sheetnames):
    # Loading tournament info
    tournament = utils.load_tournament_xlsx(tournaments_xlsx, tournament_sheetname)

    old_ranking = models.Ranking("pre_" + tournament.name, tournament.date, tournament.location, tid - 1)

    # Load previous ranking if exists
    if tid-1 >= 0:
        old_ranking = utils.load_ranking_sheet(rankings_xlsx, tournament_sheetnames[tid - 1].replace(
            cfg["sheetname"]["tournaments_key"], cfg["sheetname"]["rankings_key"]))

    # Load initial rankings for new players
    for name in tournament.get_players_names():
        pid = players.get_pid(name)
        if old_ranking.get_entry(pid) is None:
            old_ranking.add_entry(initial_ranking[pid])

    # Create list of players that partipate in the tournament
    pid_participation_list = [players.get_pid(name) for name in tournament.get_players_names()]

    # Get the best round for each player in each category
    # Formatted like: best_rounds[(category, pid)] = best_round_value
    aux_best_rounds = tournament.compute_best_rounds()
    best_rounds = {(categ, players.get_pid(name)): aux_best_rounds[categ, name]
                   for categ, name in aux_best_rounds.keys()}

    # Log current tournament as the last played tournament
    for pid in pid_participation_list:
        players[pid].last_tournament = tid

    # Creating matches list with pid
    matches = []
    for match in tournament.matches:
        if match.winner_name != cfg["aux"]["flag add bonus"]:
            matches.append([players.get_pid(match.winner_name), players.get_pid(match.loser_name),
                            match.round, match.category])

    # TODO make a better way to copy models
    new_ranking = models.Ranking(tournament.name, tournament.date, tournament.location, tid)
    assigned_points_per_match = new_ranking.compute_new_ratings(old_ranking, matches)
    assigned_points_per_best_round = new_ranking.compute_bonus_points(best_rounds)
    assigned_participation_points = new_ranking.add_participation_points(pid_participation_list)

    # Saving new ranking
    utils.save_ranking_sheet(rankings_xlsx, tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                                                         cfg["sheetname"]["rankings_key"]),
                             new_ranking, players, True)

    # Saving points assigned in each match
    points_log_to_save = [[players[winner_pid].name, players[loser_pid].name, winner_points, loser_points]
                          for winner_pid, loser_pid, winner_points, loser_points in assigned_points_per_match]

    utils.save_sheet_workbook(log_xlsx,
                              tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                                           cfg["sheetname"]["rating_details_key"]),
                              [cfg["labels"][key] for key in ["Winner", "Loser", "Winner Points", "Loser Points"]],
                              points_log_to_save, True)

    # Saving points assigned per best round reached and for participation
    points_log_to_save = [[players[pid].name, points, best_round, category] for pid, points, best_round, category
                          in assigned_points_per_best_round]
    participation_points_log_to_save = [[players[pid].name, points, cfg["labels"]["Participation Points"], ""]
                                        for pid, points in assigned_participation_points]

    utils.save_sheet_workbook(log_xlsx,
                              tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                                           cfg["sheetname"]["bonus_details_key"]),
                              [cfg["labels"][key] for key in ["Player", "Bonus Points", "Best Round", "Category"]],
                              points_log_to_save + participation_points_log_to_save, True)
