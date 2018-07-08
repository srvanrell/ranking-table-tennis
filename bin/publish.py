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

# Listing tournament sheetnames by increasing date
tournament_sheetnames = utils.get_tournament_sheetnames_by_date()

# Loading players info list
players = models.PlayersList()
players.load_list(utils.load_players_sheet())

# Loading initial ranking
initial_ranking = utils.load_ranking_sheet(cfg["sheetname"]["initial_ranking"])

for tid, tournament_sheetname in enumerate(tournament_sheetnames, start=1):
    print("%d\t->\t%s" % (tid, tournament_sheetname))
tid = int(input("Enter the tournament id to publish (look above):\n"))
tournament_sheetname = tournament_sheetnames[tid-1]

# Loading tournament info
tournament = utils.load_tournament_xlsx(tournament_sheetname)
ranking = utils.load_ranking_sheet(tournament_sheetname)

old_ranking = models.Ranking("pre_" + tournament.name, tournament.date, tournament.location, tid - 2)
# Load previous ranking if exists
if tid-1 > 0:
    old_ranking = utils.load_ranking_sheet(tournament_sheetnames[tid - 2])

# Load initial rankings for new players
for entry in ranking:
    if old_ranking.get_entry(entry.pid) is None:
        old_ranking.add_entry(initial_ranking[entry.pid])

answer = input("\nDo you want to publish to temporal online sheets [y/n]? (press Enter to continue)\n")
upload = answer.lower() != "n"

# Publish formated rating of selected tournament
utils.publish_rating_sheet(tournament_sheetname, ranking, players, old_ranking, upload=upload)

# Publish formated championship of selected tournament
utils.publish_championship_sheet(tournament_sheetname, ranking, players, old_ranking, upload=upload)

# Publish points assigned in each match and points assigned per best round reached and for participation
utils.publish_details_sheets(tournament_sheetname, ranking, upload=upload)

# Saving complete histories of players
utils.publish_histories_sheet(ranking, players, tournament_sheetnames, upload=upload)

# Testing publshing initial_ranking
# TODO it's not working
# utils.publish_rating_sheet(tournament_sheetname, initial_ranking, players, initial_ranking, upload=upload)

# Testing statistics publishing
utils.publish_statistics_sheet(tournament_sheetname, ranking, upload=upload)
