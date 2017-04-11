import utils
import models
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
histories_xlsx = xlsx_file  # cfg["io"]["data_folder"] + "histories.xlsx"

# Listing tournament sheetnames by increasing date
tournament_sheetnames = utils.get_sheetnames_by_date(xlsx_file, cfg["sheetname"]["tournaments_key"])

# Loading and completing the players list
players = models.PlayersList()
players.load_list(utils.load_sheet_workbook(xlsx_file, cfg["sheetname"]["players"]))

# Loading initial ranking and adding new players with 0
ranking = utils.load_ranking_sheet(xlsx_file, cfg["sheetname"]["initial_ranking"])

for tid, tournament_sheetname in enumerate(tournament_sheetnames):
    # Loading tournament info
    tournament = utils.load_tournament_xlsx(xlsx_file, tournament_sheetname)

    for name in tournament.get_players_names():
        if players.get_pid(name) is None:
            association = input("Enter the association of %s:\n" % name)
            city = input("Enter the city of %s:\n" % name)
            # Assign a pid for the new given player and add it to the list
            players.add_new_player(name, association, city)
            print(players[players.get_pid(name)])

        pid = players.get_pid(name)

        if ranking.get_entry(pid) is None:
            # TODO ask for initial category
            initial_rating = int(input("Enter the initial rating points for %s:\n" % name))
            ranking.add_new_entry(pid, initial_rating)
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
                          sorted(players.to_list(), key=lambda l: l[1]),
                          True)

# Saving initial rankings for all known players
utils.save_ranking_sheet(xlsx_file, cfg["sheetname"]["initial_ranking"], ranking, players, True)

# Saving complete histories of players
histories = []
for player in sorted(players, key=lambda l: l.name):
    histories.append([player.name, "", "", ""])
    old_cat = ""
    for cat, tid, best_round in player.sorted_history:
        if cat == old_cat:
            cat = ""
        else:
            old_cat = cat
        histories.append(["", cat, best_round, " ".join(tournament_sheetnames[tid].split()[1:])])


utils.save_sheet_workbook(histories_xlsx, "Historiales",
                          [cfg["labels"][key] for key in ["Player", "Category", "Best Round", "Tournament"]],
                          histories,
                          True)

