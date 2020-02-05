#!/usr/bin/env python3

from ranking_table_tennis import utils
from ranking_table_tennis import models
from ranking_table_tennis.models import cfg

__author__ = 'sebastian'

##########################################
# Script to run after preprocess.py
# It computes rating and points of
# the selected tournament
# Input: xlsx tournaments database
#        config.yaml
# Output: xlsx rankings database
#         xlsx log file
##########################################

log_xlsx = cfg["io"]["data_folder"] + cfg["io"]["log_filename"]

# Loading all tournament data
tournaments = utils.load_tournaments_sheets()

# Loading players list
players = utils.load_players_sheet()
tournaments.assign_pid_from_players(players)

# Loading initial ranking
rankings = utils.load_initial_ranking_sheet()
initial_tid = cfg["aux"]["initial tid"]

# Will compute all rankings from the beginning by default
tids = [initial_tid] + [tid for tid in tournaments]

for tid in tournaments:
    print("==", tid, "==")

    # Get the tid of the previous tournament
    prev_tid = tids[tids.index(tid) - 1]

    # Previous ranking data will be the default for the new ranking
    rankings.initialize_new_ranking(tid, prev_tid)

    # Create list of players that partipate in the tournament
    pid_participation_list = [players.get_pid(name) for name in tournaments.get_players_names(tid)]

    # Get the best round for each player in each category
    # Formatted like: best_rounds[(category, pid)] = best_round_value
    aux_best_rounds = tournaments.compute_best_rounds(tid)
    best_rounds = {(categ, players.get_pid(name)): aux_best_rounds[categ, name]
                   for categ, name in aux_best_rounds.keys()}

    # List of players that didn't play its own category but plyed the higher one
    # Fans category is not considered in this list
    # Old ranking need to be updated so known old players are not misclassified
    rankings.update_categories()
    pid_not_own_category = [pid for pid in pid_participation_list
                            if (rankings[tid, pid, "category"], pid) not in best_rounds
                            and rankings[tid, pid, "category"] != models.categories[-1]]

    assigned_points_per_match = rankings.compute_new_ratings(tid, prev_tid, tournaments, pid_not_own_category)
    assigned_points_per_best_round = rankings.compute_category_points(tid, best_rounds)
    rankings.update_active_players(tid, players, initial_tid)

    # Promote those players indicated in the matches list of the tournament
    rankings.promote_players(tid, tournaments)

    # Substract championship points
    rankings.apply_sanction(tid, tournaments)

    # TODO verify if it is necessary
    rankings.update_categories()
    rankings.compute_championship_points(tid)

#     # Saving new ranking
#     utils.save_ranking_sheet(tournament_sheetname, new_ranking, players)
#
#     # Saving points assigned in each match
#     points_log_to_save = [[players[winner_pid].name + " (%d)" % old_ranking[winner_pid].rating,
#                            players[loser_pid].name + " (%d)" % old_ranking[loser_pid].rating,
#                            old_ranking[winner_pid].rating - old_ranking[loser_pid].rating, winner_points, loser_points,
#                            match_round, match_category]
#                           for winner_pid, loser_pid, winner_points, loser_points, match_round, match_category
#                           in assigned_points_per_match]
#
#     utils.save_sheet_workbook(log_xlsx,
#                               tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
#                                                            cfg["sheetname"]["rating_details_key"]),
#                               [cfg["labels"][key] for key in ["Winner", "Loser", "Difference",
#                                                               "Winner Points", "Loser Points",
#                                                               "Round", "Category"]],
#                               points_log_to_save)
#
#     utils.save_sheet_workbook(log_xlsx,
#                               tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
#                                                            cfg["sheetname"]["bonus_details_key"]),
#                               [cfg["labels"][key] for key in ["Player", "Bonus Points", "Best Round", "Category"]],
#                               points_log_to_save)
#
#     utils.save_statistics(tournament_sheetname, tournament, new_ranking)
