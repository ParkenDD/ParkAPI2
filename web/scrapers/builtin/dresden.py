try:
    from scraper import *
except ImportError:
    from .scraper import *


class Dresden(ScraperBase):

    POOL = PoolInfo(
        id="dresden",
        name="Dresden",
        web_url="https://www.dresden.de/parken",
        source_url="https://www.dresden.de/apps_ext/ParkplatzApp/",
    )

    def get_lot_data(self) -> List[LotData]:
        now = self.now()
        soup = self.request_soup(self.POOL.source_url)

        last_updated = None
        for h3 in soup.find_all("h3"):
            if h3.text == "Letzte Aktualisierung":
                last_updated = self.convert_date(h3.find_next_sibling("div").text, "%d.%m.%Y %H:%M:%S")

        lots = []
        for table in soup.find_all("table"):
            thead = table.find("thead")
            if not thead:
                continue
            region = table.find("thead").find("tr").find_all("th")[1].find("div").text

            if region == "Busparkplätze":
                continue

            for tr in table.find("tbody").find_all("tr"):
                td = tr.find_all("td")
                name = tr.find("a").text

                try:
                    total = int(td[2].find_all("div")[1].text)
                except ValueError:
                    total = None
                try:
                    free = int(td[3].find_all("div")[1].text)
                    valid_free = True
                except ValueError:
                    valid_free = False
                    free = None
                if "park-closed" in td[0]["class"]:
                    state = "closed"
                elif "blue" in td[0]["class"] and not valid_free:
                    state = "nodata"
                else:
                    state = "open"

                lots.append(
                    LotData(
                        timestamp=now,
                        lot_timestamp=last_updated,
                        id=self.name_to_id(name),
                        status=state,
                        num_free=free,
                    )
                )

        return lots
