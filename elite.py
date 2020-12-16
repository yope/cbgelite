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
from random import randint, uniform
from cbg import CBG, G3d
from ship import AllShips
import sys
from time import sleep, monotonic
from math import sin, sqrt
from microverse import Microverse
from universe import Universe
from ai import BaseAi
from control import Control, BaseDev
from collections import deque

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
	def __init__(self, cbg, cockpit, x, y, w, h):
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.cockpit = cockpit
		self.cx = self.x + self.w // 2
		self.cy = self.y + self.h // 2
		self.rradx = self.w // 2 - 12
		self.rrady = self.h // 2 - 6
		self.rradz = (self.rrady * 2) // 2.5
		self.rrange = 20000
		self.sradw = 22
		self.sradh = 22
		self.sradx = x + w - self.sradw
		self.srady = y - 6
		self.cbg = cbg
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
		m = self.cockpit.m
		if not m.planet:
			px, py, pz = (0, 0, 1000)
			dp = 1000
		else:
			px, py, pz = m.planet.pos
			dp = m.get_planet_dist()
		if m.station:
			ds = m.get_station_dist()
			if ds < 55000:
				px, py, pz = m.station.pos
				self.near_station = True
				dp = ds
			else:
				self.near_station = False
		if self.near_station:
			self.cbg.drawtext(cx, cy + 40, "S", fg=4)
		pm = self.pmaxdist
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
		objs = self.cockpit.m.get_objects()
		for o in objs:
			p = o.get_viewpos()
			d = o.distance
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
	def __init__(self, cp, x, y, w, h):
		self.cp = cp
		self.cbg = cp.cbg
		self.g3d = cp.g3d
		self.type = "pulse"
		self.cx = x + w // 2
		self.cy = y + h // 2
		self.lcpos = (-40, 20, 20)
		self.rcpos = (40, 20, 20)
		self.w = w
		self.h = h
		self.trg = None
		self.highlite_count = 0
		self.highlite_count_max = 16
		self.shooting = False
		self.fire = False
		self.shot_timer = 0

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
		if not self.shooting and not self.fire:
			return
		self.shooting = True
		i = self.shot_timer
		if i == 0:
			self._xm = self.cx + randint(-2, 2)
			self._ym = self.cy + randint(-2, 2)
			self.cp.shot_fired(self.trg)
		if i < 6:
			i0 = max(0, i - 1)
			x, y, z = self.lcpos
			self.g3d.line((x, y, z + i0*1000), (x, y, z + i*1000+1500))
			x += 10
			self.g3d.line((x, y, z + i0*1000), (x, y, z + i*1000+1500))
			x, y, z = self.rcpos
			self.g3d.line((x, y, z + i0*1000), (x, y, z + i*1000+1500))
			x -= 10
			self.g3d.line((x, y, z + i0*1000), (x, y, z + i*1000+1500))
		self.shot_timer += 1
		if self.shot_timer >= 20:
			self.shot_timer = 0
			if not self.fire:
				self.shooting = False

	def set_shooting(self, shooting):
		self.fire = shooting

class BaseScreen:
	def __init__(self, elite, cbg):
		self.cbg = cbg
		self.elite = elite
		self.universe = elite.universe
		self.width = 320
		self.height = 240
		self.hstatus = 64
		self.ystatus = self.height - self.hstatus - 1
		self.spaceclip = (4, 4, self.width - 4, self.ystatus - 4)

	def setup_screen(self):
		self.cbg.colorrect(0, 0, self.width, self.height, 11, 0)
		self.cbg.colorrect(2, 4, self.width-3, self.ystatus-4, 15, 0)

	def draw_background(self):
		self.cbg.rect(1, 2, self.width-2, self.height-4)

	def draw(self):
		pass

	def exit(self):
		pass

class MenuScreen(BaseScreen):
	TITLE = "Base Menu"
	def __init__(self, elite, cbg):
		super().__init__(elite, cbg)
		self.tx = self.width // 2 - len(self.TITLE) * 4

	def handle(self, inp):
		self.cbg.clearmap()
		self.draw_background()
		self.draw()
		return inp.get_new_keys(), True

	def draw_background(self):
		super().draw_background()
		self.cbg.line(1, 20, self.width-2, 20)
		self.cbg.drawtext(self.tx, 8, self.TITLE)

class Cockpit(BaseScreen):
	def __init__(self, elite, cbg, cd):
		super().__init__(elite, cbg)
		self.cd = cd
		self.sboxw = 64
		self.radarw = self.width-2*self.sboxw
		self.g3d = G3d(self.cbg, cx = self.width // 2, cy = self.ystatus // 2)
		self.bgnames = ["FS", "AS", "FV", "CT", "LT", "AL"]
		rbx = self.sboxw + self.radarw + 2
		self.battery = Battery(self.cbg, rbx, self.ystatus + 28, 40, 7)
		self.speedbar = BarGraph(self.cbg, rbx, self.ystatus + 4, 40, 7, 11, 0, ticks=8)
		self.rlmeter = Meter(self.cbg, rbx, self.ystatus + 12, 40, 7, 14, 0, ticks=8)
		self.dcmeter = Meter(self.cbg, rbx, self.ystatus + 20, 40, 7, 14, 0, ticks=8)
		self.laser = Laser(self, 0, 0, self.width, self.ystatus)
		self.m = Microverse(self.cbg, self.g3d, self.laser, self.elite.ships, cd, self.universe)
		self.radar = Radar(self.cbg, self, self.sboxw + 1, self.ystatus + 8, self.radarw - 2, self.hstatus - 10)
		self.setup_screen()

	def setup_screen(self):
		super().setup_screen()
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
		super().draw_background()
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

	def handle(self, inp):
		m = self.m
		nkeys = inp.get_new_keys()
		if m.dead: # If we die by AI coroutine...
			return nkeys, False
		roll = inp.get_roll() * 0.03
		pitch = inp.get_pitch() * 0.03
		speed = inp.get_throttle() * 15.0
		nbtns = inp.get_new_buttons()
		btns = inp.get_buttons()
		m.set_speed(speed)
		if nbtns:
			if BaseDev.BTN_JUMP in nbtns:
				m.jump()
			elif BaseDev.BTN_HYPERSPACE in nbtns:
				m.hyperspace()
			elif BaseDev.BTN_VIEW_FRONT in nbtns:
				m.set_view(m.VIEW_FRONT)
			elif BaseDev.BTN_VIEW_REAR in nbtns:
				m.set_view(m.VIEW_REAR)
			elif BaseDev.BTN_VIEW_RIGHT in nbtns:
				m.set_view(m.VIEW_RIGHT)
			elif BaseDev.BTN_VIEW_LEFT in nbtns:
				m.set_view(m.VIEW_LEFT)
		self.laser.set_shooting(BaseDev.BTN_FIRE in btns)
		ret = m.handle()
		self.speedbar.set_value(speed / 15)
		self.rlmeter.set_value(roll * 33)
		self.dcmeter.set_value(pitch * 33)
		self.battery.set_value(m.energy)
		self.bar_as.set_value(m.aft_shield)
		self.bar_fs.set_value(m.front_shield)
		self.cbg.clearmap()
		self.draw_background()
		m.set_roll_pitch(roll, pitch)
		self.cbg.setclip(self.spaceclip)
		m.draw()
		self.cbg.setclip(None)
		return nkeys, ret

	def handle_hidden(self):
		self.m.handle()

	def hyperspace(self):
		self.m.stop()
		self.m = Microverse(self.cbg, self.g3d, self.laser, self.elite.ships, self.cd, self.universe, hyperspace=True)

	def game_over_iteration(self):
		m = self.m
		ret = m.handle()
		self.cbg.clearmap()
		self.cbg.setclip(self.spaceclip)
		m.draw()
		self.cbg.setclip(None)
		return ret

	def shot_fired(self, target):
		self.m.shot_fired(target)

	async def launch_animation(self):
		cbg = self.cbg
		g3d = self.g3d
		circles = []
		for i in range(4):
			circles.append(i*12)
		for i in range(8):
			circles.append(i*30 + 50)
		for i in range(4):
			circles.append(i*12 + 290)
		cbg.setclip(self.spaceclip)
		xc, yc = g3d.project2d(0, 0, 1000)
		dz = 400
		acc = 1.0
		self.m.sfx.play_launch()
		while dz > 0:
			cbg.clearmap()
			for c in circles:
				z = dz - c
				if z < 4:
					continue
				r = g3d.project2d(10, 0, z * 2)[0]
				if not r:
					continue
				cbg.ellipse(xc, yc, int(r - xc), int(r - xc))
			cbg.redraw_screen()
			await asyncio.sleep(0.03)
			dz -= acc
			acc += 0.1
		cbg.setclip(None)

	async def hyperspace_animation_start(self):
		cbg = self.cbg
		m = Microverse(self.cbg, self.g3d, None, self.elite.ships, self.cd, self.universe, particles=0)
		m.sfx.play_hyperspace_start()
		cobs = []
		for i in range(5):
			cobs.append(m.spawn("cobra_mkiii", (0, 80, 800), 3.1415, 0.2))
		ang = deque([0], maxlen=5)
		pos = deque([0], maxlen=5)
		i = 0
		roll = 0.0
		alpha = 0.0
		pats = [0xffff, 0xaaaa, 0x9248, 0x8888, 0x8420]
		zp = 400
		cbg.setclip(self.spaceclip)
		while i < 80:
			if alpha < 6.28 and (20 < i < 70):
				roll += 0.01
			else:
				roll = 0.0
			if i > 60:
				pos.appendleft(i - 60)
			ang.appendleft(roll)
			cbg.clearmap()
			for t, c in enumerate(cobs):
				if t >= len(ang):
					continue
				if t < len(pos):
					y = pos[t]
				else:
					y = 0.0
				pitch = 0.01 if i < 20 else 0.0
				c.pos = (0, c.pos[1] - y*4, zp)
				c.local_roll_pitch(ang[t], pitch)
				c.draw(pats[t])
			cbg.redraw_screen()
			i += 1
			alpha += roll
			if zp < 800:
				zp += 10
			await asyncio.sleep(0.01)
		cbg.setclip(None)

	async def hyperspace_animation_end(self):
		cbg = self.cbg
		m = Microverse(self.cbg, self.g3d, None, self.elite.ships, self.cd, self.universe, particles=0)
		m.sfx.play_hyperspace_end()
		cobs = []
		for i in range(5):
			cobs.append(m.spawn("cobra_mkiii", (0, -500, 800), 3.1415, 0.5))
		pos = deque([-500], maxlen=5)
		i = 0
		pats = [0xffff, 0xaaaa, 0x9248, 0x8888, 0x8420]
		cbg.setclip(self.spaceclip)
		while i < 50:
			if i < 11:
				pos.appendleft(i * 10)
			elif i < 16:
				pos.appendleft(100 + (i - 10) * 5)
			elif i < 21:
				pos.appendleft(125)
			else:
				pos = [125]
			cbg.clearmap()
			for t, c in enumerate(cobs):
				if t >= len(pos):
					continue
				y = pos[t]
				pitch = 0.01 if i < 20 else 0.0
				c.pos = (c.pos[0], -100 + y, c.pos[2] - (0 if i < 17 else 10))
				c.local_roll_pitch(0.0, pitch)
				c.draw(pats[t])
			cbg.redraw_screen()
			i += 1
			await asyncio.sleep(0.01)
		cbg.setclip(None)

class GalaxyMap(MenuScreen):
	TITLE = "GALACTIC CHART"
	def __init__(self, elite, cbg, cd):
		super().__init__(elite, cbg)
		self.cd = cd
		self.galaxy = cd.galaxy

	def get_position(self, s):
		return s.x + 32, (s.y >> 1) + 32

	def draw(self):
		tsys = self.cd.system
		self.cbg.drawtext(self.width-32, 8, "{}/8".format(self.galaxy + 1))
		for i in range(256):
			s = self.universe.get_system_by_index(self.galaxy, i)
			self.cbg.putpixel(*self.get_position(s))
		s = self.universe.get_system_by_index(self.galaxy, tsys)
		r = int(self.cd.fuel * 5)
		self.cbg.ellipse(*self.get_position(s), r, r)

class ShortRangeMap(GalaxyMap):
	TITLE = "SHORT RANGE CHART"
	def __init__(self, elite, cbg, cd):
		super().__init__(elite, cbg, cd)
		self.system = cd.system
		s = self.universe.get_system_by_index(cd.galaxy, self.system)
		st = self.universe.get_system_by_index(cd.galaxy, cd.target)
		self.cx = s.x
		self.cy = s.y
		self.curx = st.x
		self.cury = st.y

	def _coord(self, x, y):
		x = int((x - self.cx) * 4 + 160)
		y = int((y - self.cy) * 2 + 100)
		return x, y

	def get_position(self, s):
		return self._coord(s.x, s.y)

	def handle(self, inp):
		dx = -inp.get_roll()
		dy = -inp.get_pitch()
		x, y = self._coord(self.curx + dx, self.cury + dy)
		if 64 < x < 256:
			self.curx += dx
		if 32 < y < 182:
			self.cury += dy
		return super().handle(inp)

	def exit(self):
		st = self.universe.get_system_near(self.cd.galaxy, self.curx, self.cury)
		if st:
			self.cd.target = st.index
		return super().exit()

	def draw(self):
		texty = set()
		for i in range(256):
			s = self.universe.get_system_by_index(self.galaxy, i)
			x, y = self.get_position(s)
			if 64 < x < 256 and 32 < y < 182:
				r = s.radius // 1024
				self.cbg.ellipse(x, y, r, r, fill=1)
				ty = (y) // 8
				if ty in texty:
					ty += 1
				texty.add(ty)
				self.cbg.drawtext(x + 4, ty * 8, s.name)
		s = self.universe.get_system_by_index(self.galaxy, self.system)
		r = int(self.cd.fuel * 20)
		x, y, = self.get_position(s)
		self.cbg.ellipse(x, y, r, r)
		self.cbg.line(x, y - 16, x, y + 16, mode=2)
		self.cbg.line(x - 16, y, x + 16, y, mode=2)
		curx, cury = self._coord(self.curx, self.cury)
		self.cbg.line(curx, cury - 8, curx, cury + 8, mode=2)
		self.cbg.line(curx - 8, cury, curx + 8, cury, mode=2)

class StatusScreen(MenuScreen):
	def __init__(self, elite, cbg, cd):
		self.TITLE = "COMMANDER "+cd.name.upper()
		super().__init__(elite, cbg)
		self.cd = cd
		self.statustext = ["Clean", "Offender", "Fugutive"]
		self.ranktext = ["Harmless", "Mostly Harmless", "Poor", "Average",
				"Above Average", "Competent", "Dangerous", "Deadly", "---- E L I T E ----"]
		self.lasertext = ["Pulse", "Mining", "Beam", "Military"]

	def draw(self):
		c = self.cbg
		cd = self.cd
		sy = self.universe.get_system_by_index(cd.galaxy, cd.system)
		tsy = self.universe.get_system_by_index(cd.galaxy, cd.target)
		c.drawtext(16, 32, "Present System      : {}".format(sy.name))
		c.drawtext(16, 40, "Hyperspace System   : {}".format(tsy.name))
		c.drawtext(16, 48, "Condition           : {}".format("Docked" if cd.docked else "Green"))
		c.drawtext(16, 56, "Fuel: {:.1f} Light Years".format(cd.fuel))
		c.drawtext(16, 64, "Cash: {:.6f} Bitcoin".format(cd.bitcoin))
		c.drawtext(16, 72, "Legal Status: {}".format(self.statustext[cd.status]))
		c.drawtext(16, 80, "Rating: {}".format(self.ranktext[cd.nrank]))
		c.drawtext(16, 96, "EQUIPMENT:")
		y = 104
		if cd.scoops:
			c.drawtext(56, y, "Fuel Scoops")
			y += 8
		if cd.ecm:
			c.drawtext(56, y, "E.C.M. System")
			y += 8
		if cd.ebomb:
			c.drawtext(56, y, "Energy Bomb")
			y += 8
		if cd.energy:
			c.drawtext(56, y, "Extra Energy Unit")
			y += 8
		if cd.docking:
			c.drawtext(56, y, "Docking Computers")
			y += 8
		if cd.gdrive:
			c.drawtext(56, y, "Galactic Hyperspace Drive")
			y += 8
		for d in ["Front", "Rear", "Left", "Right"]:
			l = getattr(cd, "laser_" + d.lower())
			if l is not None:
				c.drawtext(56, y, " ".join([d, self.lasertext[l], "Laser"]))
				y += 8

class SystemData(MenuScreen):
	def __init__(self, elite, cbg, cd):
		s = elite.universe.get_system_by_index(cd.galaxy, cd.target)
		self.TITLE = "DATA ON "+s.name.upper()
		super().__init__(elite, cbg)
		self.system = s

	def _txt_align(self, l, n):
		words = l.split()
		line = []
		x = 0
		for w in words:
			if line and x + len(w) > n:
				if len(line) == 1:
					yield line[0]
				else:
					d, m = divmod(n - x + 1, len(line) - 1)
					minsp = ' ' * (d + 1)
					if m:
						yield (' ' * (d + 2)).join(line[:m] + [minsp.join(line[m:])])
					else:
						yield minsp.join(line)
				x = 0
				line = []
			line.append(w)
			x += len(w) + 1
		if line:
			yield " ".join(line)

	def draw(self):
		c = self.cbg
		s = self.system
		txt = repr(s)
		lines = txt.split('\n')
		y = 32
		for l in lines:
			if len(l) <= 36:
				c.drawtext(16, y, l)
				y += 8
			else:
				xlines = self._txt_align(l, 36)
				for xl in xlines:
					c.drawtext(16, y, xl)
					y += 8
			y += 8 # Extra line between paragraphs.

class CommanderData:
	def __init__(self):
		self.data_version = 1
		self.name = "Jameson"
		self.bitcoin = 10.0
		self.kills = 0
		self.nrank = 0
		self.status = 0
		self.galaxy = 0
		self.system = 7 # Default start at Lave
		self.target = 7
		self.mission = None
		self.fuel = 7.0
		self.missiles = 0
		self.laser_front = 0
		self.laser_rear = None
		self.laser_left = None
		self.laser_right = None
		self.cargo_bay = False
		self.scoops = False
		self.ecm = False
		self.ebomb = False
		self.docking = False
		self.energy = False
		self.gdrive = False
		self.docked = True

class Commander:
	def __init__(self):
		self.data = CommanderData()
		self.fname = "~/.cbgeliterc"

	def load_game(self):
		try:
			with open(self.fname, "r") as f:
				txt = f.read()
		except OSError:
			return False
		try:
			obj = json.loads(txt)
		except json.JSONDecodeError:
			return False
		for item in obj:
			if hasattr(self.data, item):
				setattr(self.data, item, obj[item])
		return True

	def save_game(self):
		try:
			with open(self.fname, "w") as f:
				f.write(json.dumps(self.data, indent="\t"))
		except OSError:
			return False

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
		self.universe = Universe()
		self.commander = Commander()
		self.ships = AllShips("all_ships.ship").ships

	def draw_title(self):
		sw = 320
		tx = sw // 2 - 80
		self.cbg.drawtext(tx, 8, "---- E L I T E ----")
		tx = sw // 2 - 80
		self.cbg.drawtext(tx, 176 - 16, "Press ESC to start")

	async def title_screen(self, showfps=False):
		dz = 20050
		cockpit = Cockpit(self, self.cbg, self.commander.data)
		cockpit.setup_screen()
		tm = Microverse(self.cbg, cockpit.g3d, None, self.ships, self.commander.data, self.universe, particles=0)
		cobra = tm.spawn("cobra_mkiii", (0, 0, dz), 0.0, 0.0)
		if showfps:
			t0 = monotonic()
			fr = 0
			fps = 0.0
		ts = monotonic()
		i = 131
		while True:
			if i > 130:
				i = 0
				roll = uniform(-0.04, 0.04)
			i += 1
			if dz > 550:
				dz -= 150
				cobra.pos = (0.0, 0.0, dz)
			self.cbg.clearmap()
			cockpit.draw_background()
			self.draw_title()
			self.cbg.setclip(cockpit.spaceclip)
			cobra.local_roll_pitch(roll, -0.0513)
			tm.draw()
			self.cbg.setclip(None)
			self.cbg.redraw_screen()
			self.inputdev.handle()
			if 1 in self.inputdev.get_new_keys():
				break
			if showfps:
				print("\x1b[2;2HFPS:{:.2f}".format(fps))
			else:
				ts = await self.framesleep(ts)
				continue
			fr += 1
			if fr > 10:
				t = monotonic()
				fps = fr / (t - t0)
				t0 = t
				fr = 0
			await asyncio.sleep(0)

	async def framesleep(self, ts):
		now = self.loop.time()
		dt = max(0.0, ts + 0.04 - now)
		await asyncio.sleep(dt)
		return now

	async def microtest(self):
		cockpit = Cockpit(self, self.cbg, self.commander.data)
		cockpit.setup_screen()
		m = cockpit.m
		cobra = m.spawn("cobra_mkiii", (-500, 0, 10000), 0.0, 0.0)
		cobra.add_ai(BaseAi)
		viper = m.spawn("krait",       (1500, 0, 5000), -0.5, 2.0)
		viper.add_ai(BaseAi)
		trans = m.spawn("transporter", (0, 1500, 5000), -0.5, 2.0)
		fdl = m.spawn("fer-de-lance",  (0, -1500, 5000), -0.5, 2.0)
		fdl.add_ai(BaseAi)
		mam = m.spawn("mamba",  (1000, 4000, 3000), 0.5, 2.0)
		mam.add_ai(BaseAi)
		boa = m.spawn("boa",  (-1000, 3000, 3000), 0.5, 2.0)
		boa.add_ai(BaseAi)
		asteroid0 = m.spawn("asteroid", (1500, -1500, -5000), -0.1, 1.0)
		asteroid1 = m.spawn("asteroid", (-1500, 1500, -5000), 0.1, -1.0)
		ts = monotonic()
		inp = self.inputdev
		while True:
			nkey, ret = cockpit.handle(inp)
			if not ret:
				break
			self.cbg.redraw_screen()
			ts = await self.framesleep(ts)
		if m.dead:
			while True:
				cockpit.game_over_iteration()
				self.cbg.redraw_screen()
				ts = await self.framesleep(ts)
		elif self.commander.data.docked:
			await cockpit.launch_animation()

	async def menu(self):
		cd = self.commander.data
		m = StatusScreen(self, self.cbg, cd)
		m.setup_screen()
		inp = self.inputdev
		ts = self.loop.time()
		cd.docked = True
		cockpit = None
		while True:
			inp.handle()
			nkey, ret = m.handle(inp)
			if cockpit and m is not cockpit:
				cockpit.handle_hidden()
			if not ret:
				if cd.docked: # Docking
					await m.launch_animation()
					m.exit()
					m = StatusScreen(self, self.cbg, cd)
					cockpit = None
				elif m.m.dead:
					for i in range(500):
						inp.handle()
						if 1 in inp.get_new_keys():
							break
						cockpit.game_over_iteration()
						self.cbg.redraw_screen()
						ts = await self.framesleep(ts)
					self.commander = Commander()
					cd = self.commander.data
					m.exit()
					m = StatusScreen(self, self.cbg, cd)
					cockpit = None
				elif m.m.hyperspacing:
					await m.hyperspace_animation_start()
					await asyncio.sleep(1)
					await m.hyperspace_animation_end()
					cd.system = cd.target
					m.hyperspace()
			self.cbg.redraw_screen()
			if 6 in nkey:
				m.exit()
				m = GalaxyMap(self, self.cbg, cd)
			elif 7 in nkey:
				m.exit()
				m = ShortRangeMap(self, self.cbg, cd)
			elif 8 in nkey:
				m.exit()
				m = SystemData(self, self.cbg, cd)
			elif 10 in nkey:
				m.exit()
				m = StatusScreen(self, self.cbg, cd)
			elif 2 in nkey: # FIXME: launch
				m.exit()
				if cd.docked:
					m = cockpit = Cockpit(self, self.cbg, cd)
					await m.launch_animation()
				else:
					m = cockpit
			ts = await self.framesleep(ts)

	async def startup(self, showfps=False):
		mt = self.loop.create_task(self.run(showfps))
		mt.add_done_callback(lambda fut: self.cbg.exit(fut.result()))

	async def run(self, showfps=False):
		await self.title_screen(showfps)
		await self.menu()
		#await self.cockpit.launch_animation()
		#await self.cockpit.hyperspace_animation_start()
		#await asyncio.sleep(1)
		#await self.cockpit.hyperspace_animation_end()
		await self.microtest()
		return 0

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	showfps = ("-fps" in sys.argv)
	config = ("-config" in sys.argv)
	e = Elite(config=config)
	loop.run_until_complete(e.startup(showfps=showfps))
	loop.run_forever()
