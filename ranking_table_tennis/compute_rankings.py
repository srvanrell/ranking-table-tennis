from ranking_table_tennis import helpers
from ranking_table_tennis.configs import ConfigManager


def main():
    """Compute rating and championship points of loaded tournaments.

    Function to run after preprocess.main().

    It will read players, tournaments in pickles.
    It will save players, tournaments and rankings in pickles.
    """
    print("\n## Starting to compute rankings\n")

    # TODO set date from here?
    cfg = ConfigManager().current_config

    # Loading all tournament data
    tournaments = helpers.load_from_pickle(cfg.io.pickle.tournaments)

    # Loading players list
    players = helpers.load_from_pickle(cfg.io.pickle.players)
    tournaments.assign_pid_from_players(players)

    # Loading initial ranking
    rankings = helpers.load_initial_ranking_sheet()
    initial_tid = cfg.initial_metadata.initial_tid

    # Will compute all rankings from the beginning by default
    tids = [initial_tid] + [tid for tid in tournaments]

    for tid in tournaments:
        print("==", tid, "==")

        # Get the tid of the previous tournament
        prev_tid = tids[tids.index(tid) - 1]

        # Previous ranking data will be the default for the new ranking
        rankings.initialize_new_ranking(tid, prev_tid)

        # Create list of players that partipate in the tournament
        pid_participation_list = tournaments.get_players_pids(tid)

        # Get the best round for each player in each category
        best_rounds = tournaments.compute_best_rounds(tid, players)
        # Best rounds reached in each category are saved into corresponding history
        players.update_histories(tid, best_rounds)

        # List of players that didn't play its own category but plyed the higher one
        # Fans category is not considered in this list
        # Old ranking need to be updated so known old players are not misclassified
        rankings.update_categories()
        pid_not_own_category = [
            pid
            for pid in pid_participation_list
            if best_rounds[
                (best_rounds.pid == pid) & (best_rounds.category == rankings[tid, pid, "category"])
            ].empty
            and rankings[tid, pid, "category"] != cfg.categories[-1]
        ]

        rankings.compute_new_ratings(tid, prev_tid, tournaments, pid_not_own_category)
        rankings.compute_category_points(tid, best_rounds)

        rankings.update_active_players(tid, players, initial_tid)

        # Promote those players indicated in the matches list of the tournament
        # TODO I guess this has no effect because update categories is based on ratings
        rankings.promote_players(tid, tournaments)

        # Substract championship points
        rankings.apply_sanction(tid, tournaments)

        rankings.update_categories()
        rankings.compute_championship_points(tid)

    helpers.save_to_pickle(players=players, tournaments=tournaments, rankings=rankings)


if __name__ == "__main__":
    main()
