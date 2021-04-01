# Camera Remote

Combining this program with a Raspberry Pi HQ camera, a Raspberry Pi Zero WH, and an Adafruit 16-LED NeoPixel ring will result in a camera that can be controlled via a web page.

---

The following attributes can be adjusted from the web interface:

1) Capture
     * Still Photo
     * Video*
1) Shutter Speed
1) ISO
1) Exposure Compensation
1) Bracketing
1) Scene Lighting - Currently limited to a 16-LED NeoPixel.
     * Red
     * Green
     * Blue
     * White 
   

:information_source:  The primary purpose of this application is intended still photography / photogammetry.  Video preview is suspended during capture due to apparent hardware limitations.   This system can be used to capture video, but currently it is not user-friendly.  

---
## Getting Started

- Use [raspi-config](https://www.raspberrypi.org/documentation/configuration/raspi-config.md) to:
  - Set the Memory Split value to a value of at least 256MB
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

:information_source: *This application was developed using a Raspberry Pi HQ (2020) camera and Raspberry Pi Zero WH and Raspberry Pi 4B boards.   Issues may arise if you are using either third party or older hardware.*
