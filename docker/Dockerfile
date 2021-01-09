FROM ubuntu:18.04

# install requirements
COPY requirements.txt /tmp/requirements.txt
RUN apt-get update && apt-get install --yes python3-pip
RUN python3 -m pip install -r /tmp/requirements.txt
