import argparse
from ranking_table_tennis import preprocess, compute_rankings, publish


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess, compute, and publish table tennis rankings. "
        "Commands must be given in the right order!! They are splitted for usage simplicity."
    )
    parser.add_argument(
        "cmd",
        help="(1) preprocess: downloads tournament data and preprocess it.\n"
        "(2) compute: generates rankings from preprocessed data.\n"
        "(3) publish: provides formatted spreadsheets to upload rankings",
        choices=["preprocess", "compute", "publish"],
    )
    args = parser.parse_args()

    # FIXME calls are not performed in the best way.
    if args.cmd == "preprocess":
        preprocess.main()
    elif args.cmd == "compute":
        compute_rankings.main()
    elif args.cmd == "publish":
        publish.main()
    else:
        print("you shouldn't see this message")


if __name__ == "__main__":
    main()
