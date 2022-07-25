from ranking_table_tennis import helpers
from ranking_table_tennis.configs import get_cfg

cfg = get_cfg()


def main(offline=True, last=True, tournament_num=None):
    """Publish the results to anew spreadsheet and upload it.

    Function to run after compute_rankings.main().
    It will read players, tournaments and rankings in pickles, and config.yaml.
    It will output an xlsx to publish a single ranking (the tournament indicated).
    It will output a raw ranking xlsx corresponding to the one indicated.

    If offline=True it will publish locally (not uploading results).
    If last=True it will publish results of the last tournament.

    tournament_num (int): enter the number of a valid tournament
    """
    print("\n## Starting publish\n")

    # Loading all tournament data
    tournaments = helpers.load_from_pickle(cfg.io.tournaments_pickle)

    # Loading players list
    players = helpers.load_from_pickle(cfg.io.players_pickle)
    tournaments.assign_pid_from_players(players)

    # Loading initial ranking
    rankings = helpers.load_from_pickle(cfg.io.rankings_pickle)
    initial_tid = cfg.aux.initial_tid

    # Will publish rankings of last tournament by default
    tids = [initial_tid] + [tid for tid in tournaments]

    tid = tids[-1]
    if not last and not tournament_num:
        print("\nNumber\t->\tTournament ID")
        for tenum, tid in enumerate(tids[1:], 1):
            print(f"{tenum:d}\t->\t{tid}")

        t_num = int(input("Enter the tournament number to publish (look above):\n"))
        tid = tids[t_num]
    # An explicit tournament num will overwrite other options
    if tournament_num:
        tid = tids[tournament_num]

    # Get the tid of the previous tournament
    prev_tid = tids[tids.index(tid) - 1]

    upload = False
    if not offline:
        answer = input(
            "\nDo you want to publish to backend online sheets [Y/n]? (press Enter to continue)\n"
        )
        upload = answer.lower() != "n"

    # Publish formated rating of selected tournament
    helpers.publish_rating_sheet(tournaments, rankings, players, tid, prev_tid, upload=upload)

    # Publish points assigned in each match
    helpers.publish_rating_details_sheet(
        tournaments, rankings, players, tid, prev_tid, upload=upload
    )

    # Publish matches as they were loaded
    helpers.publish_matches_sheet(tournaments, rankings, players, tid, upload=upload)

    # Publish formated masters championship of selected tournament
    helpers.publish_championship_sheets(
        tournaments, rankings, players, tid, prev_tid, upload=upload
    )

    # Publish points assigned per best round reached
    helpers.publish_championship_details_sheet(
        tournaments, rankings, players, tid, prev_tid, upload=upload
    )

    # Saving complete histories of players
    helpers.publish_histories_sheet(tournaments, rankings, players, tid, prev_tid, upload=upload)

    # Publshing initial_ranking
    helpers.publish_initial_rating_sheet(tournaments, rankings, players, tid, upload=upload)

    # Publish statistics
    helpers.publish_statistics_sheet(tournaments, rankings, players, tid, prev_tid, upload=upload)

    if not offline:
        answer = input("\nDo you want to publish to the web [Y/n]? (press Enter to continue)\n")
        show_on_web = (answer.lower() != "n") and (tid != tids[1])

        helpers.publish_to_web(tid, show_on_web)

    helpers.save_raw_ranking(rankings, players, tid)
