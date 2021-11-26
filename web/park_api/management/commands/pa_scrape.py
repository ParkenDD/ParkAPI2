import sys
import glob
import importlib
import json
import inspect
from pathlib import Path
import subprocess
from typing import List, Dict, Type, Union

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings

from park_data.models import store_snapshot


class Command(BaseCommand):
    help = 'Scrape all parking websites and store to database'

    def add_arguments(self, parser):
        def cache_type(a) -> Union[bool, str]:
            if isinstance(a, str):
                a = a.lower()
            if a == "true":
                return True
            elif a == "false":
                return False
            elif a in ("read", "write"):
                return a
            raise ValueError  # argparse does not display the exception message

        parser.add_argument(
            "-p", "--pools", nargs="+", type=str,
            help=f"Filter for one or more pool IDs"
        )
        parser.add_argument(
            "-c", "--cache", nargs="?", type=cache_type, default=False, const=True,
            help=f"ONLY FOR DEVELOPMENT!"
                 f" Enable caching of the web-requests. Specify '-c' to enable writing and reading cache"
                 f", '-c read' to only read cached files or '-c write' to only write cache files"
                 f" but not read them."
        )

    def handle(self, *args, **options):
        scrape(pool_filter=options["pools"], caching=options["cache"])


def scrape(pool_filter: List[str], caching: Union[bool, str]):
    scrapers_path = settings.BASE_DIR / "scrapers"
    for scraper_py in glob.glob(str(scrapers_path / "*/scraper.py")):

        run_scraper_process(path=Path(scraper_py).parent, pool_filter=pool_filter, caching=caching)


def run_scraper_process(
        path: Path,
        pool_filter: List[str],
        caching: Union[bool, str]
):
    args = [Path(sys.executable).resolve(), "scraper.py", "scrape"]
    if pool_filter:
        args += ["--pools", *pool_filter]
    if caching is True:
        args += ["--cache"]
    elif caching:
        args += ["--cache", caching]

    output = subprocess.check_output(args=args, cwd=str(path)).decode("utf-8")
    snapshots = json.loads(output)

    for snapshot in snapshots:
        store_snapshot(snapshot)


