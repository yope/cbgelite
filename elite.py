#!/usr/bin/env python3


from cbg import CBG, G3d
from ship import ShipReader
import sys
from time import sleep
from math import sin

class BarGraph:
	def __init__(self, cbg, x, y, w, h, fg, bg, ticks=0):
		self.value = 1.0
		self.minval = 0.0
		self.w = w
		self.h = h
		self.x = x
		self.y = y
		self.fg = fg
		self.bg = bg
		self.cbg = cbg
		self.ticks = ticks

	def setup(self):
		self.cbg.colorrect(self.x, self.y + 2, self.w, self.h-3, self.fg, self.bg)

	def set_value(self, v):
		v = max(self.minval, v)
		v = min(1.0, v)
		self.value = v

	def draw_ticks(self):
		if self.ticks < 2:
			return
		ts = (self.w - 1) // (self.ticks - 1)
		for i in range(self.ticks):
			self.cbg.putpixel(self.x + i * ts, self.y + self.h - 1)

	def redraw(self):
		self.cbg.fillrect(self.x, self.y + 2, int(self.value * self.w), self.h - 4)
		self.draw_ticks()

class Meter(BarGraph):
	def __init__(self, cbg, x, y, w, h, fg, bg, ticks=0):
		super().__init__(cbg, x, y, w, h, fg, bg, ticks=ticks)
		self.value = 0.0
		self.minval = -1.0

	def redraw(self):
		v = (self.value - self.minval) / (1.0 - self.minval)
		xp = self.x + int(v * self.w)
		self.cbg.line(xp, self.y + 2, xp, self.y + self.h - 3)
		self.draw_ticks()

class Battery:
	def __init__(self, cbg, x, y, bw, bh):
		self.value = 1.0
		self.bars = []
		for i in range(4):
			self.bars.append(BarGraph(cbg, x, y + i * 8, bw, bh, 5, 0))

	def setup(self):
		for b in self.bars:
			b.setup()

	def set_value(self, v):
		self.value = v
		for i in range(4):
			vb = v * 4.0 - (3.0 - i)
			self.bars[i].set_value(vb)

	def redraw(self):
		for b in self.bars:
			b.redraw()

class Radar:
	def __init__(self, cbg, x, y, w, h):
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.sradw = 22
		self.sradh = 22
		self.sradx = x + w - self.sradw
		self.srady = y - 6
		self.cbg = cbg

	def setup(self):
		self.cbg.colorrect(self.x + 2, self.y + 2, self.w - 4, self.h - 4, 1, 0)
		self.cbg.colorrect(self.sradx, self.srady, self.sradw + 2, self.sradh + 4, 13, 0)

	def redraw_srad(self):
		cx = self.sradx + self.sradw // 2
		cy = self.srady + self.sradh // 2
		a = self.sradw
		b = self.sradh
		self.cbg.ellipse(cx, cy, a, b)

	def redraw(self):
		cx = self.x + self.w // 2
		cy = self.y + self.h // 2
		a = self.w - 24
		b = self.h - 12
		self.cbg.ellipse(cx, cy, a, b)
		self.redraw_srad()
		self.cbg.line(cx, cy + b // 2, cx, cy - b // 2, pattern=0xaaaa)
		self.cbg.line(cx - a // 2, cy - 2, cx + a // 2, cy - 2, pattern=0x8888)
		self.cbg.line(cx - a // 2 + 14, cy - b // 4 - 3, cx + a // 2 - 14, cy - b // 4 - 3, pattern=0x8888)
		self.cbg.line(cx - a // 2 + 8, cy + b // 4 + 1, cx + a // 2 - 8, cy + b // 4 + 1, pattern=0x8888)
		self.cbg.line(cx - int(a/6.5), cy - b // 2 + 2, cx - int(a/2.5), cy + b // 2 - 9, pattern=0xaaaa)
		self.cbg.line(cx + int(a/6.5), cy - b // 2 + 2, cx + int(a/2.5), cy + b // 2 - 9, pattern=0xaaaa)
		self.cbg.line(cx - int(a/6.5), cy - b // 2 + 2, cx, cy - 3, pattern=0x8888)
		self.cbg.line(cx + int(a/6.5), cy - b // 2 + 2, cx, cy - 3, pattern=0x8888)

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
		self.bgnames = ["FS", "AS", "FV", "CT", "LT", "AL"]
		rbx = self.sboxw + self.radarw + 2
		self.battery = Battery(self.cbg, rbx, self.ystatus + 28, 40, 7)
		self.speedbar = BarGraph(self.cbg, rbx, self.ystatus + 4, 40, 7, 11, 0, ticks=8)
		self.rlmeter = Meter(self.cbg, rbx, self.ystatus + 12, 40, 7, 14, 0, ticks=8)
		self.dcmeter = Meter(self.cbg, rbx, self.ystatus + 20, 40, 7, 14, 0, ticks=8)
		self.radar = Radar(self.cbg, self.sboxw + 1, self.ystatus + 8, self.radarw - 2, self.hstatus - 10)

	def setup_screen(self):
		self.cbg.colorrect(0, 0, self.width, self.height, 11, 0)
		self.cbg.colorrect(2, 4, self.width-3, self.ystatus-4, 15, 0)
		bglen = 40
		bgcolors = [5, 5, 3, 1, 1, 10]
		bgticks = [0, 0, 6, 5, 6, 5]
		bgvals = [1.0, 1.0, 0.4, 0.1, 0.0, 0.6]
		for i in range(7):
			y = self.ystatus + 10 + i * 8
			x2 = self.sboxw + self.radarw
			self.cbg.colorrect(self.sboxw - bglen, y, bglen, 4, 2, 0)
			self.cbg.colorrect(x2+2, y, bglen, 4, 2, 0)
			if i==6:
				continue
			bgr = BarGraph(self.cbg, self.sboxw-bglen, y-6, bglen, 7, bgcolors[i], 0, bgticks[i])
			bgr.set_value(bgvals[i])
			setattr(self, "bar_"+self.bgnames[i].lower(), bgr)
			bgr.setup()
		self.cbg.colorrect(2, self.ystatus+6, 18, 16, 15, 0)
		self.cbg.colorrect(self.width-20, self.ystatus+6, 16, 24, 14, 0)
		self.cbg.colorrect(2, self.ystatus+6+16, 18, 32, 14, 0)
		self.cbg.colorrect(self.width-20, self.ystatus+6+24, 16, 32, 15, 0)
		self.battery.setup()
		self.speedbar.setup()
		self.rlmeter.setup()
		self.dcmeter.setup()
		self.radar.setup()

	def draw_background(self):
		self.cbg.rect(1, 2, self.width-2, self.height-4)
		self.cbg.line(1, self.ystatus, self.width-1, self.ystatus)
		self.cbg.line(self.sboxw, self.ystatus, self.sboxw, self.height-2)
		self.cbg.line(self.sboxw + self.radarw + 1, self.ystatus, self.sboxw + self.radarw + 1, self.height-2)
		tl = self.bgnames
		tl.append("MI")
		tr = ["SP", "RL", "DC", "1", "2", "3", "4"]
		bglen = 40
		for i in range(7):
			y = self.ystatus + 11 + i * 8
			x2 = self.sboxw + self.radarw + 1
			self.cbg.line(self.sboxw - bglen, y, self.sboxw, y)
			self.cbg.line(x2, y, x2 + bglen, y)
			self.cbg.drawtext(4, y-5, tl[i])
			self.cbg.drawtext(self.width-20, y-5, tr[i])
			if i<6:
				getattr(self, "bar_"+self.bgnames[i].lower()).redraw()
		self.battery.redraw()
		self.speedbar.redraw()
		self.rlmeter.redraw()
		self.dcmeter.redraw()
		self.radar.redraw()

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
		self.setup_screen()
		while True:
			self.g3d.setRotMat(rx, ry, rz)
			self.g3d.setTranslation((0, 0, dz))
			self.cbg.clearmap()
			self.draw_title()
			self.g3d.draw_ship(self.ships["cobra_mk3"])
			self.cbg.redraw_screen()
			ry += 0.1
			rz += 0.03
			self.bar_fs.set_value(0.5+0.5*sin(rz))
			sleep(0.04)

	def run(self):
		self.title_screen()

if __name__ == "__main__":
	e = Elite()
	e.run()
