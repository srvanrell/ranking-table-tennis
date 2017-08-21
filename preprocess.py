import utils
import models
from urllib import request
from utils import cfg

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
spreadsheet_id = cfg["io"]["tournaments_spreadsheet_id"]

retrieve = input("Do you want to retrieve online sheet [YES/no]? (press Enter to continue)\n")
if retrieve.lower() != "no":
    print("Downloading and saving %s\n" % xlsx_file)
    request.urlretrieve(cfg["io"]["tournaments_gdrive"], xlsx_file)

# Listing tournament sheetnames by increasing date
tournament_sheetnames = utils.get_sheetnames_by_date(cfg["sheetname"]["tournaments_key"])

# Loading players list
players = models.PlayersList()
players.load_list(utils.load_sheet_workbook(xlsx_file, cfg["sheetname"]["players"]))

# Loading initial ranking and adding new players with 0
ranking = utils.load_ranking_sheet(xlsx_file, cfg["sheetname"]["initial_ranking"], replace_key=False)

for tid, tournament_sheetname in enumerate(tournament_sheetnames, start=1):
    # Loading tournament info
    tournament = utils.load_tournament_xlsx(tournament_sheetname)

    for name in tournament.get_players_names():
        if players.get_pid(name) is None:
            association = input("Enter the association of %s:\n" % name)
            city = input("Enter the city of %s:\n" % name)
            # Assign a pid for the new given player and add it to the list
            players.add_new_player(name, association, city)
            print(players[players.get_pid(name)])

        pid = players.get_pid(name)

        if ranking.get_entry(pid) is None:
            initial_rating = int(input("Enter the initial rating points for %s:\n" % name))
            ranking.add_new_entry(pid, initial_rating)
            print(ranking[pid])

        if ranking[pid].category is "":
            for option, category in enumerate(models.categories, start=1):
                print("\n%d\t->\t%s" % (option, category))
            selected_category = int(input("Enter the initial category (look above) for %s:\n" % name))
            ranking[pid].category = models.categories[selected_category-1]
            print(ranking[pid])

    # Get the best round for each player in each category
    # Formatted like: best_rounds[(category, pid)] = best_round_value
    aux_best_rounds = tournament.compute_best_rounds()
    best_rounds = {(categ, players.get_pid(name)): aux_best_rounds[categ, name]
                   for categ, name in aux_best_rounds.keys()}

    # Log current tournament as the last played tournament
    # Also, best rounds reached in each category are saved into corresponding history
    players.update_histories(tid, best_rounds)

# Saving complete list of players, including new ones
utils.save_sheet_workbook(xlsx_file, cfg["sheetname"]["players"],
                          [cfg["labels"][key] for key in ["PID", "Player", "Association", "City",
                                                          "Last Tournament", "Participations"]],
                          sorted(players.to_list(), key=lambda l: l[1]))

# Saving initial rankings for all known players
utils.save_ranking_sheet(xlsx_file, cfg["sheetname"]["initial_ranking"], ranking, players, replace_key=False)

# Update the online version
retrieve = input("\nDo you want to update online sheets [YES/no]? (press Enter to continue)\n")
if retrieve.lower() != "no":
    print("Uploading changes to online sheets in %s\n" % spreadsheet_id)

    # Saving complete list of players, including new ones
    utils.upload_sheet(spreadsheet_id, cfg["sheetname"]["players"],
                       [cfg["labels"][key] for key in ["PID", "Player", "Association", "City",
                                                       "Last Tournament", "Participations"]],
                       sorted(players.to_list(), key=lambda l: l[1]))

    # # Saving initial rankings for all known players
    utils.upload_ranking_sheet(spreadsheet_id, cfg["sheetname"]["initial_ranking"], ranking,
                               players, replace_key=False)
