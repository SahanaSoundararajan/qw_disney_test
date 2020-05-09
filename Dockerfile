FROM ubuntu:latest

RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip

ADD ./requirements.txt /src/requirements.txt
WORKDIR /src

RUN apt-get install -y git vim wget less

RUN pip3 install --trusted-host pypi.python.org -r requirements.txt
