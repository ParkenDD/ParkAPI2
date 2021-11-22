import warnings
from typing import Union

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from osm_locations.models import OSMLocation
from park_data.nominatim import NominatimApi


class Command(BaseCommand):
    help = 'Query Nominatim data for all OSMLocation models that do not have the data yet'

    def add_arguments(self, parser):
        parser.add_argument(
            "-f", "--force", type=bool, nargs="?", default=False, const=True,
            help="Query update of all OSMLocations. Note that this can take a while!",
        )
        parser.add_argument(
            "-cp", "--create-parents", type=bool, nargs="?", default=False, const=True,
            help="Automatically create parent objects if they do not exist yet",
        )

    def handle(self, *args, create_parents: bool, force: bool, **options):
        update_osm_locations_from_nominatim(force=force, print_to_console=True)
        if create_parents:
            create_osm_location_parents(print_to_console=True)


def update_osm_locations_from_nominatim(
        force: bool = False,
        batch_size: int = 10,
        caching: Union[bool, str] = True,
        print_to_console: bool = False,
):
    qset = OSMLocation.objects.all()
    if not force:
        qset = (
            qset.filter(osm_feature_type=None)
            | qset.filter(geo_point=None)
            | qset.filter(geo_polygon=None)
        )

    all_osm_ids = list(qset.values_list("osm_id", flat=True))

    if print_to_console:
        if not all_osm_ids:
            print("All updated")
        else:
            print(f"Updating {len(all_osm_ids)} locations")

    if not all_osm_ids:
        return

    api = NominatimApi(verbose=print_to_console)

    while all_osm_ids:
        # take a batch of the IDs
        osm_ids = all_osm_ids[:batch_size]
        all_osm_ids = all_osm_ids[batch_size:]

        geojson_point = api.lookup(
            osm_ids=osm_ids,
            format="geojson",
            extratags=0,
            addressdetails=0,
            namedetails=0,
            polygon_geojson=0,
            caching=caching,
        )

        geojson_poly = api.lookup(
            osm_ids=osm_ids,
            format="geojson",
            extratags=1,
            addressdetails=1,
            namedetails=1,
            polygon_geojson=1,
            caching=caching,
        )

        with transaction.atomic():
            for osm_id in osm_ids:
                location_model = OSMLocation.objects.get(osm_id=osm_id)
                location_model.update_from_nominatim_geojson(geojson_point)
                location_model.update_from_nominatim_geojson(geojson_poly)
                location_model.save()
                if print_to_console:
                    print(f"updated {location_model}")


def create_osm_location_parents(
        caching: Union[bool, str] = True,
        print_to_console: bool = False,
):
    any_updated = False
    for i in range(4):
        updated = _create_osm_location_parents_impl(caching=caching, print_to_console=print_to_console)
        any_updated |= updated
        if not updated:
            break
    
    if any_updated:
        update_osm_locations_from_nominatim(print_to_console=print_to_console)


def _create_osm_location_parents_impl(
        caching: Union[bool, str] = True,
        print_to_console: bool = False,
) -> bool:
    FOLLOWED_ADDRESS_KEYS = ("suburb", "city", "state", "country")

    # get all objects that have OSM data but no place_rank
    #   (but exclude countries)
    qset = (
        OSMLocation.objects.filter(osm_parent=None)
        .exclude(osm_place_rank=None)
        .exclude(osm_linked_place="country")
    )
    all_osm_ids = list(qset.values_list("osm_id", flat=True))

    if print_to_console:
        if not all_osm_ids:
            print("All parents defined")
        else:
            print(f"Searching {len(all_osm_ids)} parents")

    if not all_osm_ids:
        return False

    api = NominatimApi(verbose=print_to_console)
    num_updates = 0

    for osm_id in all_osm_ids:
        osm_location = OSMLocation.objects.get(osm_id=osm_id)
        if not osm_location.osm_properties or not osm_location.osm_properties.get("address"):
            warnings.warn(
                f"No address data for {osm_location}"
            )
            continue

        address = osm_location.osm_properties["address"]

        for key in FOLLOWED_ADDRESS_KEYS:
            if key not in address:
                continue
            value = address[key]

            # see if we find an existing object by name
            existing_qset = OSMLocation.objects.filter(
                osm_properties__extratags__linked_place=key,
                name=value,
            )
            if existing_qset.exists():
                osm_parent_model = existing_qset[0]
                if osm_parent_model.osm_place_rank < osm_location.osm_place_rank:
                    osm_location.osm_parent = osm_parent_model
                    osm_location.save()
                    break

            # search for the 'suburb', 'city', etc...
            geojson = api.search(
                **{key: value},
                format="geojson",
                extratags=1,
                addressdetails=1,
                namedetails=1,
                countrycodes=[address["country_code"]],
                #polygon_geojson=1,
                caching=caching,
            )

            if not geojson.get("features"):
                if print_to_console:
                    print(f"No result for search {key}={value}, countrycode={address['country_code']}")
                continue

            if len(geojson["features"]) > 1:
                warnings.warn(
                    f"nominatim search result for {key}={value}, countrycode={address['country_code']}"
                    f" returned more than one result:\n{geojson}"
                )
                continue

            feature = geojson["features"][0]

            # skip objects that are below or equal in the hierarchy
            if feature["properties"].get("place_rank"):
                if feature["properties"]["place_rank"] >= osm_location.osm_place_rank:
                    continue

            try:
                osm_parent_model = OSMLocation.objects.get(osm_id=feature["properties"]["osm_id"])
            except OSMLocation.DoesNotExist:
                osm_parent_model = OSMLocation.create_from_nominatim_geojson_feature(feature)
                print(f"created new parent location {osm_parent_model}")

            osm_location.osm_parent = osm_parent_model
            osm_location.save()
            num_updates += 1
            break

    return num_updates > 0
