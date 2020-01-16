#!/usr/bin/env python3

from ranking_table_tennis import utils
from ranking_table_tennis import models
from ranking_table_tennis.models import cfg
from urllib import request

__author__ = 'sebastian'

##########################################
# Script to run before computing_all.py
# Input: xlsx tournaments database
#        config.yaml
# Output: xlsx tournaments database
#
# It looks for unknown or unrated players.
# It will ask for information not given 
# and saves the result into the same xlsx
##########################################

xlsx_file = cfg["io"]["data_folder"] + cfg["io"]["tournaments_filename"]

# retrieve = input("Do you want to retrieve online sheet [Y/n]? (press Enter to continue)\n")
# if retrieve.lower() != "n":
#     print("Downloading and saving %s\n" % xlsx_file)
#     request.urlretrieve(cfg["io"]["tournaments_gdrive"], xlsx_file)

# Listing tournament sheetnames by increasing date
tournaments_df = utils.get_tournaments_df()

print(tournaments_df)
print(tournaments_df.dtypes)

# Loading players list
players_df = utils.get_players_df()

print(players_df)
print(players_df.dtypes)

# Loading initial ranking and adding new players with 0
# ranking = utils.load_ranking_sheet(cfg["sheetname"]["initial_ranking"])

# # Loading temp ranking and players. It will be deleted after a successful preprocessing
# players_temp, ranking_temp = utils.load_temp_players_ranking()
#
# for tid, tournament_sheetname in enumerate(tournament_sheetnames, start=1):
#     # Loading tournament info
#     tournament = utils.load_tournament_xlsx(tournament_sheetname)
#
#
#     for name in tournament.get_players_names():
#         unknown_player = False
#         if players.get_pid(name) is None:
#             if players_temp.get_pid(name) is None:
#                 unknown_player = True
#                 association = input("Enter the association of %s: (optional field)\n" % name)
#                 city = input("Enter the city of %s: (optional field)\n" % name)
#                 # Assign a pid for the new given player and add it to the list
#                 players.add_new_player(name, association, city)
#                 # Save a temp player to resume preprocessing, if necessary
#                 players_temp.add_player(players[players.get_pid(name)])
#             else:
#                 print(">>>>\tUNCOMPLETE preprocessing detected. Resuming...")
#                 players.add_player(players_temp[players_temp.get_pid(name)])
#             print(players[players.get_pid(name)])
#
#         pid = players.get_pid(name)
#
#         if ranking.get_entry(pid) is None:
#             if ranking_temp.get_entry(pid) is None:
#                 unknown_player = True
#                 initial_rating = int(input("Enter the initial rating points for %s:\n" % name))
#                 ranking.add_new_entry(pid, initial_rating)
#                 # Save a temp ranking of the player to resume preprocessing, if necessary
#                 ranking_temp.add_entry(ranking[pid])
#             else:
#                 print(">>>>\tUNCOMPLETE preprocessing detected. Resuming...")
#                 ranking.add_entry(ranking_temp[pid])
#             print(ranking[pid])
#
#         if ranking[pid].category is "":
#             if ranking_temp[pid].category is "":
#                 unknown_player = True
#                 for option, category in enumerate(models.categories, start=1):
#                     print("%d\t->\t%s" % (option, category))
#                 selected_category = int(input("Enter the initial category (pick a number above) for %s:\n" % name))
#                 ranking[pid].category = models.categories[selected_category-1]
#                 # Save a temp ranking of the player to resume preprocessing, if necessary
#                 ranking_temp[pid].category = ranking[pid].category
#             else:
#                 print(">>>>\tUNCOMPLETE preprocessing detected. Resuming...")
#                 ranking[pid].category = ranking_temp[pid].category
#             print(ranking[pid])
#
#         if unknown_player:
#             retrieve = input("press Enter to continue or Ctrl+C to forget last player data\n")
#             utils.save_temp_players_ranking(players_temp, ranking_temp)
#
#     # Get the best round for each player in each category
#     # Formatted like: best_rounds[(category, pid)] = best_round_value
#     aux_best_rounds = tournament.compute_best_rounds()
#     best_rounds = {(categ, players.get_pid(name)): aux_best_rounds[categ, name]
#                    for categ, name in aux_best_rounds.keys()}
#
#     # Log current tournament as the last played tournament
#     # Also, best rounds reached in each category are saved into corresponding history
#     players.update_histories(tid, best_rounds)
#
# # Update the online version
# answer = input("\nDo you want to update online sheets [y/n]? (press Enter to continue)\n")
# upload = answer.lower() != "n"
#
# # Saving complete list of players, including new ones
# utils.save_players_sheet(players, upload=upload)
#
# # Saving initial rankings for all known players
# utils.save_ranking_sheet(cfg["sheetname"]["initial_ranking"], ranking, players, upload=upload)
#
# # Remove temp files after a successful preprocessing
# utils.remove_temp_players_ranking()
