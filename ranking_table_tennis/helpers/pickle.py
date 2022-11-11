import logging
import os
import pickle
from typing import Any

from ranking_table_tennis import models
from ranking_table_tennis.configs import ConfigManager

logger = logging.getLogger(__name__)


def save_to_pickle(
    players: models.Players = None,
    rankings: models.Rankings = None,
    tournaments: models.Tournaments = None,
) -> None:
    cfg = ConfigManager().current_config
    objects = [players, rankings, tournaments]
    filenames = [
        cfg.io.pickle.players,
        cfg.io.pickle.rankings,
        cfg.io.pickle.tournaments,
    ]
    objects_filenames = [(obj, fn) for obj, fn in zip(objects, filenames) if obj]

    for obj, fn in objects_filenames:
        logger.debug("< Saving '%s' @ '%s'", fn, cfg.io.data_folder)
        with open(os.path.join(cfg.io.data_folder, fn), "wb") as fo:
            pickle.dump(obj, fo, pickle.HIGHEST_PROTOCOL)


def load_from_pickle(filename: str) -> Any:
    cfg = ConfigManager().current_config
    logger.debug("> Loading '%s' @ '%s'", filename, cfg.io.data_folder)
    with open(os.path.join(cfg.io.data_folder, filename), "rb") as fo:
        obj = pickle.load(fo)

    return obj
