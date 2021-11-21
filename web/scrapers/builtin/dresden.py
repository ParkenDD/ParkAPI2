try:
    from scraper import ScraperBase
except ImportError:
    from .scraper import ScraperBase


class Dresden(ScraperBase):

    POOL_ID = "dresden"

    def scrape(self) -> dict:
        soup = self.request_soup(
            "https://www.dresden.de/apps_ext/ParkplatzApp/"
        )

        last_updated = None
        for h3 in soup.find_all("h3"):
            if h3.text == "Letzte Aktualisierung":
                last_updated = self.convert_date(h3.find_next_sibling("div").text, "%d.%m.%Y %H:%M:%S")

        data = {
            "lots": [],
            "timestamp": self.now(),
            "last_updated": last_updated
        }
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

                #lot = geodata.lot(name)

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

                data["lots"].append({
                    #"coords": lot.coords,
                    "name": name,
                    "total": total,
                    "free": free,
                    "state": state,
                    #"id": lot.id,
                    #"lot_type": lot.type,
                    #"address": lot.address,
                    #"forecast": os.path.isfile("forecast_data/" + lot.id + ".csv"),
                    "region": region
                })
        return data
