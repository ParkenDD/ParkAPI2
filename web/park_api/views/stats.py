import datetime
import math

from django import views
from django.shortcuts import render

from park_data.models import *


class StatsView(views.View):

    def get(self, request):
        param_hours = max(1, int(request.GET.get("hours") or 2))
        param_bucket_minutes = int(request.GET.get("bucket_minutes") or 5)
        param_field = request.GET.get("field") or "num_occupied"

        pool_qset = ParkingPool.objects.all()
        lot_qset = ParkingLot.objects.all()
        data_qset = ParkingData.objects.all()

        context = {
            "tables": [
                {
                    "name": "Pools",
                    "rows": [
                        ["all", pool_qset.count()],
                        ["with license", pool_qset.exclude(license=None).count()],
                    ]
                },
                {
                    "name": "Lots",
                    "rows": [
                        ["all", lot_qset.count()],
                        ["with coordinates", lot_qset.exclude(geo_point=None).count()],
                        ["with osm location", lot_qset.exclude(location=None).count()],
                        ["with live capacity", lot_qset.filter(has_live_capacity=True).count()],
                    ]
                },
                {
                    "name": "Data",
                    "rows": [
                        ["all", data_qset.count()],
                        ["with num_free", data_qset.exclude(num_free=None).count()],
                        ["with capacity", data_qset.exclude(capacity=None).count()],
                    ]
                }
            ],
            "pools": [],
            "fields": ["num_free", "num_occupied", "capacity"],
            "param_hours": param_hours,
            "param_bucket_minutes": param_bucket_minutes,
            "param_field": param_field,
        }

        # -- bucket latest data ---

        time_back = datetime.timedelta(hours=param_hours)
        bucket_width = min(time_back.total_seconds(), 60 * param_bucket_minutes)
        num_buckets = int(time_back.total_seconds() // bucket_width)

        context["plot_width"] = int(math.pow(num_buckets, .5) * 3)

        start_time = datetime.datetime.utcnow() - time_back
        all_lot_data = (
            ParkingData.objects.filter(timestamp__gte=start_time)
            .exclude(**{param_field: None})
            .values_list("lot__lot_id", "timestamp", param_field)
        )
        lot_data_map = dict()
        for lot_id, timestamp, num_free in all_lot_data:
            if lot_id not in lot_data_map:
                lot_data_map[lot_id] = [[-1, 0] for i in range(num_buckets)]
            bucket = int((timestamp - start_time).total_seconds() // bucket_width)
            if 0 <= bucket < num_buckets:
                lot_data_map[lot_id][bucket][0] = max(lot_data_map[lot_id][bucket][0], 0) + 1
                lot_data_map[lot_id][bucket][1] += num_free

        # --- calc mean ---

        lot_bucket_map = dict()
        for lot_id, buckets in lot_data_map.items():
            # get mean per bucket
            buckets = [b[1] / b[0] if b[0] > 0 else -1 for b in buckets]
            # normalize
            max_v = max(buckets)
            if max_v >= 0:
                lot_bucket_map[lot_id] = {
                    "buckets": [[b, round(100 - b * 100 / max_v, 2) if max_v else b] for b in buckets],
                    "max": max_v,
                }

        # -- pool and lot infos --
        for pool in pool_qset.order_by("pool_id").values("pk", "pool_id", "name"):
            context["pools"].append(pool)
            pool["lots"] = []
            for lot in lot_qset.filter(pool__pk=pool["pk"]).order_by("lot_id").values(
                    "pk", "lot_id", "name", "public_url", "address",
                    "geo_point", "location__city", "location__state",
            ):
                lot["data"] = lot_bucket_map.get(lot["lot_id"])
                pool["lots"].append(lot)

        return render(request, "park_api/stats.html", context)
