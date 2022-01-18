import json
import os
import datetime
from pathlib import Path
import argparse
import glob
import importlib
import inspect
import itertools
from typing import Union, Optional, Tuple, List, Type, Dict

from util import ScraperBase, SnapshotMaker, log
from util.validate import validate_snapshot


MODULE_DIR: Path = Path(__file__).resolve().parent


def parse_args() -> dict:

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

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "command", type=str,
        choices=["list", "scrape", "validate", "show-geojson", "write-geojson"],
        help="The command to execute",
    )
    parser.add_argument(
        "-p", "--pools", nargs="+", type=str,
        help=f"Filter for one or more pool IDs"
    )
    parser.add_argument(
        "-c", "--cache", nargs="?", type=cache_type, default=False, const=True,
        help=f"Enable caching of the web-requests. Specify '-c' to enable writing and reading cache"
             f", '-c read' to only read cached files or '-c write' to only write cache files"
             f" but not read them. Cache directory is {ScraperBase.CACHE_DIR}"
    )
    parser.add_argument(
        "-mp", "--max-priority", type=int, default=1000,
        help="Maximum error priority to display in validation [0-4]. 0 = severe, 1 = should really fix that"
             ", 2 = should fix that at some point, etc.."
    )

    return vars(parser.parse_args())


def get_scrapers(
        pool_filter: List[str],
) -> Dict[str, Type["ScraperBase"]]:

    scrapers = dict()
    all_scrapers = dict()

    for filename in itertools.chain(
            glob.glob(str(MODULE_DIR / "*.py")),
            glob.glob(str(MODULE_DIR / "*" / "*.py"))
    ):
        filename = Path(filename)
        if filename.parent.name in ("tests", "util"):
            continue

        module_name = str(filename.relative_to(MODULE_DIR))[:-3].replace(os.path.sep, ".")
        if module_name == "scraper":
            continue

        module = importlib.import_module(module_name)
        for key, scraper_class in vars(module).items():
            if not inspect.isclass(scraper_class) or not getattr(scraper_class, "POOL", None):
                continue

            # --- some validation of the POOL info ---

            if scraper_class.POOL.id in all_scrapers:
                raise ValueError(
                    f"{scraper_class.__name__}.POOL.id '{scraper_class.POOL.id}'"
                    f" is already used by class {all_scrapers[scraper_class.POOL.id].__name__}"
                )

            # --

            all_scrapers[scraper_class.POOL.id] = scraper_class

            if pool_filter and scraper_class.POOL.id not in pool_filter:
                continue

            scrapers[scraper_class.POOL.id] = scraper_class

    return scrapers


class JsonPrinter:
    def __init__(self):
        self.levels = 0
        self.first_entry = True

    def print(self, data: Union[list, dict]):
        if not self.first_entry:
            print(",")
        self.first_entry = False

        text = json.dumps(data, indent=2, ensure_ascii=False)

        if self.levels:
            text = "\n".join("  " * self.levels + line for line in text.splitlines())
        print(text, end="" if self.levels else "\n")

    def __enter__(self):
        """Start a list and indent all the following contents"""
        self.levels += 1
        print("[")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.levels -= 1
        print("\n]")


def main(
        command: str,
        cache: Union[bool, str],
        pools: List[str],
        max_priority: int,
):
    scrapers = get_scrapers(pool_filter=pools)
    pool_ids = sorted(scrapers)

    if command == "list":
        print(json.dumps(pool_ids, indent=2))

    elif command == "scrape":

        snapshots = []

        for pool_id in pool_ids:
            log(f"scraping pool '{pool_id}'")
            scraper = scrapers[pool_id](caching=cache)
            snapshotter = SnapshotMaker(scraper)
            snapshot = snapshotter.get_snapshot(infos_required=False)
            snapshots.append(snapshot)

        JsonPrinter().print(snapshots)

    elif command == "validate":

        validations = []

        for pool_id in pool_ids:
            log(f"scraping pool '{pool_id}'")
            scraper = scrapers[pool_id](caching=cache)
            snapshotter = SnapshotMaker(scraper)
            snapshot = snapshotter.get_snapshot(infos_required=False)

            validation = validate_snapshot(snapshot)
            for message in validation["validations"]:
                if message["priority"] <= max_priority:
                    validations.append({"pool_id": pool_id, "validation": message})

        JsonPrinter().print(validations)

    elif command in ("show-geojson", "write-geojson"):

        for pool_id in pool_ids:
            log(f"scraping pool '{pool_id}'")
            scraper = scrapers[pool_id](caching=cache)
            snapshotter = SnapshotMaker(scraper)
            snapshot = snapshotter.info_map_to_geojson(include_unknown=True)
            if command == "write-geojson":
                filename = Path(inspect.getfile(scraper.__class__)[:-3] + ".geojson")
                log("writing", filename)
                filename.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(snapshot, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(**parse_args())

