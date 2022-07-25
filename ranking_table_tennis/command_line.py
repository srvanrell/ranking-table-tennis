import argparse
import textwrap

from ranking_table_tennis import compute_rankings, preprocess, publish


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess, compute, and publish table tennis rankings. "
        "Commands must be given in the right order!! They are splitted for usage simplicity.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "cmd",
        help=textwrap.dedent(
            """\
            (1) preprocess: downloads tournament data and preprocess it
            (2) compute: generates rankings from preprocessed data
            (3) publish: provides formatted spreadsheets to upload rankings
            """
        ),
        choices=["preprocess", "compute", "publish"],
    )
    parser.add_argument(
        "--offline",
        help="Execute the given command locally. Compute is always offline.",
        action="store_true",
    )
    parser.add_argument(
        "--last",
        help="Publish the last available tournament. Only valid if publish is given.",
        action="store_true",
    )
    args = parser.parse_args()

    # FIXME calls are not performed in the best way.
    if args.cmd == "preprocess":
        preprocess.main(args.offline)
    elif args.cmd == "compute":
        compute_rankings.main()
    elif args.cmd == "publish":
        publish.main(args.offline, args.last)
    else:
        print("you shouldn't see this message")


if __name__ == "__main__":
    main()
