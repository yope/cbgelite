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

import os
from time import sleep
from math import sin, cos, sqrt
from collections import deque
import sys
import signal
import termios
import traceback

from ship import ShipReader
from text import FontData
from quaternion import *

class CBG:
	def __init__(self):
		self.charcodes = [chr(x) for x in range(0x2800, 0x2900)]
		self.charcodes[0] = ' ' # Replace 0 with space. This is faster in some cases.
		self.bitmasks = ((1, 8), (2, 16), (4, 32), (64, 128))
		self.cheight, self.cwidth = (int(x) for x in os.popen('stty size', 'r').read().split())
		self.curx = 5
		self.cury = 5
		self.putcursor(0, 0)
		self.set_log_area(max(0, self.cheight-60))
		self.width = self.cwidth * 2
		self.height = self.cheight * 4
		self.setclip()
		self.clearcolormap()
		self.clearscreen()
		print("\x1b[2J", end="")
		self.font = FontData("chargen.rom")
		self.font.optimize(self.bitmasks)
		self.orig_sigint = signal.getsignal(signal.SIGINT)
		signal.signal(signal.SIGINT, self.handle_sigint)
		self.disable_cursor()
		self.disable_echo()

	def set_log_area(self, h):
		self.cheight -= h
		self.log_l0 = self.cheight
		self.log_h = h
		if h > 0:
			self.logbuf = deque(maxlen=h)
		for i in range(h):
			self.log(" ")

	def log(self, *args):
		if not self.log_h:
			return
		s = " ".join(str(a) for a in args)
		s = s.ljust(self.cwidth-1, " ")
		self.logbuf.append(s)
		for i, l in enumerate(self.logbuf):
			self.putcursor(0, self.log_l0 + i)
			print(l, end='')

	def enable_cursor(self):
		print("\x1b[?25h", end='')

	def disable_cursor(self):
		print("\x1b[?25l", end='')

	def disable_echo(self):
		fd = sys.stdin.fileno() # Well.. this is 0, right?
		flags = termios.tcgetattr(fd)
		flags[3] &= ~termios.ECHO
		termios.tcsetattr(fd, termios.TCSANOW, flags)

	def enable_echo(self):
		fd = sys.stdin.fileno()
		flags = termios.tcgetattr(fd)
		flags[3] |= termios.ECHO
		termios.tcsetattr(fd, termios.TCSANOW, flags)

	def exit(self, retcode):
		self.enable_cursor()
		self.enable_echo()
		self.putcursor(0, self.cheight+self.log_h-1)
		print("\x1b[0m")
		print("Screen size: {}x{}".format(self.width, self.height))
		print("Screen Char size: {}x{}".format(self.cwidth, self.cheight))
		sys.exit(retcode)

	def handle_sigint(self, sig, frm):
		signal.signal(signal.SIGINT, self.orig_sigint)
		self.cury = 0
		self.putcursor(0, self.cheight+self.log_h-1)
		print("\nBacktrace:")
		traceback.print_stack()
		self.exit(1)

	def setclip(self, cr=None):
		if not cr:
			self.clxmin = 0
			self.clymin = 0
			self.clxmax = self.width
			self.clymax = self.height
		else:
			self.clxmin = cr[0]
			self.clymin = cr[1]
			self.clxmax = cr[2]
			self.clymax = cr[3]

	def clearmap(self):
		size = self.cwidth * self.cheight
		self.map = bytearray(b'\x00' * size)

	def clearcolormap(self):
		size = self.cwidth * self.cheight
		self.colormap = bytearray(b'\x0f' * size)

	def clearscreen(self):
		self.clearmap()
		self.redraw_screen()

	def putcursor(self, x, y):
		if self.cury == y and  self.curx == x:
			return
		print("\x1b[{};{}H".format(int(y)+1, int(x)+1), end='')
		self.curx = x
		self.cury = y

	def putcode(self, x, y, code):
		self.map[x + y * self.cwidth] = code

	def putpixel(self, x, y, clear=False):
		if x < self.clxmin or x > self.clxmax or y < self.clymin or y > self.clymax:
			return
		cpx = x >> 1
		cpy = y >> 2
		bmp = self.bitmasks[y & 3][x & 1]
		idx = cpx + cpy * self.cwidth
		b = self.map[idx]
		if clear:
			b &= ~bmp
		else:
			b |= bmp
		self.map[idx] = b

	def drawglyph(self, x, y, char):
		data = self.font.getchar(char)
		x = int(x / 2)
		y = int(y / 4)
		for r in range(2):
			for c in range(4):
				self.putcode(x + c, y + r, data[r*4+c])

	def drawtext(self, x, y, s, fg=None, bg=None):
		for c in s:
			self.drawglyph(x, y, c)
			if fg or bg:
				self.colorrect(x, y, 8, 8, fg, bg)
			x += 8

	def colorrect(self, x, y, w, h, fg, bg):
		x = int(x / 2)
		y = int(y / 4)
		w = int(w / 2)
		h = int(h / 4)
		msk = 0
		if fg is None:
			fg = 0
			msk |= 0x0f
		if bg is None:
			bg = 0
			msk |= 0xf0
		c = (bg << 4) | fg
		if msk:
			for i in range(y, y+h):
				idx = i * self.cwidth
				for j in range(x, x+w):
					self.colormap[idx + j] &= msk
					self.colormap[idx + j] |= c
		else:
			for i in range(y, y+h):
				idx = i * self.cwidth
				for j in range(x, x+w):
					self.colormap[idx + j] = c

	def redraw_screen(self):
		fg0 = 16
		bg0 = 16
		curc = 256
		for y in range(self.cheight):
			print("\x1b[{};1H".format(y+1), end='')
			for x in range(self.cwidth):
				idx = y * self.cwidth + x
				b = self.map[idx]
				c = self.colormap[idx]
				if curc != c:
					fg = c & 0x0f
					curc = c
					if fg0 != fg:
						fg0 = fg
						print("\x1b[38;5;{}m".format(fg), end='')
					bg = c >> 4
					if bg0 != bg:
						bg0 = bg
						print("\x1b[48;5;{}m".format(bg), end='')
				u = self.charcodes[b]
				print(u, end='')
		sys.stdout.flush()

	def line(self, x0, y0, x1, y1, clear=False, pattern=None):
		dx = abs(x1 - x0)
		sx = 1 if (x0 < x1) else -1
		dy = -abs(y1 - y0)
		sy = 1 if (y0 < y1) else -1
		err = dx + dy
		if pattern:
			i = 0
			while True:
				if pattern & (1 << i):
					self.putpixel(x0, y0, clear)
				if (x0 == x1) and (y0 == y1):
					break
				i = (i+1) & 0x0f
				e2 = 2 * err
				if e2 >= dy:
					err += dy
					x0 += sx
				if e2 <= dx:
					err += dx
					y0 += sy
		else:
			while True:
				self.putpixel(x0, y0, clear)
				if (x0 == x1) and (y0 == y1):
					break
				e2 = 2 * err
				if e2 >= dy:
					err += dy
					x0 += sx
				if e2 <= dx:
					err += dx
					y0 += sy

	def clipped_line(self, x0, y0, x1, y1, clear=False, pattern=None):
		# Basic check to see if any part of the line is visible
		if x0 < self.clxmin and x1 < self.clxmin:
			return
		if x0 > self.clxmax and x1 > self.clxmax:
			return
		if y0 < self.clymin and y1 < self.clymin:
			return
		if y0 > self.clymax and y1 > self.clymax:
			return

		# FIXME: Now we could do intersection checks to optimize the line drawing
		# further, but this is already quite good, so let's just draw it.
		self.line(x0, y0, x1, y1, clear=clear, pattern=pattern)

	def rect(self, x, y, w, h, clear=False):
		self.line(x, y, x+w, y, clear)
		self.line(x, y, x, y+h, clear)
		self.line(x, y+h, x+w, y+h, clear)
		self.line(x+w, y, x+w, y+h, clear)

	def ellipse(self, x, y, a, b, clear=False, fill=False):
		x0 = x - a // 2
		x1 = x + a // 2
		y0 = y - b // 2
		y1 = y + b // 2
		b1 = b & 1
		dx = 4*(1-a)*b*b
		dy = 4*(b1+1)*a*a
		err = dx+dy+b1*a*a
		y0 += (b+1)/2
		y1 = y0-b1
		a *= 8*a
		b1 = 8*b*b
		if fill:
			while True:
				self.line(int(x0), int(y0), int(x1), int(y0), clear)
				self.line(int(x0), int(y1), int(x1), int(y1), clear)
				e2 = 2 * err
				if e2 <= dy:
					y0 += 1
					y1 -= 1
					dy += a
					err += dy
				if e2 >= dx or 2*err > dy:
					x0 += 1
					x1 -= 1
					dx += b1
					err += dx
				if x0 > x1:
					break
		else:
			while True:
				self.putpixel(int(x1), int(y0), clear)
				self.putpixel(int(x0), int(y0), clear)
				self.putpixel(int(x0), int(y1), clear)
				self.putpixel(int(x1), int(y1), clear)
				e2 = 2 * err
				if e2 <= dy:
					y0 += 1
					y1 -= 1
					dy += a
					err += dy
				if e2 >= dx or 2*err > dy:
					x0 += 1
					x1 -= 1
					dx += b1
					err += dx
				if x0 > x1:
					break

		while y0-y1 < b:
			self.putpixel(x0-1, y0)
			self.putpixel(x1+1, y0)
			y0 += 1
			self.putpixel(x0-1, y1)
			self.putpixel(x1+1, y1)
			y1 -= 1

	def fillrect(self, x, y, w, h, clear=False):
		# FIXME: Optimize this.
		for i in range(y, y+h):
			for j in range(x, x+w):
				self.putpixel(j, i, clear)

	def end(self):
		print("\x1b[{};{}H".format(self.cheight - 3, 0))

	def liney(self):
		lines = deque(maxlen=40)
		xa = self.width / 2
		xoff = self.width / 2
		ya = self.height / 2
		yoff = self.height / 2
		t = 0
		while True:
			if lines:
				x0, y0, x1, y1 = lines[0]
				self.line(x0, y0, x1, y1, True)
			x0 = int(xoff + xa * sin(0.077 * t))
			x1 = int(xoff + xa * cos(0.037 * t))
			y0 = int(yoff + ya * sin(0.079 * t))
			y1 = int(yoff + ya * cos(0.101 * t))
			lines.append((x0, y0, x1, y1))
			self.line(x0, y0, x1, y1)
			t += 1
			sleep(0.02)

class G3d:
	def __init__(self, cbg, cx=None, cy=None):
		self.cbg = cbg
		self.width = cbg.width
		self.height = cbg.height
		self.persp = 400.0
		self.cx = cx or self.width / 2
		self.cy = cy or self.height / 2
		self.rmat = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
		self.tvec = (0.0, 0.0, 0.0)
		self.rotc = (0.0, 0.0, 0.0)

	def project2d(self, x, y, z):
		if z <= 0:
			return None, None
		x = self.persp * x / z
		y = self.persp * y / z
		return x + self.cx, y + self.cy

	def point(self, p, clear=False):
		x, y = self.project2d(*p)
		if x is not None:
			self.cbg.putpixel(int(x), int(y), clear)

	def line(self, p0, p1, clear=False):
		x0, y0 = self.project2d(*p0)
		if x0 is None:
			return
		x1, y1 = self.project2d(*p1)
		if x1 is None:
			return
		self.cbg.clipped_line(int(x0), int(y0), int(x1), int(y1), clear)

	def setRotMat(self, rx, ry, rz, rotc=None):
		if rotc is None:
			self.rotc = (0, 0, 0)
		else:
			self.rotc = rotc
		sx = sin(rx)
		cx = cos(rx)
		sy = sin(ry)
		cy = cos(ry)
		sz = sin(rz)
		cz = cos(rz)
		self.rmat = (sx, cx, sy, cy, sz, cz)
		return self.rmat

	def setTranslation(self, p):
		self.tvec = p

	def rotate(self, p, cp=None):
		if cp is None:
			cp = self.rotc
		x = p[0] - cp[0]
		y = p[1] - cp[1]
		z = p[2] - cp[2]
		sx, cx, sy, cy, sz, cz = self.rmat
		dx = cy*(sz*y + cz*x) - sy*z
		dy = sx*(cy*z + sy*(sz*y + cz*x)) + cx*(cz*y - sz*x)
		dz = cx*(cy*z + sy*(sz*y + cz*x)) - sx*(cz*y - sz*x)
		return (dx + cp[0], dy + cp[1], dz + cp[2])

	def translate(self, p):
		return (p[0] + self.tvec[0], p[1] + self.tvec[1], p[2] + self.tvec[2])

	def normal(self, p0, p1, p2):
		v0 = (p0[0] - p1[0], p0[1] - p1[1], p0[2] - p1[2])
		v1 = (p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2])
		n = (v0[1]*v1[2] - v0[2]*v1[1], v0[2]*v1[0] - v0[0]*v1[2], v0[0]*v1[1] - v0[1]*v1[0])
		return n

	def add(self, p0, p1):
		return p0[0] + p1[0], p0[1] + p1[1], p0[2] + p1[2]

	def sub(self, p0, p1):
		return p0[0] - p1[0], p0[1] - p1[1], p0[2] - p1[2]

	def distv(self, v):
		return sqrt(v[0]**2 + v[1]**2 + v[2]**2)

	def normalize(self, v):
		vlen = self.distv(v)
		return (v[0]/vlen, v[1]/vlen, v[2]/vlen)

	def dot(self, v0, v1):
		return v0[0]*v1[0] + v0[1]*v1[1] + v0[2]*v1[2]

	def backface(self, p0, p1, p2):
		vcop = self.normalize((p0[0], p0[1], p0[2] + self.persp))
		dp = self.dot(vcop, self.normal(p0, p1, p2))
		return (dp > 0)

	def setRotQ(self, rx, ry, rz):
		q1 = aangle2q((1, 0, 0), rx)
		q2 = aangle2q((0, 1, 0), ry)
		q3 = aangle2q((0, 0, 1), rz)
		self.qtot = qmult(q1, qmult(q2, q3))
		self.qcon = qconj(self.qtot)

	def rotate_q(self, p):
		qp = (0.0,) + p
		return qmult(qmult(self.qtot, qp), self.qcon)[1:]

	def cube(self, w, h, d):
		x = w / 2
		y = h / 2
		z = d / 2
		vert = [
			(-x, -y, -z),
			(x, -y, -z),
			(x, y, -z),
			(-x, y, -z),
			(-x, -y, z),
			(x, -y, z),
			(x, y, z),
			(-x, y, z)
		]
		faces = [
			(0, 3, 2, 1),
			(1, 2, 6, 5),
			(1, 5, 4, 0),
			(5, 6, 7, 4),
			(0, 4, 7, 3),
			(3, 7, 6, 2)
		]
		for f in faces:
			p = [vert[x] for x in f]
			p = [self.translate(self.rotate(x)) for x in p]
			if self.backface(p[0], p[1], p[2]):
				continue
			self.line(p[0], p[1])
			self.line(p[1], p[2])
			self.line(p[2], p[3])
			self.line(p[3], p[0])

	def draw_ship(self, s):
		for f in s.face:
			fe = s.face[f]
			n = self.rotate(s.norm[f])
			p0 = self.translate(self.rotate(s.vert[s.edge[fe[0]][0]]))
			vcop = self.normalize((p0[0], p0[1], p0[2] + self.persp ))
			dp = self.dot(vcop, n)
			if dp > 0:
				continue
			for ei in fe:
				e = s.edge[ei]
				p0 = self.translate(self.rotate(s.vert[e[0]]))
				p1 = self.translate(self.rotate(s.vert[e[1]]))
				self.line(p0, p1)

	def draw_ship_q(self, s):
		for f in s.face:
			fe = s.face[f]
			n = self.rotate_q(s.norm[f])
			p0 = self.translate(self.rotate_q(s.vert[s.edge[fe[0]][0]]))
			vcop = self.normalize((p0[0], p0[1], p0[2] + self.persp ))
			dp = self.dot(vcop, n)
			if dp > 0:
				continue
			for ei in fe:
				e = s.edge[ei]
				p0 = self.translate(self.rotate_q(s.vert[e[0]]))
				p1 = self.translate(self.rotate_q(s.vert[e[1]]))
				self.line(p0, p1)

	def draw_background(self):
		sh = self.cbg.height
		sw = self.cbg.width
		self.cbg.rect(0, 0, sw-2, sh-9)
		self.cbg.line(0, 3 * sh // 4, sw-2, 3 * sh // 4)
		tx = sw // 2 - 80
		self.cbg.drawtext(tx, 8, "---- E L I T E ----")
		tx = sw // 2 - 80
		self.cbg.drawtext(tx, (3 * sh // 4) - 16, "Commander Jameson")

	def spinship(self, s):
		rx = 0.0
		ry = 0.0
		rz = 0.0
		dz = 150
		while True:
			self.setRotMat(rx, ry, rz)
			self.setTranslation((0, 0, dz))
			self.cbg.clearmap()
			self.draw_background()
			self.draw_ship(s)
			self.cbg.redraw_screen()
			ry += 0.1
			rz += 0.03
			sleep(0.04)

	def spincube(self):
		rx = 0.0
		ry = 0.0
		rz = 0.0
		while True:
			self.setRotMat(rx, ry, rz)
			self.setTranslation((0, 0, 1000))
			self.cbg.clearmap()
			self.cube(120, 120, 120)
			self.setRotMat(rz, rx, ry, (70, 0, 0))
			self.setTranslation((-50, 50, 50))
			self.cube(60, 60, 60)
			self.redraw_screen()
			ry += 0.1
			rz += 0.03
			sleep(0.04)

def main():
	c = CBG()
	#c.liney()
	d = G3d(c, cy=c.height / 2 - 40)
	#d.spincube()
	d.spinship(ShipReader("cobra_mk3.ship"))
	c.end()

if __name__ == "__main__":
	main()
