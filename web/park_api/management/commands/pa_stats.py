import datetime
from typing import Optional, List

from django.core.management.base import BaseCommand, CommandError
from django.db.models import QuerySet

from park_data.models import *


class Command(BaseCommand):
    help = 'Show database statistics'

    def add_arguments(self, parser):
        parser.add_argument(
            "-t", "--time", type=str, nargs="?", default=None,
            help="Only display last N (m)inutes, (h)ours, (d)ays",
        )
        parser.add_argument(
            "-p", "--pools", nargs="+", type=str,
            help="Filter for one or more pool IDs"
        )

    def handle(self, *args, verbosity, time: Optional[str], pools: List[str], **options):
        dump_stats(time=time, pools=pools, verbosity=verbosity or 1)


def dump_stats(time: Optional[str], pools: List[str], verbosity: int):
    max_list = 20

    start_time = None
    if time is not None:
        value, unit = int(time[:-1]), time[-1]
        if unit == "m":
            delta = datetime.timedelta(minutes=value)
        elif unit == "h":
            delta = datetime.timedelta(hours=value)
        elif unit == "d":
            delta = datetime.timedelta(days=value)
        else:
            raise ValueError(f"Invalid --time '{time}' parameter.")
        start_time = (datetime.datetime.utcnow() - delta).replace(microsecond=0)

    pool_qset = ParkingPool.objects.all()
    lot_qset = ParkingLot.objects.all()
    data_qset = ParkingData.objects.all()
    error_qset = ErrorLog.objects.all()

    if pools:
        pool_qset = pool_qset.filter(pool_id__in=pools)
        lot_qset = lot_qset.filter(pool__pool_id__in=pools)
        data_qset = data_qset.filter(lot__pool__pool_id__in=pools)
        error_qset = error_qset.filter(pool_id__in=pools)

    if start_time:
        data_qset = data_qset.filter(timestamp__gte=start_time)
        error_qset = error_qset.filter(timestamp__gte=start_time)

        lot_ids = data_qset.values_list("lot__lot_id", flat=True).distinct()
        lot_qset = lot_qset.filter(lot_id__in=lot_ids)

        pool_ids = set(lot_qset.values_list("pool__pool_id", flat=True))
        pool_ids |= set(error_qset.exclude(pool_id=None).values_list("pool_id", flat=True).distinct())
        pool_qset = pool_qset.filter(pool_id__in=pool_ids)

    if start_time:
        print(f"\nSince {start_time}")

    print("\nPools")
    print("  all:                {:9,d}".format(pool_qset.count()))
    print("  with license:       {:9,d}".format(pool_qset.exclude(attribution_license=None).count()))

    if verbosity > 1:
        print()
        for model in pool_qset.order_by("pool_id")[:max_list]:
            print("   ", model)

    print("\nLots")
    print("  all:                {:9,d}".format(lot_qset.count()))
    print("  with coordinates:   {:9,d}".format(lot_qset.exclude(geo_point=None).count()))
    print("  with location:      {:9,d}".format(lot_qset.exclude(location=None).count()))
    print("  with live capacity: {:9,d}".format(lot_qset.filter(has_live_capacity=True).count()))

    if verbosity > 1:
        print()
        for model in lot_qset.order_by("lot_id")[:max_list]:
            print("   ", model)

    print("\nData")
    print("  all:                {:9,d}".format(data_qset.count()))
    print("  with capacity:      {:9,d}".format(data_qset.exclude(capacity=None).count()))
    print("  with num_free:      {:9,d}".format(data_qset.exclude(num_free=None).count()))
    print("  timestamps:         {} - {}".format(
        data_qset.order_by("timestamp")[0].timestamp,
        data_qset.order_by("-timestamp")[0].timestamp,
    ))

    if verbosity > 1:
        print()
        for model in data_qset.order_by("-timestamp")[:max_list]:
            print("   ", model)

    print("\nErrors")
    print("  all:                {:9d}".format(error_qset.count()))
    print("  modules:            {:9d}".format(error_qset.filter(pool_id=None).count()))
    print("  pools:              {:9d}".format(error_qset.exclude(pool_id=None).count()))

    if verbosity > 1:
        print()
        for model in error_qset.order_by("-timestamp")[:max_list]:
            print("   ", model)
