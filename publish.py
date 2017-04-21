import utils
import models
from utils import cfg

__author__ = 'sebastian'

##########################################
# Script to run after compute_all.py
# Input: xlsx tournaments database
#        config.yaml
# Output: temp xlsx to publish a single ranking
##########################################

tournaments_xlsx = cfg["io"]["data_folder"] + cfg["io"]["tournaments_filename"]
rankings_xlsx = cfg["io"]["data_folder"] + cfg["io"]["rankings_filename"]
temp_xlsx = cfg["io"]["data_folder"] + "temp.xlsx"
histories_xlsx = temp_xlsx

# Listing tournament sheetnames by increasing date
tournament_sheetnames = utils.get_sheetnames_by_date(tournaments_xlsx, cfg["sheetname"]["tournaments_key"])

# Loading players info list
players = models.PlayersList()
players.load_list(utils.load_sheet_workbook(tournaments_xlsx, cfg["sheetname"]["players"]))

# Loading initial ranking
initial_ranking = utils.load_ranking_sheet(tournaments_xlsx, cfg["sheetname"]["initial_ranking"])

for tid, tournament_sheetname in enumerate(tournament_sheetnames, start=1):
    print("\n%d\t->\t%s" % (tid, tournament_sheetname))
tid = int(input("Enter the tournament id to publish (look above):\n"))
tournament_sheetname = tournament_sheetnames[tid-1]

# Loading tournament info
tournament = utils.load_tournament_xlsx(tournaments_xlsx, tournament_sheetname)
ranking = utils.load_ranking_sheet(rankings_xlsx, tournament_sheetname.replace(
    cfg["sheetname"]["tournaments_key"], cfg["sheetname"]["rankings_key"]))

# #FIXME should not update here
# ranking.update_categories()
# # # Update categories before saving the new ranking
# # # FIXME see if it should be here or in publish
if tid == 1:
    new_ranking.update_categories(n_first=12, n_second=16)
else:
    # new_ranking.update_active()
    new_ranking.update_categories()

# Saving new ranking
utils.publish_rating_sheet(temp_xlsx, tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                                                   cfg["labels"]["Rating Points"]),
                           ranking, players, True)

# Saving new ranking
utils.publish_championship_sheet(temp_xlsx, tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                                                         "Campeonato"),
                                 ranking, players, True)


# TODO make a copy of point log sheets
# # Saving points assigned in each match
# points_log_to_save = [[players[winner_pid].name, players[loser_pid].name, winner_points, loser_points]
#                       for winner_pid, loser_pid, winner_points, loser_points in assigned_points_per_match]
#
# utils.save_sheet_workbook(log_xlsx,
#                           tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
#                                                        cfg["sheetname"]["rating_details_key"]),
#                           [cfg["labels"][key] for key in ["Winner", "Loser", "Winner Points", "Loser Points"]],
#                           points_log_to_save, True)
#
# # Saving points assigned per best round reached and for participation
# points_log_to_save = [[players[pid].name, points, best_round, category] for pid, points, best_round, category
#                       in assigned_points_per_best_round]
# participation_points_log_to_save = [[players[pid].name, points, cfg["labels"]["Participation Points"], ""]
#                                     for pid, points in assigned_participation_points]
#
# utils.save_sheet_workbook(log_xlsx,
#                           tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
#                                                        cfg["sheetname"]["bonus_details_key"]),
#                           [cfg["labels"][key] for key in ["Player", "Bonus Points", "Best Round", "Category"]],
#                           # points_log_to_save, True)
#                           points_log_to_save + participation_points_log_to_save, True)

# Saving complete histories of players
utils.publish_histories_sheet(histories_xlsx, "Historiales", players, tournament_sheetnames, True)
