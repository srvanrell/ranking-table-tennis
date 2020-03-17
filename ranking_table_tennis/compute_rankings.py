#!/usr/bin/env python3

from ranking_table_tennis import utils
from ranking_table_tennis import models
from ranking_table_tennis.models import cfg

import time

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

# Loading all tournament data
tournaments = utils.load_from_pickle(cfg["io"]["tournaments_pickle"])

# Loading players list
players = utils.load_from_pickle(cfg["io"]["players_pickle"])
tournaments.assign_pid_from_players(players)

# Loading initial ranking
t0 = time.time()
rankings = utils.load_initial_ranking_sheet()
initial_tid = cfg["aux"]["initial tid"]
t1 = time.time()
print("Load initial ranking:", t1-t0)

# Will compute all rankings from the beginning by default
tids = [initial_tid] + [tid for tid in tournaments]

for tid in tournaments:
    print("==", tid, "==")

    # Get the tid of the previous tournament
    prev_tid = tids[tids.index(tid) - 1]

    # Previous ranking data will be the default for the new ranking
    t0 = time.time()
    rankings.initialize_new_ranking(tid, prev_tid)
    t1 = time.time()
    print("Initialize new rankings:", t1 - t0)

    # Create list of players that partipate in the tournament
    t0 = time.time()
    pid_participation_list = [players.get_pid(name) for name in tournaments.get_players_names(tid)]
    t1 = time.time()
    print("PID participation list:", t1 - t0)

    # Get the best round for each player in each category
    t0 = time.time()
    best_rounds = tournaments.compute_best_rounds(tid, players)
    t1 = time.time()
    print("Compute best round:", t1 - t0)

    # List of players that didn't play its own category but plyed the higher one
    # Fans category is not considered in this list
    # Old ranking need to be updated so known old players are not misclassified
    t0 = time.time()
    rankings.update_categories()
    t1 = time.time()
    print("Update categories:", t1 - t0)
    pid_not_own_category = [pid for pid in pid_participation_list
                            if best_rounds[(best_rounds.pid == pid) &
                                           (best_rounds.category == rankings[tid, pid, "category"])].empty
                            and rankings[tid, pid, "category"] != models.categories[-1]]

    t0 = time.time()
    rankings.compute_new_ratings(tid, prev_tid, tournaments, pid_not_own_category)
    t1 = time.time()
    print("compute new ratings:", t1 - t0)
    t0 = time.time()
    assigned_points_per_best_round = rankings.compute_category_points(tid, best_rounds)
    t1 = time.time()
    print("compute category points:", t1 - t0)
    t0 = time.time()
    rankings.update_active_players(tid, players, initial_tid)
    t1 = time.time()
    print("Update active players:", t1 - t0)

    # Promote those players indicated in the matches list of the tournament
    t0 = time.time()
    rankings.promote_players(tid, tournaments)
    t1 = time.time()
    print("promote:", t1 - t0)

    # Substract championship points
    t0 = time.time()
    rankings.apply_sanction(tid, tournaments)
    t1 = time.time()
    print("apply sanction:", t1 - t0)

    # TODO verify if it is necessary
    t0 = time.time()
    rankings.update_categories()
    t1 = time.time()
    print("Update categories:", t1 - t0)
    t0 = time.time()
    rankings.compute_championship_points(tid)
    t1 = time.time()
    print("Compute championship points:", t1 - t0)

t0 = time.time()
utils.save_to_pickle(players=players, tournaments=tournaments, rankings=rankings)
t1 = time.time()
print("Save rankings:", t1 - t0)
