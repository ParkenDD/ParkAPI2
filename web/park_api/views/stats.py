from django import views
from django.shortcuts import render

from park_data.models import *

class StatsView(views.View):

    def get(self, request):
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
            "pools": []
        }
        for pool in pool_qset.values("pk", "pool_id", "name"):
            context["pools"].append(pool)
            pool["lots"] = []
            for lot in lot_qset.filter(pool__pk=pool["pk"]).values("pk", "lot_id", "name", "geo_point"):
                pool["lots"].append(lot)

        return render(request, "park_api/stats.html", context)
