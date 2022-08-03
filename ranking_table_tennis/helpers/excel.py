import os
from typing import List

import pandas as pd

from ranking_table_tennis import models
from ranking_table_tennis.configs import get_cfg
from ranking_table_tennis.helpers.gspread import upload_sheet_from_df

cfg = get_cfg()


def get_tournament_sheet_names_ordered() -> List[str]:
    tournaments_xlsx = cfg.io.data_folder + cfg.io.xlsx.tournaments_filename
    filter_key = cfg.sheetname.tournaments_key
    df_tournaments = pd.read_excel(tournaments_xlsx, sheet_name=None, header=None)
    sheet_names = [s for s in df_tournaments.keys() if filter_key in s]

    return sorted(sheet_names)


def load_players_sheet() -> models.Players:
    tournaments_xlsx = cfg.io.data_folder + cfg.io.xlsx.tournaments_filename
    players_df = pd.read_excel(tournaments_xlsx, sheet_name=cfg.sheetname.players, header=0)
    print("> Reading", cfg.sheetname.players, "from", tournaments_xlsx, sep="\t")

    players_df.rename(
        columns={
            cfg.labels.pid: "pid",
            cfg.labels.Player: "name",
            cfg.labels.Association: "affiliation",
            cfg.labels.City: "city",
        },
        inplace=True,
    )

    players = models.Players(players_df)

    return players


def load_initial_ranking_sheet() -> models.Rankings:
    tournaments_xlsx = cfg.io.data_folder + cfg.io.xlsx.tournaments_filename
    initial_ranking_df = pd.read_excel(
        tournaments_xlsx, sheet_name=cfg.sheetname.initial_ranking, header=0
    )
    print("> Reading", cfg.sheetname.initial_ranking, "from", tournaments_xlsx, sep="\t")

    columns_translations = {
        cfg.labels.tid: "tid",
        cfg.labels.Tournament_name: "tournament_name",
        cfg.labels.Date: "date",
        cfg.labels.Location: "location",
        cfg.labels.pid: "pid",
        cfg.labels.Player: "name",
        cfg.labels.Rating: "rating",
        cfg.labels.Category: "category",
        cfg.labels.Active_Player: "active",
    }

    initial_ranking_df.rename(columns=columns_translations, inplace=True)
    initial_ranking_df.loc[:, "active"] = initial_ranking_df.loc[:, "active"].apply(
        lambda x: x == cfg.activeplayer[True]
    )
    initial_ranking = models.Rankings(initial_ranking_df)

    return initial_ranking


def load_tournaments_sheets() -> models.Tournaments:
    tournaments_xlsx = cfg.io.data_folder + cfg.io.xlsx.tournaments_filename
    filter_key = cfg.sheetname.tournaments_key
    raw_tournaments = pd.read_excel(tournaments_xlsx, sheet_name=None, header=None)
    sheet_names = sorted([s for s in raw_tournaments.keys() if filter_key in s])

    to_concat = []
    for sheet_name in sheet_names:
        print("> Reading", sheet_name, "from", tournaments_xlsx, sep="\t")
        raw_tournament = raw_tournaments[sheet_name]

        tournament_df = raw_tournament.iloc[5:].copy()
        tournament_df.rename(
            columns={
                0: "player_a",
                1: "player_b",
                2: "sets_a",
                3: "sets_b",
                4: "round",
                5: "category",
            },
            inplace=True,
        )
        tournament_df.insert(0, "location", raw_tournament.iat[2, 1])
        tournament_df.insert(0, "date", raw_tournament.iat[1, 1])
        tournament_df.insert(0, "tournament_name", raw_tournament.iat[0, 1])
        tournament_df.insert(0, "sheet_name", sheet_name)

        to_concat.append(tournament_df)

    tournaments_df = pd.concat(to_concat, ignore_index=True)
    tournaments = models.Tournaments(tournaments_df)

    return tournaments


def save_players_sheet(players: models.Players, upload=False) -> None:
    sorted_players_df = players.players_df.sort_values("name")
    xlsx_filename = cfg.io.data_folder + cfg.io.xlsx.tournaments_filename
    sheet_name = cfg.sheetname.players

    with _get_writer(xlsx_filename, sheet_name) as writer:
        headers = [cfg.labels[key] for key in ["Player", "Association", "City"]]
        sorted_players_df.to_excel(
            writer, sheet_name=sheet_name, index_label=cfg.labels.pid, header=headers
        )

    if upload:
        headers_df = [cfg.labels.pid] + headers
        upload_sheet_from_df(
            cfg.io.tournaments_spreadsheet_id,
            cfg.sheetname.players,
            sorted_players_df,
            headers_df,
            include_index=True,
        )  # index is pid


def save_ranking_sheet(
    tid: str,
    tournaments: models.Tournaments,
    rankings: models.Rankings,
    players: models.Players,
    upload: bool = False,
) -> None:
    if tid == cfg.initial_metadata.initial_tid:
        sheet_name = cfg.sheetname.initial_ranking
        xlsx_filename = cfg.io.data_folder + cfg.io.xlsx.tournaments_filename
    else:
        xlsx_filename = cfg.io.data_folder + cfg.io.xlsx.rankings_filename
        sheet_name = tournaments[tid].iloc[0].sheet_name
        sheet_name = sheet_name.replace(cfg.sheetname.tournaments_key, cfg.sheetname.rankings_key)

    sorted_rankings_df = rankings.ranking_df.sort_values("rating", ascending=False)
    sorted_rankings_df.loc[:, "active"] = sorted_rankings_df.loc[:, "active"].apply(
        lambda x: cfg.activeplayer[x]
    )
    sorted_rankings_df.insert(
        2, "name", sorted_rankings_df.loc[:, "pid"].apply(lambda pid: players[pid]["name"])
    )
    sorted_rankings_df.loc[:, "date"] = sorted_rankings_df.loc[:, "date"].apply(
        lambda d: d.strftime("%Y %m %d")
    )

    with _get_writer(xlsx_filename, sheet_name) as writer:
        headers = [
            cfg.labels[key]
            for key in [
                "tid",
                "Tournament_name",
                "Date",
                "Location",
                "pid",
                "Player",
                "Rating",
                "Category",
                "Active_Player",
            ]
        ]
        columns = [
            "tid",
            "tournament_name",
            "date",
            "location",
            "pid",
            "name",
            "rating",
            "category",
            "active",
        ]
        sorted_rankings_df.to_excel(
            writer, sheet_name=sheet_name, index=False, header=headers, columns=columns
        )

    if upload:
        upload_sheet_from_df(
            cfg.io.tournaments_spreadsheet_id,
            cfg.sheetname.initial_ranking,
            sorted_rankings_df.loc[:, columns],
            headers,
        )


def save_raw_ranking(rankings: models.Rankings, players: models.Players, tid: str) -> None:
    """Add players name to raw ranking to be save into a spreadsheet."""
    xlsx_filename = cfg.io.data_folder + f"raw_ranking_{tid}.xlsx"
    print("<<<Saving raw ranking in", xlsx_filename, sep="\t")

    # Rankings sorted by rating
    this_ranking_df = rankings[tid].sort_values("rating", ascending=False)

    # Format data and columns to write into the file
    this_ranking_df = this_ranking_df.merge(players.players_df.loc[:, ["name"]], on="pid")
    this_ranking_df.to_excel(xlsx_filename)


def _get_writer(xlsx_filename: str, sheet_name: str) -> pd.ExcelWriter:
    writer_mode = _get_writer_mode(xlsx_filename)
    print("<<<Saving", sheet_name, "in", xlsx_filename, sep="\t")
    if writer_mode == "a":
        writer = pd.ExcelWriter(
            xlsx_filename, engine="openpyxl", mode=writer_mode, if_sheet_exists="replace"
        )
    else:
        writer = pd.ExcelWriter(xlsx_filename, engine="openpyxl", mode=writer_mode)

    return writer


def _get_writer_mode(xlsx_file_path: str) -> str:
    mode = "a"
    if not os.path.exists(xlsx_file_path):
        mode = "w"

    return mode
