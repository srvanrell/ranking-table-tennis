import logging
import os
import pickle
from typing import Tuple

from ranking_table_tennis import models
from ranking_table_tennis.configs import ConfigManager
from ranking_table_tennis.helpers.pickle import load_from_pickle

logger = logging.getLogger(__name__)


def load_temp_players_ranking() -> Tuple[models.Players, models.Rankings]:
    """returns players_temp, ranking_temp"""
    cfg = ConfigManager().current_config
    # Loading temp ranking and players. It should be deleted after a successful preprocessing
    players_temp_file = os.path.join(cfg.io.data_folder, cfg.io.pickle.players_temp)
    ranking_temp_file = os.path.join(cfg.io.data_folder, cfg.io.pickle.ranking_temp)

    if os.path.exists(players_temp_file):
        players_temp = load_from_pickle(cfg.io.pickle.players_temp)
        logger.info("Resume preprocessing...")
    else:
        players_temp = models.Players()

    if os.path.exists(ranking_temp_file):
        ranking_temp = load_from_pickle(cfg.io.pickle.ranking_temp)
        logger.info("Resume preprocessing...")
    else:
        ranking_temp = models.Rankings()

    return players_temp, ranking_temp


def save_temp_players_ranking(players_temp: models.Players, ranking_temp: models.Rankings) -> None:
    """returns players_temp, ranking_temp"""
    cfg = ConfigManager().current_config
    # Loading temp ranking and players. It shuould be deleted after a successful preprocessing
    players_temp_file = os.path.join(cfg.io.data_folder, cfg.io.pickle.players_temp)
    ranking_temp_file = os.path.join(cfg.io.data_folder, cfg.io.pickle.ranking_temp)
    logger.debug(
        "< Saving temp resume files: '%s' '%s'",
        ranking_temp_file,
        players_temp_file,
    )
    with open(players_temp_file, "wb") as ptf, open(ranking_temp_file, "wb") as rtf:
        # Pickle the 'data' dictionary using the highest protocol available.
        pickle.dump(players_temp, ptf, pickle.HIGHEST_PROTOCOL)
        pickle.dump(ranking_temp, rtf, pickle.HIGHEST_PROTOCOL)


def remove_temp_players_ranking() -> None:
    cfg = ConfigManager().current_config
    players_temp_file = os.path.join(cfg.io.data_folder, cfg.io.pickle.players_temp)
    ranking_temp_file = os.path.join(cfg.io.data_folder, cfg.io.pickle.ranking_temp)
    logger.debug(">< Removing temp resume files '%s' '%s'", players_temp_file, ranking_temp_file)
    if os.path.exists(players_temp_file):
        os.remove(players_temp_file)
    if os.path.exists(ranking_temp_file):
        os.remove(ranking_temp_file)
