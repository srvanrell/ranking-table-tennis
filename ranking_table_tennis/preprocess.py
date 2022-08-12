from urllib import request

from ranking_table_tennis import helpers
from ranking_table_tennis.configs import ConfigManager


def main(offline=True):
    """Preprocess matches on xlsx tournaments database.

    Function to run before compute_rankings.main().
    It will use xlsx tournaments database and config.yaml.
    It will output xlsx tournaments database updated.
    It will save players and tournaments in pickles.

    It looks for unknown or unrated players.
    It will ask for information not given and saves the result into the same xlsx

    If offline=True it will execute preprocessing locally (not retrieving or uploading updates).
    """
    print("\n## Starting preprocess\n")

    ConfigManager().set_current_config(date="220101")
    cfg = ConfigManager().current_config

    xlsx_file = cfg.io.data_folder + cfg.io.xlsx.tournaments_filename

    if not offline:
        retrieve = input("Do you want to retrieve online sheet [Y/n]? (press Enter to continue)\n")
        if retrieve.lower() != "n":
            print("Downloading and saving %s\n" % xlsx_file)
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

    # Loading temp ranking and players. It will be deleted after a successful preprocessing
    players_temp, ranking_temp = helpers.load_temp_players_ranking()

    for tid in tournaments:
        print("==", tid, "==")

        for name in tournaments.get_players_names(tid):
            unknown_player = False
            if players.get_pid(name) is None:
                if players_temp.get_pid(name) is None:
                    unknown_player = True
                    association = input("\nEnter the affiliation of %s: (optional field)\n" % name)
                    city = input("\nEnter the city of %s: (optional field)\n" % name)
                    # Assign a pid for the new given player and add it to the list
                    players.add_new_player(name, association, city)
                    # Save a temp player to resume preprocessing, if necessary
                    players_temp.add_player(players[players.get_pid(name)])
                else:
                    print(">>>>\tUNCOMPLETE preprocessing detected. Resuming...")
                    players.add_player(players_temp[players_temp.get_pid(name)])
                print(f"\n{players[players.get_pid(name)]}\n")

            pid = players.get_pid(name)

            # Category will be asigned
            if rankings[initial_tid, pid] is None:
                if ranking_temp[initial_tid, pid] is None:
                    unknown_player = True

                    # Will print available ratings of known players
                    helpers.print_rating_context(tournaments, players, name, tid)

                    text_to_show = f"\nEnter the initial rating points for {name}"
                    text_to_show += " (category will be auto-assigned):\n"
                    initial_rating = int(input(text_to_show))
                    rankings.add_new_entry(initial_tid, pid, initial_rating)
                    # Save a temp ranking of the player to resume preprocessing, if necessary
                    ranking_temp.add_entry(rankings[initial_tid, pid])
                else:
                    print(">>>>\tUNCOMPLETE preprocessing detected. Resuming...")
                    rankings.add_entry(ranking_temp[initial_tid, pid])

                print(
                    f"\n{rankings[initial_tid, pid][['tid', 'pid', 'rating', 'category']]}\n"
                    f"{players[pid]['name']}"
                )

            if unknown_player:
                retrieve = input(
                    "press Enter to continue or Kill this process to forget last player data\n"
                )
                helpers.save_temp_players_ranking(players_temp, ranking_temp)

    # Update the online version
    upload = False
    if not offline:
        answer = input("\nDo you want to update online sheets [Y/n]? (press Enter to continue)\n")
        upload = answer.lower() != "n"

    # Saving complete list of players, including new ones
    helpers.save_players_sheet(players, upload=upload)

    # Saving initial rankings for all known players
    rankings.update_categories()
    helpers.save_ranking_sheet(initial_tid, tournaments, rankings, players, upload=upload)

    # Remove temp files after a successful preprocessing
    helpers.remove_temp_players_ranking()

    helpers.save_to_pickle(players=players, tournaments=tournaments)
