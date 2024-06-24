import logging
from urllib import request

from ranking_table_tennis import helpers
from ranking_table_tennis.configs import ConfigManager

logger = logging.getLogger(__name__)


def main(config_initial_date="220101", download=True):
    """Preprocess matches on xlsx tournaments database. Resolves with no human interaction

    Function to run before compute_rankings.main().
    It will use xlsx tournaments database and config.yaml.
    It will output xlsx tournaments database updated.
    It will save players and tournaments in pickles.

    It looks for unknown or unrated players.
    It will ask for information not given and saves the result into the same xlsx

    If offline=True it will execute preprocessing locally (not retrieving or uploading updates).
    """
    logger.info("Starting preprocess unattended!")

    ConfigManager().set_current_config(date=config_initial_date)
    cfg = ConfigManager().current_config

    # Stop preprocess if there were no recent updates on the spreadsheet
    helpers.no_updates_stop_workflow(cfg.io.tournaments_spreadsheet_id)

    if download:
        xlsx_file = cfg.io.data_folder + cfg.io.xlsx.tournaments_filename
        logger.info("Downloading and saving '%s'" % xlsx_file)
        request.urlretrieve(cfg.io.tournaments_gdrive, xlsx_file)

    # Loading all tournament data
    tournaments = helpers.load_tournaments_sheets()

    # Loading players list
    players = helpers.load_players_sheet()

    # Assign pid to known players
    tournaments.assign_pid_from_players(players)

    # Loading initial ranking
    rankings = helpers.load_initial_ranking_sheet()
    initial_tid = cfg.initial_metadata.initial_tid

    unknown_player_should_update = False

    for tid in tournaments:
        logger.info("** Processing %s", tid)

        for name in tournaments.get_players_names(tid):

            if players.get_pid(name) is None:
                unknown_player_should_update = True
                # Assign a pid for the new given player and add it to the list
                players.add_new_player(name)
                logger.info(f"\n{players[players.get_pid(name)]}\n")

            pid = players.get_pid(name)

            # Category will be asigned
            if rankings[initial_tid, pid] is None:
                unknown_player_should_update = True
                rankings.add_new_entry(initial_tid, pid)
                logger.info(
                    f"Initial rating to be revised"
                    f"\n{rankings[initial_tid, pid][['tid', 'pid', 'rating', 'category']]}\n"
                    f"{players[pid]['name']}"
                )
            elif rankings[initial_tid, pid, "rating"] < 0:
                # Will print available ratings of known players
                suggested_rating = helpers.suggest_initial_rating(
                    tournaments, players, rankings, name, tid
                )

                if suggested_rating > 0:
                    unknown_player_should_update = True
                    rankings[initial_tid, pid, "rating"] = suggested_rating
                    logger.info(
                        f"Filled with suggested ranking "
                        f"\n{rankings[initial_tid, pid][['tid', 'pid', 'rating', 'category']]}\n"
                        f"{players[pid]['name']}"
                    )
                else:
                    logger.info(
                        f"Initial rating to be revised"
                        f"\n{rankings[initial_tid, pid][['tid', 'pid', 'rating', 'category']]}\n"
                        f"{players[pid]['name']}"
                    )

        # FIXME Update config but do not affect initial tid
        # tournament_date = tournaments[tid].iloc[0].date.strftime("%y%m%d")
        # ConfigManager().set_current_config(date=tournament_date)
        # rankings.update_config()

    # Update the online version if an unknown player was found during preprocessing
    upload = unknown_player_should_update

    # Saving complete list of players, including new ones
    helpers.save_players_sheet(players, upload=upload)

    # Saving initial rankings for all known players
    rankings.update_categories(initial_tid)
    helpers.save_ranking_sheet(initial_tid, tournaments, rankings, players, upload=upload)

    helpers.save_to_pickle(players=players, tournaments=tournaments)
