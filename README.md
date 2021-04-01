# Camera Remote

Combining this program with a Raspberry Pi HQ camera, a Raspberry Pi Zero WH, and an Adafruit 16-LED NeoPixel ring will result in a camera that can be controlled via a web page.

:information_source: &nbsp; *The primary intended use of this application is for still photography and photogammetry.  Preview is suspended during video capture due to apparent hardware limitations.   This system can be used to capture video, but it currently is not user-friendly.*

---
## Use With Other Camera Software

**Optionally**, this application may be used in conjunction with one of the following applications.  These applications are all designed to kill the camera.remote script at startup (and vice versa) to eliminate hardware-in-use errors.
   - [Camera](https://github.com/eat-sleep-code/camera)
   - [Camera.Zero](https://github.com/eat-sleep-code/camera.zero)
   - [Camera.Timelapse](https://github.com/eat-sleep-code/camera.timelapse)


---
## Getting Started

- Use [raspi-config](https://www.raspberrypi.org/documentation/configuration/raspi-config.md) to:
  - Set the Memory Split value to a value of at least 192MB
  - Enable the CSI camera interface
  - Set up your WiFi connection
- Connect the Raspberry Pi HQ Camera to your Raspberry Pi


## Installation

Installation of the program, any software prerequisites, as well as DNG support can be completed with the following two-line install script.

```
wget -q https://raw.githubusercontent.com/eat-sleep-code/camera.remote/main/install-camera.sh -O ~/install-camera.sh
sudo chmod +x ~/install-camera.sh && ~/install-camera.sh
```

---

## Usage
```
camera.remote
```

### Web Controls
The following attributes can be adjusted from the web interface:

1) Capture
     - Still Photo
     - Video*
1) Shutter Speed
1) ISO
1) Exposure Compensation
1) Bracketing
1) Scene Lighting - *currently limited to control of a 16-LED NeoPixel array*
     - All Lights (on/off)
     - Natural White (256 steps)
     - Red (256 steps)
     - Green (256 steps)
     - Blue (256 steps)

---
## Autostart at Desktop Login

To autostart the program as soon as the Raspberry Pi OS desktop starts, execute the following command:

```
sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
```

Add the following line to the end of the file and then save the file:

```
@lxterminal --geometry=1x1 -e sudo python3 /home/pi/camera.remote/camera.py
```

:information_source:  &nbsp; *Do not simultaneously autostart this program and one of the aforementioned software applications as they are designed to kill each other's processes.*

---

## Infrared Cameras
If you are using an infrared (IR) camera, you will need to modify the Auto White Balance (AWB) mode at boot time.

This can be achieved by executing `sudo nano /boot/config.txt` and adding the following lines.

```
# Camera Settings 
awb_auto_is_greyworld=1
```

Also note, that while IR cameras utilize "invisible" (outside the spectrum of the human eye) light, they can not magically see in the dark.   You will need to illuminate night scenes with one or more [IR emitting LEDs](https://www.adafruit.com/product/387) to take advantage of an Infrared Camera.

---

:information_source:  &nbsp; *This application was developed using a Raspberry Pi HQ (2020) camera and Raspberry Pi Zero WH and Raspberry Pi 4B boards.   Issues may arise if you are using either third party or older hardware.*
