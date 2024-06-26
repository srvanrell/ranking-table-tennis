from conftest import (
    assert_equals_xlsx,
    base_cli_run_after_tests,
    base_run_before_tests,
    config_initial_date_for_cli,
    get_expected_folder_path,
)
from pandas.testing import assert_frame_equal

from ranking_table_tennis import helpers
from ranking_table_tennis.configs import ConfigManager


def test_cli_preprocess_run_before_tests(shell):
    """To be run once before all tests"""
    base_run_before_tests()
    # Repeat twice, it should provide consistent results
    for _ in range(2):
        ret = shell.run("rtt", "preprocess", "--offline", *config_initial_date_for_cli())
        assert ret.returncode == 0
        print(ret.stdout)
    base_cli_run_after_tests()


def test_cli_preprocess_xlsx_output():
    """Compare xlsx preprocessed between expected and output folder"""
    cfg = ConfigManager().current_config
    assert_equals_xlsx(
        get_expected_folder_path(), cfg.io.data_folder, cfg.io.xlsx.tournaments_filename
    )


def test_cli_preprocess_outputs_players_and_histories(ref_players_df):
    cfg = ConfigManager().current_config
    # Load output from preprocess
    players_output = helpers.load_from_pickle(cfg.io.pickle.players)

    assert_frame_equal(players_output.players_df, ref_players_df)
    assert players_output.history_df.empty


def test_cli_preprocess_outputs_tournaments(ref_tournaments_df):
    cfg = ConfigManager().current_config
    # Load output from preprocess
    tournaments_output = helpers.load_from_pickle(cfg.io.pickle.tournaments)

    assert_frame_equal(tournaments_output.tournaments_df, ref_tournaments_df)
