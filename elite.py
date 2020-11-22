#!/usr/bin/env python3
#
# Copyright (c) 2020 David Jander <djander@gmail.com>
#
# This file is part of CBGElite.
#
# CBGElite is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# CBGElite is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CBGElite.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
from cbg import CBG, G3d
from ship import AllShips
import sys
from time import sleep, monotonic
from math import sin, sqrt
from microverse import Microverse
from ai import BaseAi
from control import Control, BaseDev

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
	def __init__(self, cbg, m, x, y, w, h):
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.cx = self.x + self.w // 2
		self.cy = self.y + self.h // 2
		self.rradx = self.w // 2 - 12
		self.rrady = self.h // 2 - 6
		self.rradz = (self.rrady * 2) // 2.5
		self.rrange = 10000
		self.sradw = 22
		self.sradh = 22
		self.sradx = x + w - self.sradw
		self.srady = y - 6
		self.cbg = cbg
		self.m = m
		self.pmaxdist = 200000
		self.near_station = False

	def setup(self):
		self.cbg.colorrect(self.x + 2, self.y + 2, self.w - 4, self.h - 4, 1, 0)
		self.cbg.colorrect(self.sradx, self.srady, self.sradw + 2, self.sradh + 4, 13, 0)

	def redraw_srad(self):
		cx = self.sradx + self.sradw // 2
		cy = self.srady + self.sradh // 2
		a = self.sradw
		b = self.sradh
		self.cbg.ellipse(cx, cy, a, b)
		if not self.m.planet:
			pplanet = (0, 0, 1000)
		else:
			pplanet = self.m.planet.pos
		if self.m.station:
			pstation = self.m.station.pos
			ds = self.m.g3d.distv(pstation)
			if ds < 75000:
				pplanet = pstation
				self.near_station = True
			else:
				self.near_station = False
		if self.near_station:
			self.cbg.drawtext(cx, cy + 40, "S", fg=4)
		pm = self.pmaxdist
		px, py, pz = pplanet
		dp = self.m.g3d.distv(pplanet)
		px /= dp
		py /= dp
		pz /= dp
		pxr = int(px * a / 2)
		pyr = int(py * b / 2)
		pxr += cx - 1
		pyr += cy - 1
		if pz > 0:
			self.cbg.fillrect(pxr, pyr, 3, 3)
		else:
			self.cbg.rect(pxr, pyr, 2, 2)

	def redraw(self):
		cx = self.cx
		cy = self.cy
		a = self.rradx * 2
		b = self.rrady * 2
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
		self.redraw_objects()

	def redraw_objects(self):
		objs = self.m.get_objects()
		for o in objs:
			p = o.get_viewpos()
			d = sqrt(sum([n*n for n in p]))
			if d > self.rrange:
				continue
			x = int(p[0] * self.rradx / self.rrange) + self.cx
			y = int(-p[2] * self.rrady / self.rrange) + self.cy
			bh = int(p[1] * self.rradz / self.rrange)
			if bh < 0:
				self.cbg.fillrect(x, y + bh, 2, -bh)
				self.cbg.fillrect(x, y + bh - 1, 4, 2)
			elif bh >= 0:
				if bh:
					self.cbg.fillrect(x, y, 2, bh)
				self.cbg.fillrect(x - 2, y + bh - 1, 4, 2)

class Laser:
	def __init__(self, cbg, x, y, w, h):
		self.cbg = cbg
		self.type = "pulse"
		self.cx = x + w // 2
		self.cy = y + h // 2
		self.w = w
		self.h = h
		self.trg = None
		self.highlite_count = 0
		self.highlite_count_max = 16

	def set_type(self, t):
		self.type = t

	def draw(self, m, trg):
		if trg is not self.trg:
			if trg:
				m.set_subtext(trg.name)
			self.trg = trg
		if trg:
			self.highlite_count -= 1
			if self.highlite_count < 0:
				self.highlite_count = self.highlite_count_max
		else:
			self.highlite_count = 0
		getattr(self, "draw_" + self.type)()

	def draw_pulse(self):
		p = int(4.0 / (self.highlite_count_max + 1 - self.highlite_count))
		r0 = 10 + p
		l = 12
		r1 = 10 + l + p
		self.cbg.fillrect(self.cx - r1, self.cy, l, 2)
		self.cbg.fillrect(self.cx + r0, self.cy, l, 2)
		self.cbg.fillrect(self.cx, self.cy - r1, 2, l)
		self.cbg.fillrect(self.cx, self.cy + r0, 2, l)

class Elite:
	def __init__(self, loop=None, config=False):
		self.loop = loop or asyncio.get_event_loop()
		self.cbg = CBG()
		if self.cbg.width < 320 or self.cbg.height < 240:
			print("Screen is too small.")
			print("Please resize your terminal to minimal 160x60 characters.")
			self.cbg.exit(2)
		ctrl = Control(self.cbg)
		if config:
			ctrl.edit_controls()
		else:
			ctrl.load_mapping()
		self.inputdev = ctrl.get_evdev()
		self.ships = AllShips("all_ships.ship").ships
		self.width = 320
		self.height = 240
		self.hstatus = 64
		self.ystatus = self.height - self.hstatus - 1
		self.spaceclip = (4, 4, self.width - 4, self.ystatus - 4)
		self.sboxw = 64
		self.radarw = self.width-2*self.sboxw
		self.g3d = G3d(self.cbg, cx = self.width // 2, cy = self.ystatus // 2)
		self.bgnames = ["FS", "AS", "FV", "CT", "LT", "AL"]
		rbx = self.sboxw + self.radarw + 2
		self.battery = Battery(self.cbg, rbx, self.ystatus + 28, 40, 7)
		self.speedbar = BarGraph(self.cbg, rbx, self.ystatus + 4, 40, 7, 11, 0, ticks=8)
		self.rlmeter = Meter(self.cbg, rbx, self.ystatus + 12, 40, 7, 14, 0, ticks=8)
		self.dcmeter = Meter(self.cbg, rbx, self.ystatus + 20, 40, 7, 14, 0, ticks=8)
		self.laser = Laser(self.cbg, 0, 0, self.width, self.ystatus)
		self.m = Microverse(self.cbg, self.g3d, self.laser, self.ships)
		self.radar = Radar(self.cbg, self.m, self.sboxw + 1, self.ystatus + 8, self.radarw - 2, self.hstatus - 10)

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

	async def title_screen(self, showfps=False):
		dz = 20050
		self.setup_screen()
		tm = Microverse(self.cbg, self.g3d, None, self.ships, particles=0)
		cobra = tm.spawn("cobra_mkiii", (0, 0, dz), 0.0, 0.0)
		if showfps:
			t0 = monotonic()
			fr = 0
			fps = 0.0
		ts = monotonic()
		while True:
			if dz > 550:
				dz -= 150
				cobra.pos = (0.0, 0.0, dz)
			self.cbg.clearmap()
			self.draw_title()
			self.cbg.setclip(self.spaceclip)
			cobra.local_roll_pitch(0.1, 0.03)
			tm.draw()
			self.cbg.setclip(None)
			self.cbg.redraw_screen()
			self.inputdev.handle()
			if 1 in self.inputdev.get_keys():
				break
			if showfps:
				print("\x1b[2;2HFPS:{:.2f}".format(fps))
			else:
				ts = await self.framsleep(ts)
				continue
			fr += 1
			if fr > 10:
				t = monotonic()
				fps = fr / (t - t0)
				t0 = t
				fr = 0
			await asyncio.sleep(0)

	async def framsleep(self, ts):
		now = self.loop.time()
		dt = max(0.0, ts + 0.04 - now)
		await asyncio.sleep(dt)
		return now

	async def microtest(self):
		self.setup_screen()
		m = self.m
		cobra = m.spawn("cobra_mkiii", (-500, 0, 10000), 0.0, 0.0)
		cobra.add_ai(BaseAi)
		viper = m.spawn("krait",       (1500, 0, 5000), -0.5, 2.0)
		viper.add_ai(BaseAi)
		trans = m.spawn("transporter", (0, 1500, 5000), -0.5, 2.0)
		fdl = m.spawn("fer-de-lance",  (0, -1500, 5000), -0.5, 2.0)
		fdl.add_ai(BaseAi)
		asteroid0 = m.spawn("asteroid", (1500, -1500, -5000), -0.1, 1.0)
		asteroid1 = m.spawn("asteroid", (-1500, 1500, -5000), 0.1, -1.0)
		roll = 0.0
		pitch = 0.0
		p1 = 0.005
		ts = monotonic()
		speed = 0.0
		while True:
			self.inputdev.handle()
			roll = self.inputdev.get_roll() * 0.03
			pitch = self.inputdev.get_pitch() * 0.03
			speed = self.inputdev.get_throttle() * 15.0
			nbtns = self.inputdev.get_new_buttons()
			m.set_speed(speed)
			if BaseDev.BTN_JUMP in nbtns:
				m.jump()
			m.handle()
			self.speedbar.set_value(speed / 15)
			self.rlmeter.set_value(roll * 33)
			self.dcmeter.set_value(pitch * 33)
			self.cbg.clearmap()
			self.draw_background()
			self.cbg.setclip(self.spaceclip)
			m.set_roll_pitch(roll, pitch)
			self.m.station.local_roll_pitch(0.005, 0.0)
			m.draw()
			self.cbg.setclip(None)
			self.cbg.redraw_screen()
			ts = await self.framsleep(ts)

	async def startup(self, showfps=False):
		mt = self.loop.create_task(self.run(showfps))
		mt.add_done_callback(lambda fut: self.cbg.exit(fut.result()))

	async def run(self, showfps=False):
		await self.title_screen(showfps)
		await self.microtest()
		return 0

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	showfps = ("-fps" in sys.argv)
	config = ("-config" in sys.argv)
	e = Elite(config=config)
	loop.run_until_complete(e.startup(showfps=showfps))
	loop.run_forever()
