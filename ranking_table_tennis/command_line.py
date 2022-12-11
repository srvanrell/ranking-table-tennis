import argparse
import logging
import os
import textwrap

from ranking_table_tennis.helpers.logging import logger


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
        "--log",
        help="Define the level of logging from string.",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
    )
    parser.add_argument(
        "--offline",
        help="Execute the given command locally. Compute is always offline.",
        action="store_true",
    )
    parser.add_argument(
        "--config-initial-date",
        help="Set the initial date to get the right configs and setup.",
        choices=["220101"],
        default="220101",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--last",
        help="Publish the last available tournament. Only valid if publish is given.",
        action="store_true",
    )
    group.add_argument(
        "--tournament-num",
        help="Publish the tournament number indicated. Only valid if publish is given.",
        type=int,
        default=None,
    )
    args = parser.parse_args()

    # assuming loglevel is bound to the string value obtained from the
    # command line argument. Convert to upper case to allow the user to
    # specify --log=DEBUG or --log=debug
    numeric_log_level = getattr(logging, args.log.upper())
    logger.setLevel(numeric_log_level)

    logger.debug("~ Working directory: '%s'", os.path.abspath(os.path.curdir))

    # FIXME calls are not performed in the best way.
    if args.cmd == "preprocess":
        from ranking_table_tennis import preprocess

        preprocess.main(args.offline, args.config_initial_date)
    elif args.cmd == "compute":
        from ranking_table_tennis import compute_rankings

        compute_rankings.main(args.config_initial_date)
    elif args.cmd == "publish":
        from ranking_table_tennis import publish

        publish.main(args.offline, args.last, args.tournament_num, args.config_initial_date)
    else:
        logger.error("you shouldn't see this message")


if __name__ == "__main__":
    main()
