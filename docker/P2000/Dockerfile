FROM debian:bullseye

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ="Europe/Amsterdam"

RUN apt update && apt upgrade -y && \
    apt-get install -y python3-pip python3-paho-mqtt python3-geopy python3-cryptography rustc build-essential cmake unzip pkg-config libusb-1.0-0-dev git qt5-qmake libpulse-dev libx11-dev udev libssl-dev libffi-dev python3-dev cargo

RUN git clone git://git.osmocom.org/rtl-sdr.git && \
    cd rtl-sdr && \
    mkdir build && \
    cd build && \
    cmake ../ -DINSTALL_UDEV_RULES=ON -DDETACH_KERNEL_DRIVER=ON && \
    make && \
    make install && \
    ldconfig && \
    cp ../rtl-sdr.rules /etc/udev/rules.d/

RUN git clone https://github.com/EliasOenal/multimon-ng.git && \
    cd multimon-ng && \
    mkdir build && \
    cd build && \
    qmake -qt=qt5 ../multimon-ng.pro && \
    make && \
    make install && \
    cd / && \
    rm -rf /tmp/multimon-ng

RUN pip3 install --upgrade pip
RUN pip3 install opencage

CMD python3 /p2000/p2000.py