#!/usr/bin/env python3


from cbg import CBG, G3d
from ship import ShipReader
import sys
from time import sleep

class Elite:
	def __init__(self):
		self.cbg = CBG()
		if self.cbg.width < 320 or self.cbg.height < 240:
			print("Screen is too small.")
			print("Please resize your terminal to minimal 160x60 characters.")
			sys.exit(2)
		shipnames = [
			"asteroid",
			"cargo",
			"cobra_mk3",
			"coriolis",
			"escape",
			"mamba",
			"missile",
			"python",
			"sidewinder",
			"thargoid",
			"thargon",
			"viper"
		]
		self.ships = {sn:ShipReader(sn+".ship") for sn in shipnames}
		self.width = 320
		self.height = 240
		self.hstatus = 64
		self.ystatus = self.height - self.hstatus - 1
		self.sboxw = 64
		self.radarw = self.width-2*self.sboxw
		self.g3d = G3d(self.cbg, cx = self.width // 2, cy = self.ystatus // 2)

	def draw_background(self):
		self.cbg.rect(0, 0, self.width-1, self.height-1)
		self.cbg.line(0, self.ystatus, self.width-1, self.ystatus)
		self.cbg.line(self.sboxw, self.ystatus, self.sboxw, self.height-1)
		self.cbg.line(self.sboxw + self.radarw, self.ystatus, self.sboxw + self.radarw, self.height-1)
		for i in range(6):
			y = self.ystatus + 9 + i * 9
			bglen = 40
			x2 = self.sboxw + self.radarw
			self.cbg.line(self.sboxw - bglen, y, self.sboxw, y)
			self.cbg.line(x2, y, x2 + bglen, y)

	def draw_title(self):
		self.draw_background()
		sw = self.width
		tx = sw // 2 - 80
		self.cbg.drawtext(tx, 8, "---- E L I T E ----")
		tx = sw // 2 - 80
		self.cbg.drawtext(tx, self.ystatus - 16, "Commander Jameson")

	def title_screen(self):
		rx = 0.0
		ry = 0.0
		rz = 0.0
		dz = 150
		while True:
			self.g3d.setRotMat(rx, ry, rz)
			self.g3d.setTranslation((0, 0, dz))
			self.cbg.clearmap()
			self.draw_title()
			self.g3d.draw_ship(self.ships["cobra_mk3"])
			self.cbg.redraw_screen()
			ry += 0.1
			rz += 0.03
			sleep(0.04)

	def run(self):
		self.title_screen()

if __name__ == "__main__":
	e = Elite()
	e.run()
