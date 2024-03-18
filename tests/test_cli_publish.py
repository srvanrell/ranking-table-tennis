import difflib
import filecmp
import glob
import os

from conftest import (
    assert_equals_xlsx,
    base_cli_run_after_tests,
    base_run_before_tests,
    config_initial_date_for_cli,
    get_expected_folder_path,
)

from ranking_table_tennis.configs import ConfigManager


def test_cli_publish_run_before_tests(shell):
    """To be run once before all tests"""
    base_run_before_tests()
    ret = shell.run("rtt", "preprocess", "--offline", *config_initial_date_for_cli())
    assert ret.returncode == 0
    print(ret.stdout)
    ret = shell.run("rtt", "compute", *config_initial_date_for_cli())
    assert ret.returncode == 0
    print(ret.stdout)
    # Repeat twice, it should provide consistent results
    for tn in range(1, 5):
        for _ in range(2):
            ret = shell.run(
                "rtt", "publish", "--tournament-num", str(tn), *config_initial_date_for_cli()
            )
            assert ret.returncode == 0
            print(ret.stdout)
    base_cli_run_after_tests()


def test_cli_publish_xlsx_to_publish_outputs():
    """Compare all xlsx to publish between folders"""
    cfg = ConfigManager().current_config
    assert_equals_xlsx(get_expected_folder_path(), cfg.io.data_folder, "*publicar.xlsx")


def test_cli_publish_xlsx_raw_rankings_outputs():
    cfg = ConfigManager().current_config
    # Creates the list of xlsx files to compare
    assert_equals_xlsx(get_expected_folder_path(), cfg.io.data_folder, "raw_ranking*.xlsx")


def test_cli_publish_markdown_outputs():
    cfg = ConfigManager().current_config
    # Creates the list of markdown files to compare
    expected_folder_path = os.path.relpath(get_expected_folder_path())
    filenames = glob.glob(os.path.join(expected_folder_path, "S2022T0*", "*.md"))
    filenames = [fn.replace(expected_folder_path + "/", "") for fn in filenames]

    # Compare them and obtain filename lists of match, mismatch, or errors
    match, mismatch, errors = filecmp.cmpfiles(expected_folder_path, cfg.io.data_folder, filenames)

    # Print mismatch to ease debugging
    for filename in mismatch:
        with open(os.path.join(expected_folder_path, filename)) as exp_f:
            with open(os.path.join(cfg.io.data_folder, filename)) as out_f:
                diff = difflib.ndiff(exp_f.readlines(), out_f.readlines())
                print("".join(diff), end="")

    # Assert for errors, messages to help debugging
    ftmstr = f"{len(match)} match, {len(mismatch)} mismatch, {len(errors)} errors"
    assert match, f"No matching. Results: {ftmstr}"
    assert not mismatch, f"Content mismatch of files. Results: {ftmstr}"
    assert not errors, f"Error reading or finding files. Results: {ftmstr}"
