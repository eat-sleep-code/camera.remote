import board
import neopixel

pixels = neopixel.NeoPixel(board.D18, 16, pixel_order=neopixel.GRBW)   # GPIO 18 = PIN 12  /// 16 = Number of NeoPixels

class Light():

	# === NeoPixel RGBW LED Color Handlers ====================================

	def off():
		pixels.fill((0,0,0,0))
		pixels.show()

	def updateLight(buttonDictionary):
		red = buttonDictionary['lightR']
		blue = buttonDictionary['lightG']
		green = buttonDictionary['lightB']
		white = buttonDictionary['lightW']
		pixels.fill((red, blue, green, white))
		pixels.show()