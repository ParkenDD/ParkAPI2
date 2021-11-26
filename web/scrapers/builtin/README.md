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
    example.py 
    
    
Then people can create one or more *pools* by copying and implementing `example.py` 

```python
from util import *

class MyCity(ScraperBase):
    
    POOL = PoolInfo(
        id="my-city",
        name="My own City",
        public_url="https://www.mycity.de/parken",
        source_url="https://www.mycity.de/api/parking/",
    )

    def get_lot_data(self) -> List[LotData]:
        soup = self.request_soup(self.POOL.source_url)
        ...
        return extracted_data
```

and then test them via

```
python scraper.py list
python scraper.py scrape [--cache]
python scraper.py validate [--cache]
```

Once it's ready it can be *git submoduled* into the ParkAPI repo at `web/scrapers/`
and the main project will import the scrapers from all modules.

The `scraper.py` has a version number and if the schema changes, contributers 
need to merge with the original scraper repo at some point.

The `validate` command could actually validate the scraped data against the live API.
(e.g. check duplicate IDs and use newest schema, ...)

