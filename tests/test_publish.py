import glob
import shutil
import pytest
from ranking_table_tennis import preprocess, compute_rankings, publish
from ranking_table_tennis.configs import cfg
import filecmp
import difflib
import os
import pandas as pd


@pytest.fixture(scope="module", autouse=True)
def run_before_tests():
    """To be run once before all tests"""
    example_data = os.path.join(
        os.path.dirname(__file__), "data_up_to_S2022T04", cfg.io.tournaments_filename
    )
    shutil.copy2(example_data, cfg.io.data_folder)
    preprocess.main()
    compute_rankings.main()
    for tn in range(1, 5):
        publish.main(tournament_num=tn)


def assert_equals_xlsx(reference_folder, output_folder, name_pattern):
    expected_folder_path = os.path.relpath(reference_folder)
    filenames = glob.glob(os.path.join(expected_folder_path, name_pattern))
    filenames = [fn.replace(expected_folder_path + "/", "") for fn in filenames]

    for fn in filenames:
        dfs_expected = pd.read_excel(os.path.join(expected_folder_path, fn), sheet_name=None)
        dfs_output = pd.read_excel(os.path.join(output_folder, fn), sheet_name=None)

        assert sorted(dfs_expected.keys()) == sorted(dfs_output.keys()), "Sheetname differences"

        for name, df in dfs_expected.items():
            assert df.equals(dfs_output[name]), f"Mismatch on {name} sheet"


def get_expected_folder_path():
    return os.path.join(os.path.dirname(__file__), "data_up_to_S2022T04")


def test_publish_xlsx_to_publish_outputs():
    """Compare all xlsx to publish between folders"""
    assert_equals_xlsx(get_expected_folder_path(), cfg.io.data_folder, "*publicar.xlsx")


def test_publish_xlsx_raw_rankings_outputs():
    # Creates the list of xlsx files to compare
    assert_equals_xlsx(get_expected_folder_path(), cfg.io.data_folder, "raw_ranking*.xlsx")


def test_publish_markdown_outputs():
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
