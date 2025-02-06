# note: build this from the root of the repo

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN echo "deb-src http://archive.ubuntu.com/ubuntu/ jammy-security main restricted universe multiverse" >> /etc/apt/sources.list


RUN apt-get update && \
  apt-get build-dep -y qemu && \
  apt-get install -y \
  build-essential \
  ca-certificates \
  cmake \
  ethtool \
  g++ \
  gcc-arm-none-eabi \
  git \
  gdb-multiarch \
  libpixman-1-dev \
  python3-pip \
  python3-venv \
  python-tk \
  tcpdump \
  vim \
  wget \
  ninja-build && \
  apt-get clean && \
  apt-get autoclean -y && \
  rm -rf /var/lib/apt/lists/*


# only copy the deps now to build qemu (which takes a while)
RUN mkdir /root/halucinator
WORKDIR /root/halucinator
COPY deps /root/halucinator/deps
RUN mkdir -p deps/build-qemu/arm-softmmu
RUN mkdir -p deps/build-qemu/aarch64-softmmu
RUN mkdir -p deps/build-qemu/ppc-softmmu

WORKDIR /root/halucinator/deps/build-qemu/arm-softmmu
RUN /root/halucinator/deps/avatar-qemu/configure --with-git-submodules=ignore --target-list=arm-softmmu
RUN make all -j`nproc`

# install depedencies first so it can be cached
WORKDIR /root/halucinator
COPY src/requirements.txt /root/halucinator_requirements.txt
RUN pip install -r /root/halucinator_requirements.txt
RUN pip install -e deps/avatar2/

# install helics
RUN pip install 'helics[cli]'

# install halucinator
COPY src /root/halucinator/src
RUN pip install -e src

WORKDIR  /root/halucinator
RUN ln -s -T /usr/bin/gdb-multiarch /usr/bin/arm-none-eabi-gdb

COPY helics_thermostat /root/halucinator/helics_thermostat
WORKDIR /root/halucinator/helics_thermostat
CMD ./run.sh
