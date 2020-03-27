FROM ubuntu:18.04

MAINTAINER Bernhard Buhl <buhl@buhl-consulting.com.cy>

RUN echo "Europe/Rome" > /etc/timezone

RUN apt-get update -q && \
	export DEBIAN_FRONTEND=noninteractive && \
    apt-get install -y --no-install-recommends tzdata

RUN dpkg-reconfigure -f noninteractive tzdata

# Install packages
RUN apt-get update -q && \
	export DEBIAN_FRONTEND=noninteractive && \
    dpkg --add-architecture i386 && \
    apt-get install -y --no-install-recommends software-properties-common && \
    add-apt-repository universe && \
    apt-get update -q && \
    apt-get remove -y python3.6 && \
    apt-get install -y --no-install-recommends wget curl rsync netcat mg vim bzip2 zip unzip && \
    apt-get install -y --no-install-recommends libx11-6 libxcb1 libxau6 jq python3-setuptools python3-tk && \
    apt-get install -y --no-install-recommends lxde tightvncserver xvfb dbus-x11 x11-utils && \
    apt-get install -y --no-install-recommends xfonts-base xfonts-75dpi xfonts-100dpi && \
    apt-get install -y --no-install-recommends python-pip python3.7-dev python-qt4 python3-pip tk-dev && \
    apt-get install -y --no-install-recommends libssl-dev git jq firefox unzip && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install && \
    rm google-chrome-stable_current_amd64.deb && \
    apt-get -qqy install nodejs && \
    apt-get install -y npm	

# Install Baangt
RUN git clone -b master --single-branch https://gogs.earthsquad.global/athos/baangt --branch master && \
    pip3 install -r baangt/requirements.txt 
    
#=============================================
# Install Android SDK's and Platform tools
#=============================================

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get -y --no-install-recommends install \
    libc6-i386 \
    lib32stdc++6 \
    lib32gcc1 \
    lib32ncurses5 \
    lib32z1 \
    wget \
    curl \
    unzip \
    ca-certificates \
    tzdata \
    libqt5webkit5 \
    libgconf-2-4 \
    openjdk-8-jdk \
    xvfb \
    gnupg \
  && wget --progress=dot:giga -O /opt/adt.tgz \
    https://dl.google.com/android/android-sdk_r24.3.4-linux.tgz \
  && tar xzf /opt/adt.tgz -C /opt \
  && rm /opt/adt.tgz \
  && echo y | /opt/android-sdk-linux/tools/android update sdk --all --filter platform-tools,build-tools-23.0.1 --no-ui --force \
  && apt-get -qqy clean \
  && rm -rf /var/cache/apt/*

#================================
# Set up PATH for Android Tools
#================================

ENV PATH $PATH:/opt/android-sdk-linux/platform-tools:/opt/android-sdk-linux/tools:/usr/lib/jvm/java-8-openjdk-amd64/jre
ENV ANDROID_HOME /opt/android-sdk-linux

#==========================
# Install Appium Dependencies
#==========================
RUN curl -sL https://deb.nodesource.com/setup_0.12 | bash - \
  && apt-get -qqy install \
    python \
    make \
    build-essential \
    g++

#=====================
# Install Appium
#=====================
ENV APPIUM_VERSION 1.4.16

RUN mkdir /opt/appium \
  && cd /opt/appium \
  && npm install appium@$APPIUM_VERSION \
  && ln -s /opt/appium/node_modules/.bin/appium /usr/bin/appium

EXPOSE 4723

WORKDIR /root/

# VNC-Server 
RUN mkdir -p /root/.vnc
COPY xstartup /root/.vnc/
RUN chmod a+x /root/.vnc/xstartup
RUN touch /root/.vnc/passwd && \
    /bin/bash -c "echo -e 'password\npassword\nn' | vncpasswd" > /root/.vnc/passwd && \ 
    chmod 400 /root/.vnc/passwd && \
    chmod go-rwx /root/.vnc && \
    touch /root/.Xauthority

COPY start-vncserver.sh /root/
COPY baangt.sh /root/
COPY getdrivers.sh /root/
RUN chmod a+x /root/start-vncserver.sh && \
    chmod a+x /root/baangt.sh && \
    chmod a+x /root/getdrivers.sh && \
    /root/getdrivers.sh && \
    echo "mycontainer" > /etc/hostname && \
    echo "127.0.0.1	localhost" > /etc/hosts && \
    echo "127.0.0.1	mycontainer" >> /etc/hosts

EXPOSE 5901
ENV USER root
CMD [ "/root/start-vncserver.sh" ]

#==========================
# Run appium as default
#==========================
CMD /usr/bin/appium

