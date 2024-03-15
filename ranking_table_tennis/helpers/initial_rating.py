import logging

import pandas as pd

from ranking_table_tennis import helpers, models
from ranking_table_tennis.configs import ConfigManager

logger = logging.getLogger(__name__)


def print_rating_context(
    tournaments: models.Tournaments,
    players: models.Players,
    name: str,
    tid: str,
) -> None:
    # Helper to assign an initial rating to name
    print("# Information that should help you assign rating")
    print("\n# Matches")

    cfg = ConfigManager().current_config

    # Print matches results for the unknown player
    matches = tournaments.get_matches(tid, False, [])
    matches_selected = matches[(matches.player_a == name) | (matches.player_b == name)].copy()
    print(matches_selected[["winner", "winner_pid", "loser", "loser_pid", "round", "category"]])

    # Print rating of known players, if available
    try:
        known_rankings = helpers.load_from_pickle(cfg.io.pickle.rankings)
        tids = [cfg.initial_metadata.initial_tid] + [t for t in tournaments]  # to use prev_tid
        pids_with_rating = known_rankings.get_entries(tids[-2]).pid.to_list()
        pids_selected = (
            pd.concat([matches_selected.winner_pid, matches_selected.loser_pid], ignore_index=True)
            .dropna()
            .pipe(lambda s: s[s.isin(pids_with_rating)])  # filter pids with known rating
            .unique()
        )
        print("\n# Known ratings")
        for pid in pids_selected:
            print(
                f"# {tids[-2]}, {players[pid]['name']}, "
                f"rating: {known_rankings.get_entries(tids[-2], pid).get('rating')}"
            )
    except (FileNotFoundError, AttributeError):
        logger.warn("Sorry, previous rankings not available to help you")
