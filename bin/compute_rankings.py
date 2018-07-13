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

# Listing tournament sheetnames by increasing date
tournament_sheetnames = utils.get_tournament_sheetnames_by_date()

# Loading players info list
players = models.PlayersList()
players.load_list(utils.load_players_sheet())

# Loading initial ranking
initial_ranking = utils.load_ranking_sheet(cfg["sheetname"]["initial_ranking"])

# Ask for the tournament data to be processed
print("\n0\t->\tCompute all from the beginning")
for tid, tournament_sheetname in enumerate(tournament_sheetnames, start=1):
    print("%d\t->\t%s" % (tid, tournament_sheetname))
tid = int(input("Enter the tournament to compute (look above):\n"))

# Will compute all rankings from the beginning by default
tids = range(1, len(tournament_sheetnames)+1)
if tid != 0:
    tids = [tid]

for tid in tids:
    # Loading tournament info
    tournament_sheetname = tournament_sheetnames[tid-1]  # Start on 1 but list is zero based
    tournament = utils.load_tournament_xlsx(tournament_sheetname)

    old_ranking = models.Ranking("pre_" + tournament.name, tournament.date, tournament.location, tid - 2)

    # Load previous ranking if exists
    if tid-1 > 0:
        old_ranking = utils.load_ranking_sheet(tournament_sheetnames[tid - 2])

    # Load initial rankings for new players
    pid_new_players = []
    for name in tournament.get_players_names():
        pid = players.get_pid(name)
        if old_ranking.get_entry(pid) is None:
            old_ranking.add_entry(initial_ranking[pid])
            pid_new_players.append(pid)

    # Create list of players that partipate in the tournament
    pid_participation_list = [players.get_pid(name) for name in tournament.get_players_names()]

    # Get the best round for each player in each category
    # Formatted like: best_rounds[(category, pid)] = best_round_value
    aux_best_rounds = tournament.compute_best_rounds()
    best_rounds = {(categ, players.get_pid(name)): aux_best_rounds[categ, name]
                   for categ, name in aux_best_rounds.keys()}

    # List of players that didn't play its own category but plyed the higher one
    # Fans category is not considered in this list
    # TODO tid limit may need to be read from config file
    pid_not_own_category = []
    if tid > 5:
        # Old ranking need to be updated so known old players are not misclassified
        if tid > 6:
            old_ranking.update_categories_thresholds(th_first=500, th_second=250)
        pid_not_own_category = [pid for pid in pid_participation_list
                                if (old_ranking[pid].category, pid) not in best_rounds
                                and old_ranking[pid].category != models.categories[-1]]
    # FIXME printing for debugging
    if pid_not_own_category:
        print("\nPlayers that didn't played their own category were identified\n")
    for pid in pid_not_own_category:
        print(tid, old_ranking[pid], players[pid])

    # Creating matches list with pid
    matches = []
    for match in tournament.matches:
        if match.winner_name not in [cfg["aux"]["flag bonus sanction"], cfg["aux"]["flag add bonus"],
                                     cfg["aux"]["flag promotion"]] \
                and match.category != models.categories[-1]:
            matches.append([players.get_pid(match.winner_name), players.get_pid(match.loser_name),
                            match.round, match.category])

    new_ranking = models.Ranking(tournament.name, tournament.date, tournament.location, tid)
    assigned_points_per_match = new_ranking.compute_new_ratings(old_ranking, matches, pid_not_own_category)
    assigned_points_per_best_round = new_ranking.compute_bonus_points(best_rounds)
    assigned_participation_points = new_ranking.add_participation_points(pid_participation_list)

    # Include all known players even if they didn't play in the tournament
    for entry in initial_ranking:
        if new_ranking.get_entry(entry.pid) is None:
            # Only include previously known players, not from future tournaments
            if entry.bonus > 0 or entry.active:
                new_ranking.add_entry(entry)

    # Update categories before saving the new ranking
    initial_active_players = [re.pid for re in initial_ranking if re.active]
    new_ranking.update_active_players(players, initial_active_players)

    # Promote those players indicated in the matches list of the tournament
    # Add or substract bonus points
    for match in tournament.matches:
        if match.winner_name == cfg["aux"]["flag promotion"]:
            new_ranking[players.get_pid(match.loser_name)].category = match.category
        if match.winner_name == cfg["aux"]["flag bonus sanction"]:
            pid_bonus = players.get_pid(match.loser_name)
            new_bonus = new_ranking[pid_bonus].bonus
            old_bonus = old_ranking[pid_bonus].bonus
            new_ranking[pid_bonus].bonus = old_bonus + (new_bonus - old_bonus) * cfg["aux"]["sanction factor"]

            # list_item == [pid, points, best_round, category]
            for list_item in assigned_points_per_best_round:
                if list_item[0] == pid_bonus:
                    list_item[1] *= cfg["aux"]["sanction factor"]

            # list_item == [pid, points]
            for list_item in assigned_participation_points:
                if list_item[0] == pid_bonus:
                    list_item[1] *= cfg["aux"]["sanction factor"]

    # TODO threshold and tid limit may need to be read from config file
    if tid < 6:
        new_ranking.update_categories(n_first=10, n_second=10)
    else:
        new_ranking.update_categories_thresholds(th_first=500, th_second=250)

    # Saving new ranking
    utils.save_ranking_sheet(tournament_sheetname, new_ranking, players)

    # Saving points assigned in each match
    points_log_to_save = [[players[winner_pid].name + " (%d)" % old_ranking[winner_pid].rating,
                           players[loser_pid].name + " (%d)" % old_ranking[loser_pid].rating,
                           old_ranking[winner_pid].rating - old_ranking[loser_pid].rating, winner_points, loser_points,
                           match_round, match_category]
                          for winner_pid, loser_pid, winner_points, loser_points, match_round, match_category
                          in assigned_points_per_match]

    utils.save_sheet_workbook(log_xlsx,
                              tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                                           cfg["sheetname"]["rating_details_key"]),
                              [cfg["labels"][key] for key in ["Winner", "Loser", "Difference",
                                                              "Winner Points", "Loser Points",
                                                              "Round", "Category"]],
                              points_log_to_save)

    # Saving points assigned per best round reached and for participation
    points_log_to_save = [[players[pid].name, points, best_round, category] for pid, points, best_round, category
                          in assigned_points_per_best_round]
    participation_points_log_to_save = [[players[pid].name, points, cfg["labels"]["Participation Points"], ""]
                                        for pid, points in assigned_participation_points if points > 0]

    utils.save_sheet_workbook(log_xlsx,
                              tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                                           cfg["sheetname"]["bonus_details_key"]),
                              [cfg["labels"][key] for key in ["Player", "Bonus Points", "Best Round", "Category"]],
                              points_log_to_save + participation_points_log_to_save)

    utils.save_statistics(tournament_sheetname, tournament, new_ranking)
