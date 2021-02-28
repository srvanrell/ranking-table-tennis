#!/usr/bin/env python3

from ranking_table_tennis import utils
from ranking_table_tennis.models import cfg

__author__ = 'sebastian'

###################################################
# Script to run after compute_rankings.py
# Input: xlsx tournaments database
#        xlsx rankings database
#        xlsx log file
#        config.yaml
# Output: temp xlsx to publish a single ranking
###################################################


# Loading all tournament data
tournaments = utils.load_from_pickle(cfg["io"]["tournaments_pickle"])

# Loading players list
players = utils.load_from_pickle(cfg["io"]["players_pickle"])
tournaments.assign_pid_from_players(players)

# Loading initial ranking
rankings = utils.load_from_pickle(cfg["io"]["rankings_pickle"])
initial_tid = cfg["aux"]["initial tid"]

# Will compute all rankings from the beginning by default
tids = [initial_tid] + [tid for tid in tournaments]

print(f"\nNumber\t->\tTournament ID")
for tenum, tid in enumerate(tids[1:], 1):
    print(f"{tenum:d}\t->\t{tid}")

t_num = int(input("Enter the tournament number to publish (look above):\n"))
tid = tids[t_num]

# Get the tid of the previous tournament
prev_tid = tids[tids.index(tid) - 1]

answer = input("\nDo you want to publish to backend online sheets [Y/n]? (press Enter to continue)\n")
upload = answer.lower() != "n"

# Publish formated rating of selected tournament
utils.publish_rating_sheet(tournaments, rankings, players, tid, prev_tid, upload=upload)

# Publish points assigned in each match
utils.publish_rating_details_sheet(tournaments, rankings, players, tid, prev_tid, upload=upload)

# Publish formated masters championship of selected tournament
utils.publish_championship_sheets(tournaments, rankings, players, tid, prev_tid, upload=upload)

# Publish points assigned per best round reached
utils.publish_championship_details_sheet(tournaments, rankings, players, tid, prev_tid, upload=upload)

# Saving complete histories of players
utils.publish_histories_sheet(tournaments, rankings, players, tid, prev_tid, upload=upload)

# Publshing initial_ranking
utils.publish_initial_rating_sheet(tournaments, rankings, players, tid, upload=upload)

# Publish statistics
utils.publish_statistics_sheet(tournaments, rankings, players, tid, prev_tid, upload=upload)

answer = input("\nDo you want to publish to the web [Y/n]? (press Enter to continue)\n")
show_on_web = (answer.lower() != "n") and (t_num > 1)

utils.publish_to_web(tid, show_on_web)

utils.save_raw_ranking(rankings, players, tid)
