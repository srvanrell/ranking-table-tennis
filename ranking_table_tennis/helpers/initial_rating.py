import pandas as pd

from ranking_table_tennis import helpers, models
from ranking_table_tennis.configs import get_cfg

cfg = get_cfg()


def print_rating_context(
    tournaments: models.Tournaments,
    players: models.Players,
    name: str,
    tid: str,
) -> None:
    # Helper to assign an initial rating to name
    print("> Information that should help you assign rating")
    print("\n> Matches")

    # Print matches results for the unknown player
    matches = tournaments.get_matches(tid, False, [])
    matches_selected = matches[(matches.player_a == name) | (matches.player_b == name)].copy()
    print(matches_selected[["winner", "winner_pid", "loser", "loser_pid", "round", "category"]])

    # Print rating of known players, if available
    try:
        known_rankings = helpers.load_from_pickle(cfg.io.pickle.rankings)
        tids = [cfg.initial_metadata.initial_tid] + [t for t in tournaments]  # to use prev_tid
        pids_selected = (
            pd.concat([matches_selected.winner_pid, matches_selected.loser_pid], ignore_index=True)
            .dropna()
            .unique()
        )
        print("\n> Known ratings")
        for pid in pids_selected:
            print(
                f"> {tids[-2]}, {players[pid]['name']}, "
                f"rating: {known_rankings.get_entries(tids[-2], pid).get('rating')}"
            )
    except FileNotFoundError:
        print("> Sorry, not available data to help you\n")
