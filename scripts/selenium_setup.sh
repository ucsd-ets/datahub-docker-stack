#!/bin/bash

# fetch signing key and install Chrome
sudo curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add 
sudo bash -c "echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' >> /etc/apt/sources.list.d/google-chrome.list" 
sudo apt -y update 
sudo apt -y install google-chrome-stable 

# instead of using command-line arg passed in from Github Secrets,
# we grab the Chrome version and download matching ChromeDriver
# `$ google-chrome --version` will return `Google Chrome 36.0.1985.125`
chrome_version=$(grep -iEo "[0-9.]{10,20}" <(google-chrome --version))
echo "The Chrome version is: ${chrome_version}"
wget https://chromedriver.storage.googleapis.com/${chrome_version}/chromedriver_linux64.zip
unzip chromedriver_linux64.zip 
sudo mv chromedriver /usr/bin/chromedriver 
sudo chown root:root /usr/bin/chromedriver 
sudo chmod +x /usr/bin/chromedriver
pip install selenium