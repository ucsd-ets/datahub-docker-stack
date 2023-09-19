#!/bin/bash

# File google-chrome.list allows `apt update` to fetch the latest stable of Chrome
# OLD: sudo bash -c "echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.90-1_amd64.deb' >> /etc/apt/sources.list.d/google-chrome.list"

# Prepare chrome repo
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -

echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

sudo apt -y update

# Install latest Chrome
sudo apt -y install google-chrome-stable unzip
chrome_version=$(grep -iEo "[0-9.]{10,20}" <(google-chrome --version))
echo "The stable Chrome version is: ${chrome_version}"

# ISSUE: Chrome driver may not have the same latest version for download
# Workaround: fetch the LATEST_RELEASE version available for download
# OLD: driver_version=$(curl -s -L https://chromedriver.storage.googleapis.com/LATEST_RELEASE_114)

# Download latest chrome driver, instead of above methods
driver_version=$(curl -s -L https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE)
echo "Latest Chrome driver version is: ${driver_version}"
# OLD: wget https://chromedriver.storage.googleapis.com/${driver_version}/chromedriver_linux64.zip
wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/${driver_version}/linux64/chromedriver-linux64.zip

# install Chrome Driver
unzip chromedriver-linux64.zip 
sudo mv chromedriver-linux64/chromedriver /usr/bin/chromedriver 
sudo chown root:root /usr/bin/chromedriver 
sudo chmod +x /usr/bin/chromedriver
