from functions import Echo, Console
from controls import Light
from threading import Condition
from libcamera import ColorSpace
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput
from http import server
import globals
import io
import socketserver
import subprocess
import time


console = Console()
echo = Echo()


PAGE="""\
<!DOCTYPE html>
<html lang="en">
<head>
	<title>Camera Remote</title>
	<meta charset="utf-8">
	<meta name="apple-mobile-web-app-capable" content="yes">
	<meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0">
	<meta name="application-name" content="Camera Remote">
	<meta name="theme-color" content="#000000">
	
	<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" integrity="sha512-1ycn6IcaQQ40/MKBW2W4Rhis/DbILU74C1vSrLJxCq57o941Ym01SwNsOMqvEBFlcgUa6xLiPY/NS5R+E6ztJQ==" crossorigin="anonymous" />
	<style>
		body 
		{
			background: rgba(8, 8, 8, 1.0); 
			color: rgba(255, 255, 255, 1.0);
			font-family: 'Century Gothic', CenturyGothic, AppleGothic, sans-serif;
			margin: 0; 
			padding: 0;
		}

		.wrapper 
		{
			align-items: center; 
			box-sizing: border-box;
			display: flex; 
			flex-wrap: wrap;
			height: 100vh;
			justify-content: center;
			margin: auto;
			max-width: 960px;
			overflow-x: hidden;
			padding-bottom: 60px; 
			width: 100%; 
		}

		.wrapper > div 
		{
			width: 100%;
			display: flex;
			flex-wrap: wrap;
			justify-content: center;
		}

		.stream
		{
			border-radius: 4px;
			max-width: 960px;
			width: 100%; 
		}

		.status 
		{
			background: rgba(0, 0, 0, 0.5);
			border-radius: 4px;
			box-sizing: border-box;
			font-size: 12px;
			height: 24px;
			line-height: 12px;
			margin: -24px 0 0 0;
			max-width: 960px;
			padding: 8px;
			text-align: center;
			width: 100%;
			z-index: 1000;
		}

		.controls
		{
			align-items: center;
			display: flex;
			flex-wrap: wrap;
			justify-content: center;
		}

		.control-group
		{
			margin: 0 8px;
		}

		.control-group label,
		.controls > label 
		{
			align-items: center;
			background: rgba(255, 255, 255, 0.1);
			border-radius: 4px;
			font-size: 12px;
			display: block;
			justify-content: center;
			line-height: 12px;
			overflow: hidden;
			padding: 6px;
			text-align: center;
			text-overflow: ellipsis;
			white-space: nowrap;
			width: 132px;
		}

		.control-group > div
		{
			text-align: center;
		}

		.controls > label
		{
			width: 100%;
		}

		.control-button
		{
			background: rgba(0, 0, 0, 0);
			border: 0;
			color: rgba(255, 255, 255, 1.0);
			display: inline-block;
			font-size: 36px;
			height: 42px;
			margin: 12px;
			padding: 0;
			text-align: center;
			text-decoration: none;
			width: 42px;
			opacity: 0.8;
		}

		.control-button:focus
		{
			outline: none !important; 
		}

		.control-button:hover,
		.control-button:focus
		{
			opacity: 1.0;
		}

		.control-button.white
		{
			color: rgba(255, 255, 255, 1.0);
		}

		.control-button.white.dim
		{
			color: rgba(255, 255, 255, 0.4);
		}

		.control-button.red
		{
			color: rgba(255, 0, 0, 1.0);
		}

		.control-button.red.dim
		{
			color: rgba(255, 0, 0, 0.4);
		}

		.control-button.green
		{
			color: rgba(0, 255, 0, 1.0);
		}

		.control-button.green.dim
		{
			color: rgba(0, 255, 0, 0.4);
		}

		.control-button.blue
		{
			color: rgba(0, 0, 255, 1.0);
		}

		.control-button.blue.dim
		{
			color: rgba(0, 0, 255, 0.5);
		}

		.control-button.blink {
			animation: blink 1s linear infinite;
		}

		@keyframes blink 
		{
			50% 
			{
				color: rgba(255, 0, 0, 0);
			}
		}
	</style>
</head>
<body>
	<div class="wrapper">
		<div>
			<img src="stream.mjpg" class="stream" />
			<div class="status"></div>
		</div>
		<div class="controls">
			<div class="control-group">
				<label>Capture</label>
				<div>
					<button data-url="/control/capture/photo" class="control-button" title="Capture photo"><i class="fas fa-camera"></i></button>
					<button data-url="/control/capture/video" class="control-button red" title="Capture video"><i class="fas fa-video"></i></button>
				</div>
			</div>
			<div class="control-group">
				<label>Shutter Speed</label>
				<div>
					<button data-url="/control/shutter/up" class="control-button" title="Increase shutter speed (shorter)"><i class="fas fa-plus-circle"></i></button>
					<button data-url="/control/shutter/down" class="control-button" title="Decrease shutter speed (longer)"><i class="fas fa-minus-circle"></i></button>
				</div>
			</div>
			<div class="control-group">
				<label>ISO</label>
				<div>
					<button data-url="/control/iso/up" class="control-button" title="Increase ISO"><i class="fas fa-plus-circle"></i></button>
					<button data-url="/control/iso/down" class="control-button" title="Decrease ISO"><i class="fas fa-minus-circle"></i></button>
				</div>
			</div>
			<div class="control-group">
				<label>Exposure Compensation</label>
				<div>
					<button data-url="/control/ev/up" class="control-button" title="Increase exposure compensation"><i class="fas fa-plus-circle"></i></button>
					<button data-url="/control/ev/down" class="control-button" title="Decrease exposure compensation"><i class="fas fa-minus-circle"></i></button>
				</div>
			</div>
			<div class="control-group">
				<label>Bracketing</label>
				<div>
					<button data-url="/control/bracket/up" class="control-button" title="Increase exposure bracket stops"><i class="fas fa-plus-circle"></i></button>
					<button data-url="/control/bracket/down" class="control-button" title="Decrease exposure bracket stops"><i class="fas fa-minus-circle"></i></button>
				</div>
			</div>
			<div class="control-group">
				<label>Exit</label>
				<div>
					<button data-url="/control/trackball" class="control-button" title="Switch to Trackball Control (if equipped)"><i class="fas fa-bowling-ball"></i></button>
					<button data-url="/control/exit" class="control-button" title="Exit"><i class="far fa-times-circle"></i></button>
				</div>
			</div>
		</div>
		<div class="controls">
			<div class="control-group">
				<div>
					<label>Master Control</label>
					<button data-url="/control/light/all/on" class="control-button white" title="Turn all lights on"><i class="fas fa-sun"></i></button>
					<button data-url="/control/light/all/off" class="control-button white dim" title="Turn all lights off"><i class="far fa-sun"></i></button>	
				</div>
			</div>
			<div class="control-group">
				<div>
					<label>Natural White</label>
					<button data-url="/control/light/white/up" class="control-button white" title="Increase natural white light level"><i class="fas fa-lightbulb"></i></button>
					<button data-url="/control/light/white/down" class="control-button white dim" title="Decrease natural white light level"><i class="far fa-lightbulb"></i></button>	
				</div>
			</div>
			<div class="control-group">
				<label>Red</label>
				<div>
					<button data-url="/control/light/red/up" class="control-button red" title="Increase red light level"><i class="fas fa-lightbulb"></i></button>
					<button data-url="/control/light/red/down" class="control-button red dim" title="Decrease red light level"><i class="far fa-lightbulb"></i></button>
				</div>
			</div>
			<div class="control-group">
				<label>Green</label>
				<div>
					<button data-url="/control/light/green/up" class="control-button green" title="Increase green light level"><i class="fas fa-lightbulb"></i></button>
					<button data-url="/control/light/green/down" class="control-button green dim" title="Decrease green light level"><i class="far fa-lightbulb"></i></button>
				</div>
			</div>
			<div class="control-group">
				<label>Blue</label>
				<div>
					<button data-url="/control/light/blue/up" class="control-button blue" title="Increase blue light level"><i class="fas fa-lightbulb"></i></button>
					<button data-url="/control/light/blue/down" class="control-button blue dim" title="Decrease blue light level"><i class="far fa-lightbulb"></i></button>
				</div>
			</div>
		</div>
	</div>
	<script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/js/all.min.js" integrity="sha512-Tn2m0TIpgVyTzzvmxLNuqbSJH3JP8jm+Cy3hvHrW7ndTDcJ1w5mBiksqDBb8GpE2ksktFvDB/ykZ0mDpsZj20w==" crossorigin="anonymous"></script>
	<script>
		function sleep(ms) {
			return new Promise(resolve => setTimeout(resolve, ms));
		}

		var lastStatus = '';
			
		async function updateStatus() {
			var url = '/status';
			
			var xhr = new XMLHttpRequest();
			xhr.open('GET', url, true);

			xhr.responseType = 'text';
			xhr.onload = function() {
				if (xhr.readyState === xhr.DONE) {
					if (xhr.status === 200) {
						status = xhr.responseText;
						if (status !== lastStatus && status !== 'Ready') {
							lastStatus = status;
							document.getElementsByClassName('status')[0].innerHTML = status;
						}
					}
				}
			};
			xhr.send(null);
		}
		async function monitorStatus() {
			try {
				while (true) {
					await updateStatus();
					await sleep(1000);
				}
			}
			catch(ex) {
				console.warn('Could not update status', ex);
			}
		}
		monitorStatus();
		
		

		async function cycleImage() {
			try {
				// This makes the browser aware that the stream has resumed
				document.getElementsByClassName('stream')[0].style.height = Math.round(document.getElementsByClassName('stream')[0].scrollWidth * 0.5625) + 'px';
				await sleep(1000);
				document.getElementsByClassName('stream')[0].src='blank.jpg';
				await sleep(500);
				document.getElementsByClassName('stream')[0].src='stream.mjpg';
				document.getElementsByClassName('stream')[0].removeAttribute("style") // Return to responsive behavior
			}
			catch(ex) {
				console.warn('Could not cycle image', ex);
			}
		}


		var controls = document.querySelectorAll('.control-button');
		controls.forEach(element => element.addEventListener('click', event => {
			var targetElement = event.target.closest('.control-button');
			var url = targetElement.getAttribute('data-url');
			console.log(url, targetElement, targetElement.classList)
			
			var confirmedButtonAction = false;
			if (url.endsWith('/control/exit')) {
				confirmedButtonAction = confirm("Exit the camera program?");
			}
			else if (url.endsWith('/control/trackball')) {
				confirmedButtonAction = confirm("Switch to trackball control?");
			}
			else {
				confirmedButtonAction = true;
			}
			
			if (confirmedButtonAction == true) {
				/* Toggle blink on record button */
				if (url.endsWith('/control/capture/video')) {
					if (targetElement.classList.contains('blink')) {
						targetElement.classList.remove('blink');
					}
					else {
						targetElement.classList.add('blink');
					}
				}
				
				var xhr = new XMLHttpRequest();
				xhr.open('GET', url);
				xhr.send();
				cycleImage();
			}
		}));
	</script>
</body>
</html>
"""

class StreamingOutput(io.BufferedIOBase):
	def __init__(self):
		self.frame = None
		self.condition = Condition()

	def write(self, streamBuffer):
		with self.condition:
			self.frame = streamBuffer
			self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
	def do_GET(self):
		global output
		if self.path == '/':
			contentEncoded = PAGE.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', len(contentEncoded))
			self.end_headers()
			self.wfile.write(contentEncoded)
		elif self.path == '/stream.mjpg' or self.path == '/blank.jpg':
			console.info('Requesting stream...')
			self.send_response(200)
			self.send_header('Age', 0)
			self.send_header('Cache-Control', 'no-cache, private')
			self.send_header('Pragma', 'no-cache')
			self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
			self.end_headers()
			try:
				while True:
					with output.condition:
						output.condition.wait()
						frame = output.frame
					self.wfile.write(b'--FRAME\r\n')
					self.send_header('Content-Type', 'image/jpeg')
					self.send_header('Content-Length', len(frame))
					self.end_headers()
					self.wfile.write(frame)
					self.wfile.write(b'\r\n')
			except Exception as ex:
				console.warn('Request failed: ' + str(ex))
				pass
		elif self.path == '/status':
			content = globals.statusDictionary['message']
			if len(content) == 0:
				content = "Ready"
			contentEncoded = content.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', len(contentEncoded))
			self.end_headers()
			self.wfile.write(contentEncoded)
		elif self.path.startswith('/control/'):
			if self.path == '/control/capture/photo':	
				globals.buttonDictionary.update({'capture': True})

			elif self.path == '/control/capture/video':	
				globals.buttonDictionary.update({'captureVideo': True})

			elif self.path == '/control/shutter/up':	
				globals.buttonDictionary.update({'shutterUp': True})

			elif self.path == '/control/shutter/down':	
				globals.buttonDictionary.update({'shutterDown': True})

			elif self.path == '/control/iso/up':	
				globals.buttonDictionary.update({'isoUp': True})

			elif self.path == '/control/iso/down':	
				globals.buttonDictionary.update({'isoDown': True})

			elif self.path == '/control/ev/up':	
				globals.buttonDictionary.update({'evUp': True})

			elif self.path == '/control/ev/down':	
				globals.buttonDictionary.update({'evDown': True})

			elif self.path == '/control/bracket/up':	
				globals.buttonDictionary.update({'bracketUp': True})

			elif self.path == '/control/bracket/down':	
				globals.buttonDictionary.update({'bracketDown': True})

			elif self.path == '/control/exit':	
				globals.buttonDictionary.update({'exit': True})

			elif self.path == '/control/trackball':	
				globals.buttonDictionary.update({'trackball': True})

			elif self.path == '/control/light/all/on':	
				globals.buttonDictionary.update({'lightW': 255})
				globals.buttonDictionary.update({'lightR': 255})
				globals.buttonDictionary.update({'lightG': 255})
				globals.buttonDictionary.update({'lightB': 255})

			elif self.path == '/control/light/all/off':	
				globals.buttonDictionary.update({'lightW': 0})
				globals.buttonDictionary.update({'lightR': 0})
				globals.buttonDictionary.update({'lightG': 0})
				globals.buttonDictionary.update({'lightB': 0})

			elif self.path == '/control/light/white/up':	
				if globals.buttonDictionary['lightW'] < 255:
					globals.buttonDictionary.update({'lightW': globals.buttonDictionary['lightW'] + 1})
				else: 
					globals.buttonDictionary.update({'lightW': 0})

			elif self.path == '/control/light/white/down':	
				if globals.buttonDictionary['lightW'] > 0:
					globals.buttonDictionary.update({'lightW': globals.buttonDictionary['lightW'] - 1})
				else: 
					globals.buttonDictionary.update({'lightW': 255})

			elif self.path == '/control/light/red/up':	
				if globals.buttonDictionary['lightR'] < 255:
					globals.buttonDictionary.update({'lightR': globals.buttonDictionary['lightR'] + 1})
				else: 
					globals.buttonDictionary.update({'lightR': 0})

			elif self.path == '/control/light/red/down':	
				if globals.buttonDictionary['lightR'] > 0:
					globals.buttonDictionary.update({'lightR': globals.buttonDictionary['lightR'] - 1})
				else: 
					globals.buttonDictionary.update({'lightR': 255})

			elif self.path == '/control/light/green/up':	
				if globals.buttonDictionary['lightG'] < 255:
					globals.buttonDictionary.update({'lightG': globals.buttonDictionary['lightG'] + 1})
				else: 
					globals.buttonDictionary.update({'lightG': 0})

			elif self.path == '/control/light/green/down':	
				if globals.buttonDictionary['lightG'] > 0:
					globals.buttonDictionary.update({'lightG': globals.buttonDictionary['lightG'] - 1})
				else: 
					globals.buttonDictionary.update({'lightG': 255})

			elif self.path == '/control/light/blue/up':	
				if globals.buttonDictionary['lightB'] < 255:
					globals.buttonDictionary.update({'lightB': globals.buttonDictionary['lightB'] + 1})
				else: 
					globals.buttonDictionary.update({'lightB': 0})

			elif self.path == '/control/light/blue/down':	
				if globals.buttonDictionary['lightB'] > 0:
					globals.buttonDictionary.update({'lightB': globals.buttonDictionary['lightB'] - 1})
				else: 
					globals.buttonDictionary.update({'lightB': 255})

			Light.updateLight()
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', 0)
			self.end_headers()
		elif self.path == '/favicon.ico':
			self.send_response(200)
			self.send_header('Content-Type', 'image/x-icon')
			self.send_header('Content-Length', 0)
			self.end_headers()
		else:
			self.send_error(404)
			self.end_headers()



class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
	allow_reuse_address = True
	daemon_threads = True


def startStream(camera, previewConfiguration, running):
	global output
	camera.configure(previewConfiguration)
	output = StreamingOutput()
	camera.start_recording(MJPEGEncoder(), FileOutput(output))
	hostname = subprocess.getoutput('hostname -I')
	url = 'http://' + str(hostname)
	print('\n Remote Interface: ' + url + '\n')
	try:
		address = ('', 80)
		server = StreamingServer(address, StreamingHandler)
		server.logging = False
		server.serve_forever()
	finally:
		camera.stop_recording()
		print('\n Stream ended \n')


def resumeStream(camera, previewConfiguration, running):
	global output
	camera.configure(previewConfiguration)
	output = StreamingOutput()
	camera.start_recording(JpegEncoder(), FileOutput(output))
	print(" Resuming preview... ")


def pauseStream(camera):
	try:
		camera.stop_recording()
		time.sleep(1)
		print(" Pausing preview... ")
	except Exception as ex:
		print(str(ex))
		pass
