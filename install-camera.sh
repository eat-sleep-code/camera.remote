# This script will install the camera, dng support, and any required prerequisites.
cd ~
echo -e ''
echo -e '\033[32mCamera Remote [Installation Script] \033[0m'
echo -e '\033[32m-------------------------------------------------------------------------- \033[0m'
echo -e ''
echo -e '\033[93mUpdating package repositories... \033[0m'
sudo apt update

echo ''
echo -e '\033[93mInstalling prerequisites... \033[0m'
sudo apt install -y git python3 python3-pip python3-picamera libatlas-base-dev
sudo pip3 install RPi.GPIO adafruit-circuitpython-neopixel PiDNG --force


echo ''
echo -e '\033[93mInstalling Camera Remote... \033[0m'
cd ~
sudo rm -Rf ~/camera.remote
sudo git clone https://github.com/eat-sleep-code/camera.remote
sudo mkdir -p ~/camera.remote/logs
sudo chown -R $USER:$USER camera.remote
cd camera.remote
sudo chmod +x camera.py
sudo chmod +x server.py

echo ''
echo -e '\033[93mDownloading color profiles... \033[0m'
cd ~
sudo rm -Rf ~/camera.remote/profiles
mkdir ~/camera.remote/profiles
sudo chown -R $USER:$USER ~/camera.remote/profiles
wget -q https://github.com/davidplowman/Colour_Profiles/raw/master/imx477/PyDNG_profile.dcp -O ~/camera.remote/profiles/basic.dcp
wget -q https://github.com/davidplowman/Colour_Profiles/raw/master/imx477/Raspberry%20Pi%20High%20Quality%20Camera%20Lumariver%202860k-5960k%20Neutral%20Look.dcp -O ~/camera.remote/profiles/neutral.dcp
wget -q https://github.com/davidplowman/Colour_Profiles/raw/master/imx477/Raspberry%20Pi%20High%20Quality%20Camera%20Lumariver%202860k-5960k%20Skin%2BSky%20Look.dcp -O ~/camera.remote/profiles/skin-and-sky.dcp

echo ''
echo -e '\033[93mSetting up alias... \033[0m'
cd ~
sudo touch ~/.bash_aliases
sudo sed -i '/\b\(function camera.remote\)\b/d' ~/.bash_aliases
sudo sed -i '$ a function camera.remote { sudo python3 ~/camera.remote/camera.py "$@"; }' ~/.bash_aliases
echo -e 'Please ensure that your camera and I2C interfaces are enabled in raspi-config before proceeding.'

echo ''
echo -e '\033[32m-------------------------------------------------------------------------- \033[0m'
echo -e '\033[32mInstallation completed. \033[0m'
echo ''
sudo rm install-camera.sh
bash
