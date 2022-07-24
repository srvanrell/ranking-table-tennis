import difflib
import filecmp
import glob
import os
import shutil

import pytest
from conftest import assert_equals_xlsx, get_expected_folder_path

from ranking_table_tennis import compute_rankings, preprocess, publish
from ranking_table_tennis.configs import get_cfg

cfg = get_cfg()


@pytest.fixture(scope="module", autouse=True)
def run_before_tests():
    """To be run once before all tests"""
    example_data = os.path.join(get_expected_folder_path(), cfg.io.tournaments_filename)
    shutil.copy2(example_data, cfg.io.data_folder)
    preprocess.main()
    compute_rankings.main()
    for tn in range(1, 5):
        publish.main(tournament_num=tn)


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
