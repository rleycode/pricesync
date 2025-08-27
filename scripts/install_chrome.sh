#!/bin/bash


echo "🔧 Установка Chrome и ChromeDriver..."

sudo apt-get update
sudo apt-get install -y wget curl unzip

wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

sudo apt-get update

sudo apt-get install -y google-chrome-stable

sudo apt-get install -y chromium-chromedriver

if ! command -v chromedriver &> /dev/null; then
    echo "Установка ChromeDriver вручную..."
    
    CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1)
    
    CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
    
    wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
    
    unzip /tmp/chromedriver.zip -d /tmp/
    sudo mv /tmp/chromedriver /usr/local/bin/
    sudo chmod +x /usr/local/bin/chromedriver
    
    rm /tmp/chromedriver.zip
fi

echo ""
echo "Проверка установки:"
google-chrome --version
chromedriver --version

echo ""
echo "Установка завершена!"
