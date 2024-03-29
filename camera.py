from functions import Echo, Console
from libcamera import ColorSpace, controls, Transform
from picamera2 import Picamera2
from picamera2.controls import Controls
from picamera2.encoders import H264Encoder, Quality
from controls import Light
from PIL import Image
import argparse
import datetime
import fractions
import globals
import os
import piexif
import server
import subprocess
import sys
import threading
import time

version = '2024.02.10'


console = Console()
echo = Echo()
globals.initialize()
camera = Picamera2()
camera.set_logging(Picamera2.ERROR)
controls = Controls(camera)
previewConfiguration = camera.create_video_configuration(main={"size": (960, 540)}, colour_space = ColorSpace.Sycc())
stillConfiguration = camera.create_still_configuration(main={"size": camera.sensor_resolution}, colour_space = ColorSpace.Sycc())
videoConfiguration = camera.create_video_configuration(main={"size": (1920, 1080)}, colour_space = ColorSpace.Rec709())


try:
	camera.set_controls({"AfMode": controls.AfModeEnum.Continuous})
except Exception as ex:
	console.info('Camera does not support autofocus.')
	time.sleep(3)
	pass

# === Argument Handling ========================================================

parser = argparse.ArgumentParser()
parser.add_argument('--rotate', dest='rotate', help='Rotate the camera in 90* increments', type=int)
parser.add_argument('--exifFStop', dest='exifFStop', help='Set the numeric F-Stop value in the image EXIF data', type=float)
parser.add_argument('--exifFocalLength', dest='exifFocalLength', help='Set the numeric Focal Length value (mm) in the image EXIF data', type=float)
parser.add_argument('--exifFocalLengthEquivalent', dest='exifFocalLengthEquivalent', help='Set the numeric 35mm Focal Length value (mm) in the image EXIF data', type=float)
args = parser.parse_args()


running = False

previewVisible = False
previewWidth = 800
previewHeight = 460

rotate = args.rotate or 0
try:
	rotate = int(rotate)
except:
	rotate = 0

shutter = 'auto'
shutterLong = 30000
shutterLongThreshold = 1000
shutterShort = 0
defaultFramerate = 30

iso = 'auto'
isoMin = 100
isoMax = 1600

exposure = 'auto'

ev = 0
evMin = -25
evMax = 25

bracket = 0
bracketLow = 0
bracketHigh = 0 

awb = 'auto'

outputFolder = 'dcim/'

timer = 0

raw = False
try:
	from pidng.core import RPICAM2DNG
	dng = RPICAM2DNG()
	raw = False # Going to disable this by default as the Pi Zero W struggles with it 
except:
	console.info( ' WARNING: DNG file format not currently supported on this device. ')


# === Data Objects ============================================================

class EXIFData:
	def __init__(self, Orientation = 1, FStop = None, FocalLength = None, FocalLengthEquivalent = None):

		self.Orientation = Orientation
		self.FStop = FStop
		self.FocalLength = FocalLength
		self.FocalLengthEquivalent = FocalLengthEquivalent
		

EXIFDataOverride = EXIFData()
EXIFDataOverride.FStop = args.exifFStop
EXIFDataOverride.FocalLength = args.exifFocalLength
EXIFDataOverride.FocalLengthEquivalent = args.exifFocalLengthEquivalent



# === Functions ================================================================

def setShutter(input, wait = 0):
	global controls
	global shutter
	global shutterLong
	global shutterLongThreshold
	global shutterShort
	global defaultFramerate
	
	if str(input).lower() == 'auto' or str(input) == '0':
		shutter = 0
	else:
		shutter = int(float(input))
		if shutter < shutterShort:
			shutter = shutterShort
		elif shutter > shutterLong:
			shutter = shutterLong 
	
	try:
		if camera.framerate == defaultFramerate and shutter > shutterLongThreshold:
			camera.framerate=fractions.Fraction(5, 1000)
		elif camera.framerate != defaultFramerate and shutter <= shutterLongThreshold:
			camera.framerate = defaultFramerate
	except Exception as ex:
		# console.info( ' WARNING: Could not set framerate!')
		pass
	
	try:
		if shutter == 0:
			controls.ExposureTime = 0
			# print(str(controls.ExposureTime) + '|' + str(controls.FrameRate) + '|' + str(shutter))	
			print(' Shutter Speed: auto')
			globals.statusDictionary.update({'message': 'Shutter Speed: auto'})
		else:
			controls.ExposureTime = shutter * 1000
			# print(str(controls.ExposureTime) + '|' + str(controls.FrameRate) + '|' + str(shutter))		
			floatingShutter = float(shutter/1000)
			roundedShutter = '{:.3f}'.format(floatingShutter)
			if shutter > shutterLongThreshold:
				print(' Shutter Speed: ' + str(roundedShutter)  + 's [Long Exposure Mode]')
				globals.statusDictionary.update({'message': ' Shutter Speed: ' + str(roundedShutter)  + 's [Long Exposure Mode]'})
			else:
				print(' Shutter Speed: ' + str(roundedShutter) + 's')
				globals.statusDictionary.update({'message': ' Shutter Speed: ' + str(roundedShutter) + 's'})
		time.sleep(wait)
		return
	except Exception as ex:
		console.info('WARNING: Invalid Shutter Speed! ' + str(shutter) + str(ex))

# ------------------------------------------------------------------------------				

def setISO(input, wait = 0):
	global controls
	global iso
	global isoMin
	global isoMax

	if str(input).lower() == 'auto' or str(input) == '0':
		controls.AeEnable = 1
		iso = 0
	else: 
		controls.AeEnable = 0
		iso = int(input)
		if iso < isoMin:	
			iso = isoMin
		elif iso > isoMax:
			iso = isoMax	
	try:	
		analogGain = iso/100
		controls.AnalogueGain = analogGain
		# print(str(camera.iso) + '|' + str(iso))
		if iso == 0:
			print(' ISO: auto')
		else:	
			print(' ISO: ' + str(iso))
			globals.statusDictionary.update({'message': ' ISO: ' + str(iso)})
		time.sleep(wait)
		return
	except Exception as ex:
		console.info('WARNING: Invalid ISO Setting! ' + str(iso) + str(ex))

# ------------------------------------------------------------------------------

def setExposure(input, wait = 0):
	global exposure

	exposure = input
	try:	
		controls.AeExposureMode = exposure
		print(' Exposure Mode: ' + exposure)
		globals.statusDictionary.update({'message': ' Exposure Mode: ' + exposure})
		time.sleep(wait)
		return
	except Exception as ex:
		console.info('WARNING: Invalid Exposure Mode! ' + str(ex))
				
# ------------------------------------------------------------------------------

def setEV(input, wait = 0, displayMessage = True):
	global controls
	global ev 
	global bracket

	ev = input
	ev = int(ev)
	evPrefix = '+/-'
	if ev > 0:
		evPrefix = '+'
	elif ev < 0:
		evPrefix = ''
	try:
		controls.ExposureValue = ev
		# print(str(camera.exposure_compensation) + '|' + str(ev))
		if displayMessage == True:
			print(' Exposure Compensation: ' + evPrefix + str(ev))
			globals.statusDictionary.update({'message': ' Exposure Compensation: ' + evPrefix + str(ev)})
		time.sleep(wait)
		return
	except Exception as ex: 
		console.info('WARNING: Invalid Exposure Compensation Setting! ' + str(ex))	
		
# ------------------------------------------------------------------------------				

def setBracket(input, wait = 0, displayMessage = True):
	global controls
	global bracket
	global bracketLow
	global bracketHigh
	global evMax
	global evMin

	bracket = int(input)
	try:
		bracketLow = controls.ExposureValue - bracket
		if bracketLow < evMin:
			bracketLow = evMin
		bracketHigh = controls.ExposureValue + bracket
		if bracketHigh > evMax:
			bracketHigh = evMax
		if displayMessage == True:
			print(' Exposure Bracketing: ' + str(bracket))
			globals.statusDictionary.update({'message': ' Exposure Bracketing: ' + str(bracket)})
		time.sleep(wait)
		return
	except Exception as ex:
		console.info('WARNING: Invalid Exposure Bracketing Value! ' + str(ex))

# ------------------------------------------------------------------------------

def setAWB(input, wait = 0):
	global controls
	global awb

	awb = input
	try:	
		controls.AwbMode = awb
		print(' White Balance Mode: ' + awb)
		globals.statusDictionary.update({'message': ' White Balance Mode: ' + awb})
		time.sleep(wait)
		return
	except Exception as ex:
		console.info('WARNING: Invalid Auto White Balance Mode! ' + str(ex))

# ------------------------------------------------------------------------------

def getFileName(timestamped = True, isVideo = False):
	now = datetime.datetime.now()
	datestamp = now.strftime('%Y%m%d')
	timestamp = now.strftime('%H%M%S')		
			
	if isVideo==True:
		extension = '.h264'
		return datestamp + '-' + timestamp + extension
	else:
		extension = '.jpg'
		if timestamped == True:
			return datestamp + '-' + timestamp + '-' + str(imageCount).zfill(2) + extension
		else:
			return datestamp + '-' + str(imageCount).zfill(8) + extension

# ------------------------------------------------------------------------------

def getfilePath(timestamped = True, isVideo = False):
	try:
		os.makedirs(outputFolder, exist_ok = True)
	except OSError:
		console.error(' ERROR: Creation of the output folder ' + outputFolder + ' failed!')
		echo.on()
		quit()
	else:
		return outputFolder + getFileName(timestamped, isVideo)

# ------------------------------------------------------------------------------

def postProcessImage(filePath, angle):

	global EXIFDataOverride

	try:
		image = Image.open(filePath)
		FileEXIFData = piexif.load(filePath)

		if angle > 0:
			newOrientation = 1
			if angle == 90:
				newOrientation = 6
				image = image.rotate(-90, expand=True)
			elif angle == 180:
				newOrientation = 3
				image = image.rotate(180, expand=True)
			elif angle == 270:
				newOrientation = 8
				image = image.rotate(90, expand=True)
			EXIFDataOverride.Orientation = newOrientation
				
			FileEXIFData['Orientation'] = EXIFDataOverride.Orientation

		try:
			if EXIFDataOverride.FStop is not None:
				FileEXIFData['Exif'][piexif.ExifIFD.FNumber] = (int(EXIFDataOverride.FStop * 100), 100)
				
			if EXIFDataOverride.FocalLength is not None:
				FileEXIFData['Exif'][piexif.ExifIFD.FocalLength] = (int(EXIFDataOverride.FocalLength * 100), 100)
				
			if EXIFDataOverride.FocalLengthEquivalent is not None:
				FileEXIFData['Exif'][piexif.ExifIFD.FocalLengthIn35mmFilm] = int(EXIFDataOverride.FocalLengthEquivalent)
		except Exception as ex:
			console.warn('Could not rotate apply additional EXIF data to image.   Please check supplied data. ' + str(ex))
			pass

		EXIFBytes = piexif.dump(FileEXIFData)
		image.save(filePath, exif=EXIFBytes)
	except Exception as ex:
		console.warn('Could not rotate ' + filePath + ' ' + str(angle) + ' degrees. ' + str(ex))
		pass

# ------------------------------------------------------------------------------

def captureImage(filePath, raw = True):
	global rotate

	request = camera.switch_mode_and_capture_request(stillConfiguration)
	request.save('main', filePath)
	request.release()

	postProcessImage(filePath, rotate)
				
	if raw == True:
		conversionThread = threading.Thread(target=convertBayerDataToDNG, args=(filePath,))
		conversionThread.daemon = True
		conversionThread.start()

# ------------------------------------------------------------------------------		

def convertBayerDataToDNG(filePath):
	try:
		dng.convert(filePath)
	except:
		pass

# ------------------------------------------------------------------------------
def startPreviewStream():
	global running
	global previewConfiguration
	running = True
	server.startStream(camera, previewConfiguration, running)
	
# -------------------------------------------------------------------------------
def darkMode():
	Light.off()



# === Image Capture ============================================================

previewStreamThread = threading.Thread(target=startPreviewStream)
previewStreamThread.daemon = True
previewStreamThread.start()


try:
	echo.clear()
	os.chdir('/home/pi') 
	
	console.info('Camera Remote ' + version )
	console.print('----------------------------------------------------------------------', '\n ', '\n ')
		
	try:	
		camera.start(show_preview=False)
		time.sleep(1.0)
	except:
		try:
			camera.stop()
			time.sleep(1.0)
			camera.start(show_preview=False)
			time.sleep(1.0)
		except: 
			console.warn('Could not start camera.   Is it already in use? ', '\n ')
			pass
		pass


	setShutter(shutter, 0)		
	setISO(iso, 0)
	setExposure(exposure, 0)
	setEV(ev, 0)
	setBracket(bracket, 0)
	setAWB(awb, 0)

	imageCount = 1
	isRecording = False
	mode = 'persistent'

	
	while True:
		try:
			# Exit / Spawn
			if globals.buttonDictionary['exit'] == True or globals.buttonDictionary['trackball'] == True:
				running = False
				darkMode()
				echo.on()
				camera.close()
				time.sleep(1.0)
				
				if globals.buttonDictionary['trackball'] == True:
					try:
						subprocess.Popen(['sudo', 'python3', '/home/pi/camera.zero/camera.py'], stdout=outputLog, stderr=errorLog)	
					except Exception as ex:
						print(' Could not switch to trackball control ')
				sys.exit(0)

				
			# Capture
			elif globals.buttonDictionary['capture'] == True:
				
				if mode == 'persistent':
					# Normal photo
					filePath = getfilePath(True)
					console.info('Capturing image: ' + filePath + '\n')
					captureImage(filePath, raw)
					
					imageCount += 1
			
					if (bracket != 0):
						baseEV = ev
						# Take underexposed photo
						setEV(baseEV + bracketLow, 0, False)
						filePath = getfilePath(True)
						console.info('Capturing image: ' + filePath + '  [' + str(bracketLow) + ']\n')
						captureImage(filePath, raw)
						imageCount += 1

						# Take overexposed photo
						setEV(baseEV + bracketHigh, 0, False)
						filePath = getfilePath(True)
						console.info('Capturing image: ' + filePath + '  [' + str(bracketHigh) + ']\n')
						captureImage(filePath, raw)
						imageCount += 1						
						
						# Reset EV to base photo's value
						setEV(baseEV, 0, False)
						
				elif mode == 'timelapse':
					# Timelapse photo series
					if timer < 0:
						timer = 1
					while True:
						filePath = getfilePath(False)
						console.info('Capturing timelapse image: ' + filePath + '\n')
						captureImage(filePath, raw)
						imageCount += 1
						time.sleep(timer) 	
						
				else:
					# Single photo and then exit
					filePath = getfilePath(True)
					console.info('Capturing single image: ' + filePath + '\n')
					captureImage(filePath, raw)
					echo.on()
					break

				globals.buttonDictionary.update({'capture': False})

			elif globals.buttonDictionary['captureVideo'] == True:

				# Video
				if isRecording == False:
					server.pauseStream(camera)
					isRecording = True
					globals.statusDictionary.update({'action': 'recording'})
					filePath = getfilePath(True, True)
					camera.resolution = (1920, 1080)
					console.info('Capturing video: ' + filePath + '\n')
					globals.statusDictionary.update({'message': ' Recording: Started '})
					globals.buttonDictionary.update({'captureVideo': False})
					camera.configure(videoConfiguration)
					encoder = H264Encoder()
					camera.start_recording(encoder, filePath, quality=Quality.VERY_HIGH)

				else:
					isRecording = False
					globals.statusDictionary.update({'action': ''})
					camera.stop_recording()
					console.info('Capture complete \n')
					globals.statusDictionary.update({'message': ' Recording: Stopped '})
					globals.buttonDictionary.update({'captureVideo': False})
					server.resumeStream(camera, previewConfiguration, running)
					
				time.sleep(1)

			# Shutter Speed	
			elif globals.buttonDictionary['shutterUp'] == True:
				if shutter == 0:
					shutter = shutterShort
				elif shutter > shutterShort and shutter <= shutterLong:					
					shutter = int(shutter / 1.5)
				setShutter(shutter, 0.25)
				globals.buttonDictionary.update({'shutterUp': False})
			elif globals.buttonDictionary['shutterDown'] == True:
				if shutter == 0:						
					shutter = shutterLong
				elif shutter < shutterLong and shutter >= shutterShort:					
					shutter = int(shutter * 1.5)
				elif shutter == shutterShort:
					shutter = 0
				setShutter(shutter, 0.25)
				globals.buttonDictionary.update({'shutterDown': False})

			# ISO
			elif globals.buttonDictionary['isoUp'] == True:
				if iso == 0:
					iso = isoMin
				elif iso >= isoMin and iso < isoMax:					
					iso = int(iso * 2)
				setISO(iso, 0.25)
				globals.buttonDictionary.update({'isoUp': False})
			elif globals.buttonDictionary['isoDown'] == True:
				if iso == 0:
					iso = isoMax
				elif iso <= isoMax and iso > isoMin:					
					iso = int(iso / 2)
				elif iso == isoMin:
					iso = 0
				setISO(iso, 0.25)
				globals.buttonDictionary.update({'isoDown': False})

			# Exposure Compensation
			elif globals.buttonDictionary['evUp'] == True:
				if ev >= evMin and ev < evMax:					
					ev = int(ev + 1)
					setEV(ev, 0.25)
					globals.buttonDictionary.update({'evUp': False})
			elif globals.buttonDictionary['evDown'] == True:
				if ev <= evMax and ev > evMin:					
					ev = int(ev - 1)
					setEV(ev, 0.25)
					globals.buttonDictionary.update({'evDown': False})
					
			# Exposure Bracketing
			elif globals.buttonDictionary['bracketUp'] == True:
				if bracket < evMax:
					bracket = int(bracket + 1)
					setBracket(bracket, 0.25)
					globals.buttonDictionary.update({'bracketUp': False})
			elif globals.buttonDictionary['bracketDown'] == True:
				if bracket > 0:					
					bracket = int(bracket - 1)
					setBracket(bracket, 0.25)
					globals.buttonDictionary.update({'bracketDown': False})

			
		except Exception as ex:
			console.error(str(ex))
			pass

	

except KeyboardInterrupt:
	darkMode()
	echo.on() 
	sys.exit(0)
