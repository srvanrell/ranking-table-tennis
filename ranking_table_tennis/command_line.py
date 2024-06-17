import argparse
import logging
import os
import textwrap
from datetime import datetime

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
        "--online-publish",
        help="Execute publish to update online public sheets (not available since 2023).",
        action="store_true",
    )
    parser.add_argument(
        "--offline",
        help="Execute preprocessing command locally. Compute is always offline.",
        action="store_true",
    )
    parser.add_argument(
        "--assume-yes",
        help="Download sheet for preprocessing and upload updates. No questions are asked.",
        action="store_true",
    )
    parser.add_argument(
        "--unattended",
        help="Preprocessing is resolved unattended. --config-initial-date is the only valid param.",
        action="store_true",
    )
    parser.add_argument(
        "--config-initial-date",
        help="Set the initial date to get the right configs and setup.",
        choices=["240101", "230101", "220101", "210101"],
        default=datetime.today().strftime("%y0101"),
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
    if args.cmd == "preprocess" and args.unattended:
        from ranking_table_tennis import preprocess_unattended

        preprocess_unattended.main(args.config_initial_date)
    elif args.cmd == "preprocess":
        from ranking_table_tennis import preprocess

        preprocess.main(args.offline, args.assume_yes, args.config_initial_date)
    elif args.cmd == "compute":
        from ranking_table_tennis import compute_rankings

        compute_rankings.main(args.config_initial_date)
    elif args.cmd == "publish":
        from ranking_table_tennis import publish

        publish.main(args.online_publish, args.last, args.tournament_num, args.config_initial_date)
    else:
        logger.error("you shouldn't see this message")


if __name__ == "__main__":
    main()
