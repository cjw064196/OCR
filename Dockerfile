FROM ubuntu:16.04
RUN sed -i 's/archive.ubuntu.com/mirrors.ustc.edu.cn/g' /etc/apt/sources.list
RUN apt-get update && apt-get install -y \
	python-pip \
	autoconf \
	autoconf-archive \
	automake \
	build-essential \
	checkinstall \
	cmake \
	g++ \
	git \
	libcairo2-dev \
	libcairo2-dev \
	libicu-dev \
	libicu-dev \
	libjpeg8-dev \
	libjpeg8-dev \
	libpango1.0-dev \
	libpango1.0-dev \
	libpng12-dev \
	libpng12-dev \
	libtiff5-dev \
	libtiff5-dev \
	libtool \
	pkg-config \
	wget \
	xzgv \
	zlib1g-dev \
        python-tk

COPY . /home/apps

RUN pip install -r /home/apps/requirement.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
WORKDIR /home/apps
ENTRYPOINT python http_server.py

