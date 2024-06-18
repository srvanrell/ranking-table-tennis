import logging

import pandas as pd

from ranking_table_tennis import helpers, models
from ranking_table_tennis.configs import ConfigManager

logger = logging.getLogger(__name__)


def print_rating_context(
    tournaments: models.Tournaments,
    players: models.Players,
    initial_ranking: models.Rankings,
    name_unknown_player: str,
    tid: str,
) -> None:
    # Helper to assign an initial rating to name
    print("# Information that should help you assign rating")
    print("\n# Matches")

    cfg = ConfigManager().current_config

    # Print matches results for the unknown player
    matches = tournaments.get_matches(tid, False, [])

    matches_as_winner = matches.loc[(matches.winner == name_unknown_player), :].copy()
    if not matches_as_winner.empty:
        fill_rating_column(matches_as_winner, players, tournaments, initial_ranking, "loser")
        print("matches as winner")
        print(
            matches_as_winner[
                ["winner", "winner_pid", "loser", "loser_pid", "round", "category", "rating"]
            ]
        )
    else:
        print("no matches as winner")

    matches_as_loser = matches.loc[(matches.loser == name_unknown_player), :].copy()
    if not matches_as_loser.empty:
        fill_rating_column(matches_as_loser, players, tournaments, initial_ranking, "winner")
        print("loser matches")
        print(
            matches_as_loser[
                ["winner", "winner_pid", "loser", "loser_pid", "round", "category", "rating"]
            ]
        )
    else:
        print("no matches as loser")

    print(f"\n# Known ratings (categories thresholds: {cfg.compute.categories_thresholds})")


def fill_rating_column(matches_df, players, tournaments, initial_rankings, winner_or_loser: str):
    matches_df["rating"] = pd.NA

    cfg = ConfigManager().current_config
    tids = [cfg.initial_metadata.initial_tid] + [t for t in tournaments]  # to use prev_tid
    prev_tid = tids[-2]

    # First try to use known previous ranking
    try:
        known_rankings = helpers.load_from_pickle(cfg.io.pickle.rankings)
    except FileNotFoundError:
        logger.warn("Sorry, no previous rating is available to help you")

    initial_rankings

    for ix, row in matches_df.iterrows():
        rival_pid = row[f"{winner_or_loser}_pid"]
        rival_name = row[winner_or_loser]
        rival_rating = pd.NA

        # First try to use known previous ranking
        try:
            rival_rating = known_rankings.get_entries(prev_tid, rival_pid).get("rating")
        except (AttributeError, UnboundLocalError):
            logger.warn("Sorry, no previous rating is available to help you with %s", rival_name)

        # If it is a new player, try to use the initial rating (that could be already defined)
        assigned_pid = players.get_pid(rival_name)
        if pd.isna(rival_rating) and pd.isna(rival_pid) and assigned_pid is not None:
            try:
                rival_rating = initial_rankings.get_entries(tids[0], assigned_pid).get("rating")
            except (AttributeError, UnboundLocalError):
                logger.warn("Sorry, no initial rating is available to help you with %s", rival_pid)

        matches_df.loc[ix, "rating"] = rival_rating
