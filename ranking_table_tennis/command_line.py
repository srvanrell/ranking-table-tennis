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
            or
            automatic: combines (1) (2) (3) to resolve automatically
            """
        ),
        choices=["preprocess", "compute", "publish", "automatic"],
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
        help=(
            "Preprocessing is resolved unattended. "
            "--config-initial-date and --dont-download are the only valid param."
        ),
        action="store_true",
    )
    parser.add_argument(
        "--dont-download",
        help="Preprocessing unattended and dont't downloading tournaments.",
        action="store_true",
    )
    parser.add_argument(
        "--config-initial-date",
        help="Set the initial date to get the right configs and setup.",
        choices=[f"{YY % 100}0101" for YY in range(2021, datetime.now().year + 1)],
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

        preprocess_unattended.main(args.config_initial_date, not args.dont_download)
    elif args.cmd == "preprocess":
        from ranking_table_tennis import preprocess

        preprocess.main(args.offline, args.assume_yes, args.config_initial_date)
    elif args.cmd == "compute":
        from ranking_table_tennis import compute_rankings

        compute_rankings.main(args.config_initial_date)
    elif args.cmd == "publish":
        from ranking_table_tennis import publish

        publish.main(args.online_publish, args.last, args.tournament_num, args.config_initial_date)
    elif args.cmd == "automatic":
        from ranking_table_tennis import compute_rankings, preprocess_unattended, publish

        # Download and preprocess with no prev rankings
        preprocess_unattended.main(args.config_initial_date, download=True)
        # Computing ratings so suggestions to new players can be given and assigned
        compute_rankings.main(args.config_initial_date)
        # preprocessing twice to assign rating as much as possible
        preprocess_unattended.main(args.config_initial_date, download=False)
        # New players that played only with new players might not be resolved. Try it one more time
        preprocess_unattended.main(args.config_initial_date, download=False)
        # Computing ratings to publish
        compute_rankings.main(args.config_initial_date)
        # Publish last tournament
        publish.main(online=False, last=True, config_initial_date=args.config_initial_date)
    else:
        logger.error("you shouldn't see this message")


if __name__ == "__main__":
    main()
