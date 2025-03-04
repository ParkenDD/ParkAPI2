FROM ghcr.io/osgeo/gdal:alpine-small-3.9.2 AS builder
LABEL maintainer="Holger Bruch <hb@mfdz.de>"

RUN apk add --no-cache build-base python3-dev py3-pip postgresql-client libpq-dev geos-dev


RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY requirements.txt .
COPY web/scrapers/ParkAPI2_sources/requirements.txt ./ParkAPI2_sources_requirements.txt

RUN pip install -r requirements.txt -r ParkAPI2_sources_requirements.txt

# Operational stage
FROM ghcr.io/osgeo/gdal:alpine-small-3.9.2
LABEL maintainer="Holger Bruch <hb@mfdz.de>"

RUN apk add --no-cache bash git python3 py3-pip postgresql-client geos

COPY --from=builder /opt/venv /opt/venv
ENV RUN_MIGRATION=0 \
    CREATE_SUPERUSER=0 \
    ASSIGN_LOCATIONS=0 \
    PYTHONBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY . /app/

EXPOSE 8000
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
CMD runserver 0.0.0.0:8000
