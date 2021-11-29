import json
import datetime
from pathlib import Path
import argparse
import glob
import importlib
import inspect
from typing import Union, Optional, Tuple, List, Type, Dict

from util import ScraperBase, SnapshotMaker, log


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
        choices=["list", "scrape", "show-geojson", "write-geojson"],
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

    return vars(parser.parse_args())


def get_scrapers(
        pool_filter: List[str],
) -> Dict[str, Type["ScraperBase"]]:

    scrapers = dict()
    for filename in glob.glob(str(MODULE_DIR / "*.py")):
        module_name = Path(filename).name[:-3]
        if module_name == "scraper":
            continue

        module = importlib.import_module(module_name)
        for key, value in vars(module).items():
            if not inspect.isclass(value) or not getattr(value, "POOL", None):
                continue

            if value.POOL.id in scrapers:
                raise ValueError(
                    f"class {value.__name__}.POOL.id '{value.POOL.id}'"
                    f" is already used by class {scrapers[value.POOL.id].__name__}"
                )

            if pool_filter and value.POOL.id not in pool_filter:
                continue

            scrapers[value.POOL.id] = value

    return scrapers


def main(
        command: str,
        cache: Union[bool, str],
        pools: List[str],
):
    scrapers = get_scrapers(pool_filter=pools)
    pool_ids = sorted(scrapers)

    if command == "list":
        print(json.dumps(pool_ids, indent=2))

    elif command == "scrape":

        print("[")
        for pool_id in pool_ids:
            log(f"scraping pool '{pool_id}'")
            scraper = scrapers[pool_id](caching=cache)
            snapshot = SnapshotMaker(scraper)
            data = snapshot.get_snapshot(infos_required=False)

            comma = "," if pool_id != pool_ids[-1] else ""
            print(json.dumps(data, indent=2, ensure_ascii=False) + comma)
        print("]")

    elif command in ("show-geojson", "write-geojson"):

        for pool_id in pool_ids:
            log(f"scraping pool '{pool_id}'")
            scraper = scrapers[pool_id](caching=cache)
            snapshot = SnapshotMaker(scraper)
            data = snapshot.info_map_to_geojson(include_unknown=True)
            if command == "write-geojson":
                filename = Path(inspect.getfile(scraper.__class__)[:-3] + ".geojson")
                log("writing", filename)
                filename.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(**parse_args())

