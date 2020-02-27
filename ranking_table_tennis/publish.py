#!/usr/bin/env python3

from ranking_table_tennis import utils
from ranking_table_tennis import models
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
tournaments = utils.load_tournaments_sheets()

# Loading players list
players = utils.load_players_sheet()
tournaments.assign_pid_from_players(players)

# Loading initial ranking
rankings = utils.load_rankings()
initial_tid = cfg["aux"]["initial tid"]

# Will compute all rankings from the beginning by default
tids = [initial_tid] + [tid for tid in tournaments]

for tenum, tid in enumerate(tids[1:], 1):
    print(f"{tenum:d}\t->\t{tid}")

t_num = int(input("Enter the tournament id to publish (look above):\n"))
tid = tids[t_num]

# Get the tid of the previous tournament
prev_tid = tids[tids.index(tid) - 1]

print(tid, prev_tid)

answer = input("\nDo you want to publish to temporal online sheets [y/n]? (press Enter to continue)\n")
upload = answer.lower() != "n"

# Publish formated rating of selected tournament
utils.publish_rating_sheet(tournaments, rankings, players, tid, prev_tid, upload=upload)

# Publish formated masters championship of selected tournament
utils.publish_championship_sheets(tournaments, rankings, players, tid, prev_tid, upload=upload)

# Publish points assigned in each match and points assigned per best round reached and for participation
utils.publish_details_sheets(tournaments, rankings, players, tid, prev_tid, upload=upload)

# # Saving complete histories of players
# utils.publish_histories_sheet(ranking, players, tournament_sheetnames, upload=upload)
#
# # Testing publshing initial_ranking
# # TODO it's not working
# # utils.publish_rating_sheet(tournament_sheetname, initial_ranking, players, initial_ranking, upload=upload)
#
# # Publish statistics
# utils.publish_statistics_sheet(tournament_sheetname, ranking, upload=upload)
#
# answer = input("\nDo you want to publish to the web [y/n]? (press Enter to continue)\n")
# show_on_web = answer.lower() != "n"
#
# utils.publish_to_web(ranking, show_on_web)
