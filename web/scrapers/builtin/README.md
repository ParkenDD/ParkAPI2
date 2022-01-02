#### Example for a scraper module

The `scraper.py` file is a command-line tool for local testing as well
as a collection of utilities for implementing
website scrapers.

The idea is to fork the scraper repo which would only contain:
    
    README.md
    LICENSE.md
    requirements.txt
    schema.json
    scraper.py
    util/*.py
    test/*.py
    example.py 
    
    
Then contributors can create one or more *pools* by copying and implementing `example.py` 

```python
from typing import List
from util import *


class MyCity(ScraperBase):
    
    POOL = PoolInfo(
        id="my-city",
        name="My City",
        public_url="https://www.mycity.de/parken/",
        source_url="https://www.mycity.de/parken/auslastung/",
        attribution_license="...",
    )

    def get_lot_data(self) -> List[LotData]:
        timestamp = self.now()
        soup = self.request_soup(self.POOL.source_url)
        
        lots = []
        for div in soup.findall("div", {"class": "special-parking-div"}):

            # ... get info from html dom

            lots.append(
                LotData(
                    id=name_to_legacy_id("mycity", lot_id),
                    timestamp=timestamp,
                    lot_timestamp=last_updated,
                    status=state,
                    num_occupied=lot_occupied,
                    capacity=lot_total,
                )
            )

        return lots
```

and then test them via

```
python scraper.py list
python scraper.py scrape [--cache]
python scraper.py validate [--cache]
```

The optional `--cache` parameter simply caches all web requests which is a fair thing to do
during scraper development. If you have old cache files and want to create new ones
then run with `--cache write` to fire new web requests and write the new files and then
use `--cache` afterwards.

The `validate` command validates the resulting snapshot data against the 
[json schema](schema.json) and prints warnings for fields that *should* be defined.
Run `validate --max-priority 0` to only print severe errors and 
`validate --max-priority 1` to include warnings about missing data in the most
important fields like `latitude`, `longitude`, `address` and `capacity`. 


### Scraping occupancy data

The `get_lot_data` method must provide a list of `LotData` objects which 
are defined in [util/structs.py](util/structs.py). It's really basic and does not contain
any further information about the parking lot, only the status, free spaces and capacity.


### Scraping meta information

Additional lot information is taken from a [geojson](https://geojson.org/) which 
should have the same name as the scraper file, e.g. `example.geojson`. **If the file
exists**, it will be used and it's `properties` must fit the `util/structs/LotInfo` object.
**If it's not existing**, the method `get_lot_infos` on your scraper will be called which
should return all the required information. 

*Some* websites do provide most of the required information and it might be easier to
scrape it from the web pages instead of writing the geojson file by hand. However, it
might not be good practice to scrape this info every other minute. To generate a 
geojson file from the lot_info data:

```shell script
# delete the old file if it exists
rm example.geojson  
# run `get_lot_infos` and write to geojson 
#   (and filter for the `example` pool) 
python scraper.py write-geojson -p example
``` 

The command `show-geojson` will write the contents to stdout for inspection.


### Publishing

Once it's ready it can be *git submoduled* into the ParkAPI repo at `web/scrapers/`
and the main project will import the scrapers from all modules.

The `scraper.py` has a version number and if the schema changes, contributors 
need to merge with the original scraper repo at some point.

The `validate` command could actually validate the scraped data against the live API.
(e.g. check duplicate IDs and use newest schema, ...)
