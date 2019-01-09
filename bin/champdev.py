#!/usr/bin/env python3

from ranking_table_tennis import utils
from ranking_table_tennis import models
from ranking_table_tennis.models import cfg
import pandas as pd

__author__ = 'sebastian'

log_xlsx = cfg["io"]["data_folder"] + cfg["io"]["log_filename"]

# Labels of columns, just to simplify notation
player_col = cfg["labels"]["Player"]
category_col = cfg["labels"]["Category"]
points_col = cfg["labels"]["Bonus Points"]
participations_col = cfg["labels"]["Participations"]

tournament_sheetnames = utils.get_tournament_sheetnames_by_date()

# Will compute all rankings from the beginning by default
tids = range(1, len(tournament_sheetnames)+1)

df = pd.DataFrame()

for tid in tids:
    tournament_sheetname = tournament_sheetnames[tid - 1]
    bonus_log = utils.load_sheet_workbook(log_xlsx,
                                          tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                                                       cfg["sheetname"]["bonus_details_key"]),
                                          first_row=1)
    temp_df = pd.DataFrame([[tid] + j for j in bonus_log],
                           columns=[cfg["labels"][key] for key in ["Tournament", "Player", "Bonus Points",
                                                                   "Best Round", "Category"]]
                           )
    temp_df = temp_df[temp_df[category_col] != ""]
    df = df.append(temp_df, ignore_index=True)

N_tournaments = 5
N_classified = 200

pl_cat_N_tour = df.groupby([player_col, category_col])[points_col].nlargest(N_tournaments)

pl_cat_cumul = pl_cat_N_tour.groupby([player_col, category_col]).sum().reset_index()
pl_cat_count = df.groupby([player_col, category_col])[points_col].count().reset_index().rename(
    columns={points_col: participations_col})

pl_cat = pd.merge(pl_cat_cumul, pl_cat_count).sort_values(points_col, ascending=False)

sort_by_point = pl_cat.groupby(category_col, as_index=False).apply(lambda x: pd.DataFrame.nlargest(x, n=N_classified, columns=points_col))
sort_by_count = pl_cat.groupby(category_col, as_index=False).apply(lambda x: pd.DataFrame.nlargest(x, n=N_classified, columns=participations_col))

filename = cfg["io"]["data_folder"] + "Copa Campeonato 2019 - " + str(N_tournaments) + " torneos.xlsx"

for cat in models.categories:
    print(cat, tournament_sheetname)

    df_cat_by_point = sort_by_point[sort_by_point[category_col] == cat]
    df_cat_by_point.drop(category_col, axis=1, inplace=True)

    utils.save_sheet_workbook(filename,
                              tournament_sheetname.replace(cfg["sheetname"]["tournaments_key"],
                                                           cat),
                              df_cat_by_point.columns.tolist(),
                              df_cat_by_point.values.tolist())
