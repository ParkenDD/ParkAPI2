FROM ubuntu:bionic
# MAINTAINER Makina Corpus "contact@makina-corpus.com"
# from https://github.com/makinacorpus/docker-geodjango/blob/master/Dockerfile

ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8

RUN apt-get update -qq && apt-get install -y -qq \
    # std libs
    git less nano curl \
    ca-certificates \
    wget build-essential\
    # python basic libs
    python3.8 python3.8-dev python3.8-venv gettext \
    # geodjango
    gdal-bin binutils libproj-dev libgdal-dev \
    # postgresql
    libpq-dev postgresql-client
    ##&& \
    ##apt-get clean all && rm -rf /var/apt/lists/* && rm -rf /var/cache/apt/*

# link default python
RUN ln -s /usr/bin/python3.8 /usr/bin/python

# install pip
RUN wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py && rm get-pip.py
RUN pip3 install --no-cache-dir setuptools wheel -U

# --- install python packages ---

COPY ./requirements.txt /app/requirements.txt
WORKDIR /app/

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# --- copy code and run ---

COPY ./web /app
ENTRYPOINT ["/app/start-server.sh"]
