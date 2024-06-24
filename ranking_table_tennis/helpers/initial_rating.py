import logging

import numpy as np
import pandas as pd

from ranking_table_tennis import helpers, models
from ranking_table_tennis.configs import ConfigManager

logger = logging.getLogger(__name__)


def suggest_initial_rating(
    tournaments: models.Tournaments,
    players: models.Players,
    initial_ranking: models.Rankings,
    name_unknown_player: str,
    tid: str,
) -> None:
    # Helper to assign an initial rating to name
    logger.info("# Following information should help you assign rating")

    cfg = ConfigManager().current_config

    # Print matches results for the unknown player
    matches = tournaments.get_matches(tid, False, [])

    limits_suggested_rating = [np.nan, np.nan]

    matches_as_winner = matches.loc[(matches.winner == name_unknown_player), :].copy()
    if matches_as_winner.empty:
        logger.warn("no matches as winner")
    else:
        fill_rating_column(matches_as_winner, players, tournaments, initial_ranking, tid, "loser")
        matches_str = str(
            matches_as_winner[
                ["winner", "winner_pid", "loser", "loser_pid", "round", "category", "rival_rating"]
            ]
        )
        logger.info(f"\n# Matches as winner\n{matches_str}\n")

        limits_suggested_rating[0] = matches_as_winner["rival_rating"].max()

    matches_as_loser = matches.loc[(matches.loser == name_unknown_player), :].copy()
    if matches_as_loser.empty:
        logger.warn("no matches as loser")
    else:
        fill_rating_column(matches_as_loser, players, tournaments, initial_ranking, tid, "winner")
        matches_str = str(
            matches_as_loser[
                ["winner", "winner_pid", "loser", "loser_pid", "round", "category", "rival_rating"]
            ]
        )
        logger.info(f"\n# Matches as loser\n{matches_str}\n")

        limits_suggested_rating[1] = matches_as_loser["rival_rating"].min()

    logger.info(f"# Known ratings (categories thresholds: {cfg.compute.categories_thresholds})")

    # Suggesting rating
    VIRTUAL_RANGE_NO_LIMIT = 60
    if np.isnan(limits_suggested_rating).all():
        # If no limits are available, cannot suggest a rating
        logger.warn("no rating to suggest")
    elif np.isnan(limits_suggested_rating[0]):
        limits_suggested_rating[0] = limits_suggested_rating[1] - VIRTUAL_RANGE_NO_LIMIT
    elif np.isnan(limits_suggested_rating[1]):
        limits_suggested_rating[1] = limits_suggested_rating[0] + VIRTUAL_RANGE_NO_LIMIT

    suggested_rating = np.mean(limits_suggested_rating)
    logger.info(f"Suggested rating: {suggested_rating}")

    return suggested_rating


def fill_rating_column(
    matches_df, players, tournaments, initial_rankings, tid, winner_or_loser: str
):
    matches_df["rival_rating"] = pd.NA

    cfg = ConfigManager().current_config
    tids = [cfg.initial_metadata.initial_tid] + [t for t in tournaments]  # to use prev_tid
    prev_tid = tids[tids.index(tid) - 1]

    # First try to use known previous ranking
    try:
        known_rankings = helpers.load_from_pickle(cfg.io.pickle.rankings)
    except FileNotFoundError:
        logger.warn("Sorry, no previous rating is available to help you")
        return

    for ix, row in matches_df.iterrows():
        rival_pid = row[f"{winner_or_loser}_pid"]
        rival_name = row[winner_or_loser]
        rival_rating = pd.NA

        # First try to use known previous ranking
        try:
            rival_rating = known_rankings.get_entries(prev_tid, rival_pid).get("rating")
            if rival_rating < 0:
                rival_rating = pd.NA
        except (AttributeError, UnboundLocalError):
            logger.warn("Sorry, no previous rating is available to help you with %s", rival_name)

        # If it is a new player, try to use the initial rating (that could be already defined)
        assigned_pid = players.get_pid(rival_name)
        # if pd.isna(rival_rating) and pd.isna(rival_pid) and assigned_pid is not None:
        if pd.isna(rival_rating) and assigned_pid is not None:
            try:
                rival_rating = initial_rankings.get_entries(tids[0], assigned_pid).get("rating")
                if rival_rating < 0:
                    rival_rating = pd.NA
            except (AttributeError, UnboundLocalError):
                logger.warn("Sorry, no initial rating is available to help you with %s", rival_pid)

        matches_df.loc[ix, "rival_rating"] = rival_rating
