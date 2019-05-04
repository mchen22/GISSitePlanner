FROM python:3.7 AS base

ENV \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PIPENV_HIDE_EMOJIS=true \
    PIPENV_COLORBLIND=true \
    PIPENV_NOSPIN=true \
    PYTHONPATH="/app:${PYTHONPATH}"

ARG \
    CI_USER_TOKEN

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN echo -e "machine github.com\n  login $CI_USER_TOKEN" >> ~/.netrc

RUN apt-get update
RUN apt-get -qq -y install curl
RUN apt-get -qq -y install binutils libproj-dev gdal-bin
RUN apt-get -qq -y install libsqlite3-mod-spatialite
RUN pip install pipenv

RUN pipenv install

RUN echo -e "machine github.com\n  login " >> ~/.netrc


