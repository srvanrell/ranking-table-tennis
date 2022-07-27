import os
import pickle
from typing import Tuple

from ranking_table_tennis import models
from ranking_table_tennis.configs import get_cfg
from ranking_table_tennis.helpers.pickle import load_from_pickle

cfg = get_cfg()


def load_temp_players_ranking() -> Tuple[models.Players, models.Rankings]:
    """returns players_temp, ranking_temp"""
    # Loading temp ranking and players. It should be deleted after a successful preprocessing
    players_temp_file = os.path.join(cfg.io.data_folder, cfg.io.players_temp_file)
    ranking_temp_file = os.path.join(cfg.io.data_folder, cfg.io.ranking_temp_file)

    if os.path.exists(players_temp_file):
        players_temp = load_from_pickle(cfg.io.players_temp_file)
        print("Resume preprocessing...")
    else:
        players_temp = models.Players()

    if os.path.exists(ranking_temp_file):
        ranking_temp = load_from_pickle(cfg.io.ranking_temp_file)
        print("Resume preprocessing...")
    else:
        ranking_temp = models.Rankings()

    return players_temp, ranking_temp


def save_temp_players_ranking(players_temp: models.Players, ranking_temp: models.Rankings) -> None:
    """returns players_temp, ranking_temp"""
    # Loading temp ranking and players. It shuould be deleted after a successful preprocessing
    players_temp_file = os.path.join(cfg.io.data_folder, cfg.io.players_temp_file)
    ranking_temp_file = os.path.join(cfg.io.data_folder, cfg.io.ranking_temp_file)
    print(
        "<Saving\t\tTemps to resume preprocessing (if necessary)",
        ranking_temp_file,
        players_temp_file,
        "\n",
    )
    with open(players_temp_file, "wb") as ptf, open(ranking_temp_file, "wb") as rtf:
        # Pickle the 'data' dictionary using the highest protocol available.
        pickle.dump(players_temp, ptf, pickle.HIGHEST_PROTOCOL)
        pickle.dump(ranking_temp, rtf, pickle.HIGHEST_PROTOCOL)


def remove_temp_players_ranking() -> None:
    players_temp_file = os.path.join(cfg.io.data_folder, cfg.io.players_temp_file)
    ranking_temp_file = os.path.join(cfg.io.data_folder, cfg.io.ranking_temp_file)
    print(
        "Removing temp files created to resume preprocessing", players_temp_file, ranking_temp_file
    )
    if os.path.exists(players_temp_file):
        os.remove(players_temp_file)
    if os.path.exists(ranking_temp_file):
        os.remove(ranking_temp_file)
