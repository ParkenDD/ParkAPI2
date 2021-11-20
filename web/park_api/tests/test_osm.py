from .test_base import *


class TestOsm(TestBase):

    def test_osm_geojson(self):
        locations, snapshots = self.load_snapshot_data("jena")

        # create locations
        lot_models = store_location_data(locations)

        city = City.objects.get(osm_id="R62693")

        geojson_point = self.load_data("jena/jena.point.geojson")
        geojson_polygon = self.load_data("jena/jena.point.geojson")

        city.update_from_nominatim_geojson(geojson_point)
        city.update_from_nominatim_geojson(geojson_polygon)

        city.save()

