#!/usr/bin/env python3

from ranking_table_tennis import utils
from ranking_table_tennis import models
from ranking_table_tennis.utils import cfg

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

    # Creating matches list with pid
    matches = []
    for match in tournament.matches:
        if match.winner_name not in [cfg["aux"]["flag add bonus"], cfg["aux"]["flag promotion"]] \
                and match.category != models.categories[-1]:
            matches.append([players.get_pid(match.winner_name), players.get_pid(match.loser_name),
                            match.round, match.category])

    # TODO make a better way to copy models
    new_ranking = models.Ranking(tournament.name, tournament.date, tournament.location, tid)
    assigned_points_per_match = new_ranking.compute_new_ratings(old_ranking, matches)
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
    for match in tournament.matches:
        if match.winner_name == cfg["aux"]["flag promotion"]:
            new_ranking[players.get_pid(match.loser_name)].category = match.category

    if tid == 1:
        new_ranking.update_categories(n_first=12, n_second=16)
    else:
        new_ranking.update_categories(n_first=10, n_second=10)

    # Saving new ranking
    utils.save_ranking_sheet(tournament_sheetname, new_ranking, players)

    # Saving points assigned in each match
    points_log_to_save = [[players[winner_pid].name + " (%d)" % old_ranking[winner_pid].rating,
                           players[loser_pid].name + " (%d)" % old_ranking[loser_pid].rating,
                           old_ranking[winner_pid].rating - old_ranking[loser_pid].rating, winner_points, loser_points]
                          for winner_pid, loser_pid, winner_points, loser_points in assigned_points_per_match]

    utils.save_sheet_workbook(log_xlsx,
                              tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                                           cfg["sheetname"]["rating_details_key"]),
                              [cfg["labels"][key] for key in ["Winner", "Loser", "Difference",
                                                              "Winner Points", "Loser Points"]],
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
