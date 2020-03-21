# syntax = docker/dockerfile:experimental
ARG IMAGE=python:3.8.2-slim-buster

FROM $IMAGE
WORKDIR /work

ADD requirements.txt requirements-dev.txt .
RUN --mount=type=cache,target=/var/cache/pip,id=pip \
    pip install -r requirements.txt -r requirements-dev.txt

ADD xmpp_http_upload ./xmpp_http_upload
ADD demo ./demo
ADD setup.py tox.ini test.py ./

RUN ./test.py code-quality
RUN ./test.py test
