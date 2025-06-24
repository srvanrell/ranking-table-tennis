import logging

from ranking_table_tennis import helpers
from ranking_table_tennis.configs import ConfigManager

logger = logging.getLogger(__name__)


def main(online=False, last=True, tournament_num=None, config_initial_date="220101"):
    """Publish the results to anew spreadsheet and upload it.

    Function to run after compute_rankings.main().
    It will read players, tournaments and rankings in pickles, and config.yaml.
    It will output an xlsx to publish a single ranking (the tournament indicated).
    It will output a raw ranking xlsx corresponding to the one indicated.

    If online=True it will upload results (otherwise only local files will be created).
    If last=True it will publish results of the last tournament.

    tournament_num (int): enter the number of a valid tournament. if given, last is ommited
    """
    logger.info("Starting publish!")

    ConfigManager().set_current_config(date=config_initial_date)
    cfg = ConfigManager().current_config

    # Loading all tournament data
    tournaments = helpers.load_from_pickle(cfg.io.pickle.tournaments)

    # Loading players list
    players = helpers.load_from_pickle(cfg.io.pickle.players)
    tournaments.assign_pid_from_players(players)

    # Loading initial ranking
    rankings = helpers.load_from_pickle(cfg.io.pickle.rankings)
    initial_tid = cfg.initial_metadata.initial_tid

    # Will publish rankings of last tournament by default
    tids = [initial_tid] + [tid for tid in tournaments]

    tid = tids[-1]
    if not last and not tournament_num:
        print("\nNumber\t->\tTournament ID")
        for tenum, tid in enumerate(tids[1:], 1):
            print(f"{tenum:d}\t->\t{tid}")

        t_num = int(input("Enter the tournament number to publish: "))
        tid = tids[t_num]
    # An explicit tournament num will overwrite other options
    if tournament_num:
        tid = tids[tournament_num]

    # Get the tid of the previous tournament
    prev_tid = tids[tids.index(tid) - 1]

    upload = False
    if online:
        answer = input("\nDo you want to publish to backend online sheets [Y/n]? ")
        upload = answer.lower() != "n"

    # Update config
    tournament_date = tournaments[tid].iloc[0].date.strftime("%y%m%d")
    ConfigManager().set_current_config(date=tournament_date)

    # Publish formated rating of selected tournament
    helpers.publish_rating_sheet(tournaments, rankings, players, tid, prev_tid, upload=upload)
    helpers.publish_rating_sheet(
        tournaments, rankings, players, tid, prev_tid, upload=upload, all_players=True
    )

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

    # Save raw rankings as xlsx
    for raw_tid in tids[1:]:
        helpers.save_raw_ranking(rankings, players, raw_tid)

    # Create and save interactive figures
    helpers.plot_ratings(tid)
    helpers.plot_championships(tid)

    if online:
        answer = input("\nDo you want to publish to the web [Y/n]? ")
        show_on_web = (answer.lower() != "n") and (tid != tids[1])

        helpers.publish_to_web(tid, show_on_web)
