#!/usr/bin/env python3

from ranking_table_tennis import utils
from ranking_table_tennis import models
from ranking_table_tennis.models import cfg
from urllib import request
import pickle
import os

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

retrieve = input("Do you want to retrieve online sheet [y/n]? (press Enter to continue)\n")
if retrieve.lower() != "n":
    print("Downloading and saving %s\n" % xlsx_file)
    request.urlretrieve(cfg["io"]["tournaments_gdrive"], xlsx_file)

# Listing tournament sheetnames by increasing date
tournament_sheetnames = utils.get_tournament_sheetnames_by_date()

# Loading players list
players = models.PlayersList()
players.load_list(utils.load_players_sheet())

# Loading initial ranking and adding new players with 0
ranking = utils.load_ranking_sheet(cfg["sheetname"]["initial_ranking"])

# Loading temp ranking and players. It will be deleted after a successful preprocessing
# FIXME this should be done in a single function inside utils
players_temp_file = 'temp_players.pickle'
ranking_temp = models.Ranking()
print("\nDebugging version\n")
if os.path.exists(players_temp_file):
    with open(players_temp_file, 'rb') as f:
        print(">Reading\t\tTemp list of players\t\tResuming preprocessing :)")
        players_temp = pickle.load(f)
else:
    players_temp = models.PlayersList()

for tid, tournament_sheetname in enumerate(tournament_sheetnames, start=1):
    # Loading tournament info
    tournament = utils.load_tournament_xlsx(tournament_sheetname)

    for name in tournament.get_players_names():
        if players.get_pid(name) is None:
            if players_temp.get_pid(name) is None:
                association = input("Enter the association of %s: (optional field)\n" % name)
                city = input("Enter the city of %s: (optional field)\n" % name)
                # Assign a pid for the new given player and add it to the list
                players.add_new_player(name, association, city)
                # Save a temp player to resume preprocessing, if necessary
                players_temp.add_player(players[players.get_pid(name)])
            else:
                print(">>>>\tUNCOMPLETE preprocessing detected. Trying to resume from", players_temp_file)
                players.add_player(players_temp[players_temp.get_pid(name)])
            print(players[players.get_pid(name)])

        # TODO save temp ranking and players
        with open(players_temp_file, 'wb') as f:
            # Pickle the 'data' dictionary using the highest protocol available.
            pickle.dump(players_temp, f, pickle.HIGHEST_PROTOCOL)

        pid = players.get_pid(name)

        if ranking.get_entry(pid) is None:
            initial_rating = int(input("Enter the initial rating points for %s:\n" % name))
            ranking.add_new_entry(pid, initial_rating)
            print(ranking[pid])
            # Save a temp ranking of the player to resume preprocessing, if necessary
            ranking_temp.add_entry(ranking[pid])

        if ranking[pid].category is "":
            for option, category in enumerate(models.categories, start=1):
                print("%d\t->\t%s" % (option, category))
            selected_category = int(input("Enter the initial category (look above) for %s:\n" % name))
            ranking[pid].category = models.categories[selected_category-1]
            print(ranking[pid])
            # Save a temp ranking of the player to resume preprocessing, if necessary
            ranking_temp[pid].category = ranking[pid].category

    # Get the best round for each player in each category
    # Formatted like: best_rounds[(category, pid)] = best_round_value
    aux_best_rounds = tournament.compute_best_rounds()
    best_rounds = {(categ, players.get_pid(name)): aux_best_rounds[categ, name]
                   for categ, name in aux_best_rounds.keys()}

    # Log current tournament as the last played tournament
    # Also, best rounds reached in each category are saved into corresponding history
    players.update_histories(tid, best_rounds)

# Update the online version
answer = input("\nDo you want to update online sheets [y/n]? (press Enter to continue)\n")
upload = answer.lower() != "n"

# Saving complete list of players, including new ones
utils.save_players_sheet(players, upload=upload)

# Saving initial rankings for all known players
utils.save_ranking_sheet(cfg["sheetname"]["initial_ranking"], ranking, players, upload=upload)
