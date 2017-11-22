# This dockerfile sets up the container for the sandbox app
FROM debian:stretch
RUN apt-get update \
    && apt-get install -y \
    build-essential \
    python-dev \
    python-pip \
    python-cffi \
    python-cryptography \
    curl \
    wget \
    gfortran \
    openssl \
    libffi-dev \
    libxml2-dev \
    libcairo2-dev \
    libblas-dev \
    libreadline-dev \
    libmariadb-dev \
    libmariadbclient-dev \
    libfreetype6-dev \
    libpng-dev \
    libpcre3-dev \
    liblzma-dev \
    libbz2-dev \
    zlib1g-dev \
    libcurl4-openssl-dev \
    supervisor \
    git \
  && pip install --upgrade pip

SHELL ["/bin/bash", "-c"]

# install some google cloud utilities:
RUN pip install gsutil
RUN curl -sSL https://sdk.cloud.google.com > /tmp/gcl \
    && bash /tmp/gcl --install-dir=/root/gcloud --disable-prompts
ARG gcloud_bin=/root/gcloud/google-cloud-sdk/bin
ENV PATH "$PATH:"${gcloud_bin}
ENV GCLOUD=${gcloud_bin}/gcloud

# setup app directory which contains everything:
ARG appdir=/tru_t_sandbox
RUN mkdir ${appdir}

# pull the code:
ENV PATH="${gcloud}:${PATH}"
RUN git clone https://github.com/blawney/mycalc.git "${appdir}"

# install virtualenv, create a virtual environment for django, and install the necessary libraries:
ARG django_venv=/django_venv
RUN pip install virtualenv \
  && virtualenv ${django_venv} \
  && source ${django_venv}/bin/activate \
  && pip install --no-cache-dir -r "${appdir}"/requirements.txt
ENV DJANGO_VENV=${django_venv}

# a directory to hold startup scripts, etc.
RUN mkdir /startup
ADD docker_utils /startup

WORKDIR ${appdir}/webapp

# run the startup script which injects some parameters and starts the app server:
ENTRYPOINT ["/startup/startup.sh"]
