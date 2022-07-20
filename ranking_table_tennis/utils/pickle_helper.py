import os
import pickle
from typing import Any

from ranking_table_tennis.configs import cfg
from ranking_table_tennis import models


def save_to_pickle(
    players: models.Players = None,
    rankings: models.Rankings = None,
    tournaments: models.Tournaments = None,
) -> None:
    objects = [players, rankings, tournaments]
    filenames = [
        cfg.io.players_pickle,
        cfg.io.rankings_pickle,
        cfg.io.tournaments_pickle,
    ]
    objects_filenames = [(obj, fn) for obj, fn in zip(objects, filenames) if obj]

    for obj, fn in objects_filenames:
        print("<<<Saving", fn, "in", cfg.io.data_folder, sep="\t")
        with open(os.path.join(cfg.io.data_folder, fn), "wb") as fo:
            pickle.dump(obj, fo, pickle.HIGHEST_PROTOCOL)


def load_from_pickle(filename: str) -> Any:
    print(">>>Loading", filename, "from", cfg.io.data_folder, sep="\t")
    with open(os.path.join(cfg.io.data_folder, filename), "rb") as fo:
        obj = pickle.load(fo)

    return obj