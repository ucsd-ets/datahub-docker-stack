# Prepare the chrome repo
sudo wget -q -O /tmp/linux_signing_key.pub https://dl.google.com/linux/linux_signing_key.pub

# Import the key
sudo rpm --import /tmp/linux_signing_key.pub

# Configure it
echo "[google-chrome]
name=google-chrome - \$basearch
baseurl=http://dl.google.com/linux/chrome/rpm/stable/\$basearch
enabled=1
gpgcheck=1
gpgkey=https://dl.google.com/linux/linux_signing_key.pub" | sudo tee /etc/yum.repos.d/google-chrome.repo

# Update pkg list
sudo dnf makecache

# Install the latest Google Chrome
sudo dnf -y install google-chrome-stable unzip
chrome_version=$(grep -iEo "[0-9.]{10,20}" <(google-chrome --version))
echo "The stable Chrome version is: ${chrome_version}"

# ISSUE: Chrome driver may not have the same latest version for download
# Workaround: fetch the LATEST_RELEASE version available for download

# Download the latest Chrome Driver
driver_version=$(curl -s -L https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_STABLE)
echo "Latest Chrome driver version is: ${driver_version}"
wget https://storage.googleapis.com/chrome-for-testing-public/${driver_version}/linux64/chromedriver-linux64.zip

# Install Chrome Driver
unzip chromedriver-linux64.zip
sudo mv chromedriver /usr/local/bin/chromedriver
sudo chown root:root /usr/local/bin/chromedriver
sudo chmod +x /usr/local/bin/chromedriver