import utils
import models
from utils import cfg

__author__ = 'sebastian'

###################################################
# Script to run after compute_single_tournament.py
# Input: xlsx tournaments database
#        xlsx rankings database
#        xlsx log file
#        config.yaml
# Output: temp xlsx to publish a single ranking
###################################################

tournaments_xlsx = cfg["io"]["data_folder"] + cfg["io"]["tournaments_filename"]
rankings_xlsx = cfg["io"]["data_folder"] + cfg["io"]["rankings_filename"]
log_xlsx = cfg["io"]["data_folder"] + cfg["io"]["log_filename"]
output_xlsx = cfg["io"]["data_folder"] + cfg["io"]["publish_filename"]

# Listing tournament sheetnames by increasing date
tournament_sheetnames = utils.get_sheetnames_by_date(tournaments_xlsx, cfg["sheetname"]["tournaments_key"])

# Loading players info list
players = models.PlayersList()
players.load_list(utils.load_sheet_workbook(tournaments_xlsx, cfg["sheetname"]["players"]))

# Loading initial ranking
initial_ranking = utils.load_ranking_sheet(tournaments_xlsx, cfg["sheetname"]["initial_ranking"], replace_key=False)

for tid, tournament_sheetname in enumerate(tournament_sheetnames, start=1):
    print("\n%d\t->\t%s" % (tid, tournament_sheetname))
tid = int(input("Enter the tournament id to publish (look above):\n"))
tournament_sheetname = tournament_sheetnames[tid-1]
output_xlsx = output_xlsx.replace("NN", "%d" % tid)

# Loading tournament info
tournament = utils.load_tournament_xlsx(tournaments_xlsx, tournament_sheetname)
ranking = utils.load_ranking_sheet(rankings_xlsx, tournament_sheetname)

old_ranking = models.Ranking("pre_" + tournament.name, tournament.date, tournament.location, tid - 2)
# Load previous ranking if exists
if tid-1 > 0:
    old_ranking = utils.load_ranking_sheet(rankings_xlsx, tournament_sheetnames[tid - 2])

# Load initial rankings for new players
for entry in ranking:
    if old_ranking.get_entry(entry.pid) is None:
        old_ranking.add_entry(initial_ranking[entry.pid])

# Publish formated rating of selected tournament
utils.publish_rating_sheet(output_xlsx, tournament_sheetname, ranking, players, old_ranking)

# Publish formated championship of selected tournament
utils.publish_championship_sheet(output_xlsx, tournament_sheetname, ranking, players, old_ranking)

# Saving points assigned in each match
rating_details_sheetname = tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                                        cfg["sheetname"]["rating_details_key"])
rating_log_saved = utils.load_sheet_workbook(log_xlsx, rating_details_sheetname, first_row=0)
utils.save_sheet_workbook(output_xlsx, rating_details_sheetname, rating_log_saved[0], rating_log_saved[1:])

# Saving points assigned per best round reached and for participation
bonus_details_sheetname = tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                                       cfg["sheetname"]["bonus_details_key"])
bonus_log_saved = utils.load_sheet_workbook(log_xlsx, bonus_details_sheetname, first_row=0)
utils.save_sheet_workbook(output_xlsx, bonus_details_sheetname, bonus_log_saved[0], bonus_log_saved[1:])

# Saving complete histories of players
utils.publish_histories_sheet(output_xlsx, cfg["sheetname"]["histories"], players, tournament_sheetnames)
