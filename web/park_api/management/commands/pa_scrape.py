import sys
import glob
import importlib
import json
import inspect
from pathlib import Path
import subprocess
from multiprocessing.pool import ThreadPool
from typing import List, Dict, Type, Union, Generator

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
            "command", type=str,
            choices=["list", "scrape"],
            help="Command to execute"
        )
        parser.add_argument(
            "-p", "--pools", nargs="+", type=str,
            help="Filter for one or more pool IDs"
        )
        parser.add_argument(
            "-c", "--cache", nargs="?", type=cache_type, default=False, const=True,
            help="ONLY FOR DEVELOPMENT!"
                 " Enable caching of the web-requests. Specify '-c' to enable writing and reading cache"
                 ", '-c read' to only read cached files or '-c write' to only write cache files"
                 " but not read them."
        )
        parser.add_argument(
            "-j", "--processes", type=int, default=1,
            help="Scrape in N parallel processes"
        )

    def handle(self, *args, command: str, pools, cache, processes, **options):
        if command == "list":
            scraper_pools = dict()
            for scraper_py in iter_scrapers():
                scraper_pools[scraper_py.parent.name] = run_scraper_process(
                    path=scraper_py.parent, command="list", pool_filter=pools, caching=cache
                )
            print(json.dumps(scraper_pools, indent=2))

        elif command == "scrape":
            if processes > 1:
                scrape_parallel(pool_filter=pools, caching=cache, processes=processes)
            else:
                scrape(pool_filter=pools, caching=cache)

        else:
            raise ValueError(f"Invalid command '{command}'")


def iter_scrapers() -> Generator[Path, None, None]:
    scrapers_path = settings.BASE_DIR / "scrapers"
    for scraper_py in glob.glob(str(scrapers_path / "*/scraper.py")):
        yield Path(scraper_py)


def scrape(pool_filter: List[str], caching: Union[bool, str]):
    for scraper_py in iter_scrapers():
        snapshots = run_scraper_process(
            path=scraper_py.parent, command="scrape", pool_filter=pool_filter, caching=caching
        )
        store_snapshots(snapshots, pool_filter)


def store_snapshots(snapshots: Union[list, dict], pool_filter):
    if isinstance(snapshots, dict) and snapshots.get("error"):
        print(f"\n\nERROR scraping pools {pool_filter}:\n {snapshots['error']}")
        # TODO: should store errors per scraper module to database
    else:
        for snapshot in snapshots:
            if snapshot.get("error"):
                print(f"\n\nERROR in pool {snapshot['pool']['id']}:\n {snapshot['error']}")
                # TODO: should store errors per pool to database
            else:
                store_snapshot(snapshot)


def scrape_parallel(pool_filter: List[str], caching: Union[bool, str], processes: int):
    scraper_commands = []
    for scraper_py in iter_scrapers():
        pool_ids = run_scraper_process(
            path=scraper_py.parent, command="list", pool_filter=pool_filter, caching=caching
        )
        if pool_ids:
            for pool_id in pool_ids:
                scraper_commands.append([scraper_py.parent, pool_id])

    if not scraper_commands:
        return

    snapshots = ThreadPool(processes).map(
        lambda args: run_scraper_process(path=args[0], command="scrape", pool_filter=[args[1]], caching=caching),
        scraper_commands,
    )
    for sn, (path, pool_id) in zip(snapshots, scraper_commands):
        store_snapshots(sn, pool_filter=[pool_id])


def run_scraper_process(
        path: Path,
        command: str,
        pool_filter: List[str],
        caching: Union[bool, str],
) -> Union[dict, list]:

    args = [Path(sys.executable).resolve(), "scraper.py", command]
    if pool_filter:
        args += ["--pools", *pool_filter]
    if caching is True:
        args += ["--cache"]
    elif caching:
        args += ["--cache", caching]

    process = subprocess.Popen(
        args=args,
        cwd=str(path),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        output = process.stdout.read()
        return json.loads(output.decode("utf-8"))
    except json.JSONDecodeError:
        return {
            "error": process.stderr.read()
        }


