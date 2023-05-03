#!/bin/bash

# File google-chrome.list allows `apt update` to fetch the latest stable of Chrome
sudo bash -c "echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' >> /etc/apt/sources.list.d/google-chrome.list"
sudo apt -y update
# Install latest Chrome
sudo apt -y install google-chrome-stable 
chrome_version=$(grep -iEo "[0-9.]{10,20}" <(google-chrome --version))
echo "The stable Chrome version is: ${chrome_version}"

# ISSUE: Chrome driver may not have the same latest version for download
# Workaround: fetch the LATEST_RELEASE version available for download
driver_version=$(curl -s -L https://chromedriver.storage.googleapis.com/LATEST_RELEASE)
echo "Latest Chrome driver version is: ${driver_version}"
wget https://chromedriver.storage.googleapis.com/${driver_version}/chromedriver_linux64.zip

# install Chrome Driver
unzip chromedriver_linux64.zip 
sudo mv chromedriver /usr/bin/chromedriver 
sudo chown root:root /usr/bin/chromedriver 
sudo chmod +x /usr/bin/chromedriver
