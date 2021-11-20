FROM python:3.7-alpine

# --- install packages ---

RUN apk add bash gcc musl-dev libffi-dev openssl-dev python3-dev postgresql-dev gettext jpeg-dev zlib-dev

# --- install python packages ---

COPY ./web/requirements.txt /app/requirements.txt
WORKDIR /app/

RUN pip install -r requirements.txt

# --- copy code and run ---

COPY ./web /app
ENTRYPOINT ["/app/start-server.sh"]
