import glob
import pytest
from ranking_table_tennis import preprocess, compute_rankings, publish
from ranking_table_tennis.configs import cfg
import filecmp
import difflib
import os


@pytest.fixture(scope="module", autouse=True)
def run_before_tests():
    """To be run once before all tests"""
    preprocess.main()
    compute_rankings.main()
    for tn in range(1, 5):
        publish.main(tournament_num=tn)


def get_expected_folder_path():
    return os.path.join(os.path.dirname(__file__), "data_up_to_S2022T04")


def test_publish_xlsx_to_publish_outputs():
    """Compare all xlsx to publish between folders"""
    pass


def test_publish_xlsx_raw_rankings_outputs():
    filenames = glob.glob(
        os.path.join(os.path.dirname(__file__), "data_up_to_S2022T04", "S2022T0*", "*.md")
    )
    for fn in filenames:
        with open(fn, "r+") as fileo:
            lines = fileo.readlines()
            print("...", fn)
            print(lines[-1:])
            lines[-1] = lines[-1][:-1]
            print(lines[-1:])
            print("---")
            fileo.writelines(lines)
    pass


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
