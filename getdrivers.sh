#!/bin/bash

INSTALL_DIR="/usr/local/bin"

json=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest)
url=$(echo "$json" | jq -r '.assets[].browser_download_url | select(contains("linux64"))')
curl -s -L "$url" | tar -xz
chmod +x geckodriver
mv geckodriver "$INSTALL_DIR"
echo "installed geckodriver binary in $INSTALL_DIR"

# Chromedriver 
a=$(uname -m) &&
rm -r /tmp/chromedriver/
mkdir /tmp/chromedriver/ &&
wget -O /tmp/chromedriver/LATEST_RELEASE http://chromedriver.storage.googleapis.com/LATEST_RELEASE &&
if [ $a == i686 ]; then b=32; elif [ $a == x86_64 ]; then b=64; fi &&
latest=$(cat /tmp/chromedriver/LATEST_RELEASE) &&
wget -O /tmp/chromedriver/chromedriver.zip 'http://chromedriver.storage.googleapis.com/'$latest'/chromedriver_linux'$b'.zip' &&
unzip /tmp/chromedriver/chromedriver.zip chromedriver -d /usr/local/bin/ &&
echo 'success?'

# Copy Chromedriver and Geckodriver to baangt
cp /usr/local/bin/geckodriver /baangt/browserDrivers/
cp /usr/local/bin/chromedriver /baangt/browserDrivers/

