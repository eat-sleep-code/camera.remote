import io
import logging
import socketserver
import subprocess
from light import Light
from picamera import PiCamera
from threading import Condition
from http import server

global buttonDictionary

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
			font-size: 12px;
			display: flex;
			justify-content: center;
			line-height: 12px;
			height: 24px;
			padding: 6px;
			text-align: center;
			width: 90px;
		}

		.controls > label
		{
			width: 100%;
		}

		.control-button
		{
			border: solid 1px rgba(255, 255, 255, 1.0);
			border-radius: 4px;
			color: rgba(255, 255, 255, 1.0);
			display: inline-block;
			font-size: 36px;
			height: 42px;
			margin: 3px;
			text-align: center;
			text-decoration: none;
			width: 42px;
			opacity: 0.9;
		}

		.control-button:hover
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
					<a href="/control/capture/photo" class="control-button" title="Capture Photo">&#10030;</a>
					<a href="/control/capture/video" class="control-button red" title="Capture Video">&#9679</a>
				</div>
			</div>
			<div class="control-group">
				<label>Shutter Speed</label>
				<div>
					<a href="/control/shutter/up" class="control-button" title="Increase Shutter Speed (Shorter)">&#8853;</a>
					<a href="/control/shutter/down" class="control-button" title="Decrease Shutter Speed (Longer)">&#8854;</a>
				</div>
			</div>
			<div class="control-group">
				<label>ISO</label>
				<div>
					<a href="/control/iso/up" class="control-button" title="Increase ISO">&#8853;</a>
					<a href="/control/iso/down" class="control-button" title="Decrease ISO">&#8854;</a>
				</div>
			</div>
			<div class="control-group">
				<label>Exposure Compensation</label>
				<div>
					<a href="/control/ev/up" class="control-button" title="Increase Exposure Compensation">&#8853;</a>
					<a href="/control/ev/down" class="control-button" title="Decrease Exposure Compensation">&#8854;</a>
				</div>
			</div>
			<div class="control-group">
				<label>Bracketing</label>
				<div>
					<a href="/control/bracket/up" class="control-button" title="Increase Bracket Stops">&#8853;</a>
					<a href="/control/bracket/down" class="control-button" title="Decrease Bracket Stops">&#8854;</a>
				</div>
			</div>
		</div>
		<div class="controls">
			<label>Scene Lighting</label>
			<div class="control-group">
				<div>
					<a href="/control/light/all/on" class="control-button white" title="Turn all lights on">&#10050;</a>
					<a href="/control/light/all/off" class="control-button white dim" title="Turn all lights off">&#9790;</a>	
				</div>
			</div>
			<div class="control-group">
				<div>
					<a href="/control/light/white/up" class="control-button white" title="Increase natural white light level">&#9728;</a>
					<a href="/control/light/white/down" class="control-button white dim" title="Decrease natural white light level">&#9728;</a>	
				</div>
			</div>
			<div class="control-group">
				<div>
					<a href="/control/light/red/up" class="control-button red" title="Increase red light level">&#9728;</a>
					<a href="/control/light/red/down" class="control-button red dim" title="Decrease red light level">&#9728;</a>
				</div>
			</div>
			<div class="control-group">
				<div>
					<a href="/control/light/green/up" class="control-button green" title="Increase green light level">&#9728;</a>
					<a href="/control/light/green/down" class="control-button green dim" title="Decrease green light level">&#9728;</a>
				</div>
			</div>
			<div class="control-group">
				<div>
					<a href="/control/light/blue/up" class="control-button blue" title="Increase blue light level">&#9728;</a>
					<a href="/control/light/blue/down" class="control-button blue dim" title="Decrease blue light level">&#9728;</a>
				</div>
			</div>
		</div>
	</div>
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
			var targetElement = event.target;
			var url = targetElement.href;
			console.log(url, targetElement, targetElement.classList)
			
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
			event.preventDefault();
			cycleImage();
			
			
		}));

		
	</script>

		
	</script>
</body>
</html>
"""

class StreamingOutput(object):
	def __init__(self):
		self.frame = None
		self.buffer = io.BytesIO()
		self.condition = Condition()

	def write(self, streamBuffer):
		if streamBuffer.startswith(b'\xff\xd8'):
			self.buffer.truncate()
			with self.condition:
				self.frame = self.buffer.getvalue()
				self.condition.notify_all()
			self.buffer.seek(0)
		return self.buffer.write(streamBuffer)


class StreamingHandler(server.BaseHTTPRequestHandler):
	def log_message(self, format, *args):
		pass

	def do_GET(self):
		global output
		global statusDictionary
		global buttonDictionary
		if self.path == '/':
			contentEncoded = PAGE.encode('utf-8')
			self.send_response(200)
			self.send_header('Content-Type', 'text/html')
			self.send_header('Content-Length', len(contentEncoded))
			self.end_headers()
			self.wfile.write(contentEncoded)
		elif self.path == '/stream.mjpg' or self.path == '/blank.jpg':
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
				pass
		elif self.path == '/status':
			content = statusDictionary['message']
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
				buttonDictionary.update({'capture': True})

			elif self.path == '/control/capture/video':	
				buttonDictionary.update({'captureVideo': True})

			elif self.path == '/control/shutter/up':	
				buttonDictionary.update({'shutterUp': True})

			elif self.path == '/control/shutter/down':	
				buttonDictionary.update({'shutterDown': True})

			elif self.path == '/control/iso/up':	
				buttonDictionary.update({'isoUp': True})

			elif self.path == '/control/iso/down':	
				buttonDictionary.update({'isoDown': True})

			elif self.path == '/control/ev/up':	
				buttonDictionary.update({'evUp': True})

			elif self.path == '/control/ev/down':	
				buttonDictionary.update({'evDown': True})

			elif self.path == '/control/bracket/up':	
				buttonDictionary.update({'bracketUp': True})

			elif self.path == '/control/bracket/down':	
				buttonDictionary.update({'bracketDown': True})

			elif self.path == '/control/light/all/on':	
				buttonDictionary.update({'lightW': 255})
				buttonDictionary.update({'lightR': 255})
				buttonDictionary.update({'lightG': 255})
				buttonDictionary.update({'lightB': 255})

			elif self.path == '/control/light/all/off':	
				buttonDictionary.update({'lightW': 0})
				buttonDictionary.update({'lightR': 0})
				buttonDictionary.update({'lightG': 0})
				buttonDictionary.update({'lightB': 0})

			elif self.path == '/control/light/white/up':	
				if buttonDictionary['lightW'] < 255:
					buttonDictionary.update({'lightW': buttonDictionary['lightW'] + 1})
				else: 
					buttonDictionary.update({'lightW': 0})

			elif self.path == '/control/light/white/down':	
				if buttonDictionary['lightW'] > 0:
					buttonDictionary.update({'lightW': buttonDictionary['lightW'] - 1})
				else: 
					buttonDictionary.update({'lightW': 255})

			elif self.path == '/control/light/red/up':	
				if buttonDictionary['lightR'] < 255:
					buttonDictionary.update({'lightR': buttonDictionary['lightR'] + 1})
				else: 
					buttonDictionary.update({'lightR': 0})

			elif self.path == '/control/light/red/down':	
				if buttonDictionary['lightR'] > 0:
					buttonDictionary.update({'lightR': buttonDictionary['lightR'] - 1})
				else: 
					buttonDictionary.update({'lightR': 255})

			elif self.path == '/control/light/green/up':	
				if buttonDictionary['lightG'] < 255:
					buttonDictionary.update({'lightG': buttonDictionary['lightG'] + 1})
				else: 
					buttonDictionary.update({'lightG': 0})

			elif self.path == '/control/light/green/down':	
				if buttonDictionary['lightG'] > 0:
					buttonDictionary.update({'lightG': buttonDictionary['lightG'] - 1})
				else: 
					buttonDictionary.update({'lightG': 255})

			elif self.path == '/control/light/blue/up':	
				if buttonDictionary['lightB'] < 255:
					buttonDictionary.update({'lightB': buttonDictionary['lightB'] + 1})
				else: 
					buttonDictionary.update({'lightB': 0})

			elif self.path == '/control/light/blue/down':	
				if buttonDictionary['lightB'] > 0:
					buttonDictionary.update({'lightB': buttonDictionary['lightB'] - 1})
				else: 
					buttonDictionary.update({'lightB': 255})

			Light.updateLight(buttonDictionary)
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


def startStream(camera, running, parentStatusDictionary, parentButtonDictionary):
	global output
	global statusDictionary 
	global buttonDictionary
	statusDictionary = parentStatusDictionary
	buttonDictionary = parentButtonDictionary
	camera.resolution = (1920, 1080)
	camera.framerate = 30

	output = StreamingOutput()
	camera.start_recording(output, format='mjpeg')
	hostname = subprocess.getoutput('hostname -I')
	url = 'http://' + str(hostname)
	print('\n Remote Interface: ' + url + '\n')
	try:
		address = ('', 80)
		server = StreamingServer(address, StreamingHandler)
		server.allow_reuse_address = True
		server.logging = False
		server.serve_forever()
	finally:
		camera.stop_recording()
		print('\n Stream ended \n')


def resumeStream(camera, running, parentStatusDictionary, parentButtonDictionary):
	global output
	global statusDictionary 
	global buttonDictionary
	statusDictionary = parentStatusDictionary
	buttonDictionary = parentButtonDictionary
	camera.resolution = (1920, 1080)
	camera.framerate = 30
	output = StreamingOutput()
	camera.start_recording(output, format='mjpeg')
	print(" Resuming preview... ")


def pauseStream(camera):
	try:
		camera.stop_recording()
		print(" Pausing preview... ")
	except Exception as ex:
		print(str(ex))
		pass
