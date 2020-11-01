#!/usr/bin/env python3

import os
from time import sleep
from math import sin, cos, sqrt
from collections import deque
import sys

from ship import ShipReader

class CBG:
	def __init__(self):
		self.charcodes = [chr(x) for x in range(0x2800, 0x2900)]
		self.bitmasks = ((1, 8), (2, 16), (4, 32), (64, 128))
		self.cheight, self.cwidth = (int(x) for x in os.popen('stty size', 'r').read().split())
		self.width = self.cwidth * 2
		self.height = self.cheight * 4
		self.curx = 5
		self.cury = 5
		self.putcursor(0, 0)
		self.clear()

	def clear(self):
		size = self.cwidth * self.cheight
		self.map = bytearray(b'\x00' * size)
		self.redraw_screen()

	def putcursor(self, x, y):
		if self.cury == y and  self.curx == x:
			return
		print("\x1b[{};{}H".format(x+1, y+1), end='')
		self.curx = x
		self.cury = y

	def puchar(self, x, y, char):
		if x == self.curx and y == self.cury:
			print(char, end='')
			self.curx += len(char)
			return
		print("\x1b[{};{}H{}".format(x+1, y+1, char), end='')
		self.curx = x + len(char)
		self.cury = y

	def putpixel(self, x, y, clear=False):
		if x >= self.width or y >=self.height or x < 0 or y < 0:
			return
		cpx = x >> 1
		cpy = y >> 2
		bmp = self.bitmasks[y & 3][x & 1]
		cmd = "\x1b[{};{}H".format(cpy, cpx)
		idx = cpx + cpy * self.cwidth
		b = self.map[idx]
		if clear:
			b &= ~bmp
		else:
			b |= bmp
		u = chr(0x2800+b)
		self.map[idx] = b
		print(cmd + u, end='')

	def redraw_screen(self):
		for y in range(self.cheight):
			print("\x1b[{};1H".format(y), end='')
			for x in range(self.cwidth):
				b = self.map[y * self.cwidth + x]
				if b:
					u = chr(0x2800 + b)
				else:
					u = ' '
				print(u, end='')

	def line(self, x0, y0, x1, y1, clear=False):
		dx = abs(x1 - x0)
		sx = 1 if (x0 < x1) else -1
		dy = -abs(y1 - y0)
		sy = 1 if (y0 < y1) else -1
		err = dx + dy
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
		sys.stdout.flush()

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
	def __init__(self, cbg):
		self.cbg = cbg
		self.width = cbg.width
		self.height = cbg.height
		self.persp = 400.0
		self.cdist = 400.0
		self.cx = self.width / 2
		self.cy = self.height / 2
		self.rmat = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
		self.tvec = (0.0, 0.0, 0.0)
		self.rotc = (0.0, 0.0, 0.0)

	def project2d(self, x, y, z):
		if z <= -self.cdist:
			return None, None
		z += self.cdist
		x = self.persp * x / z
		y = self.persp * y / z
		return x + self.cx, y + self.cy

	def point(self, p, clear=False):
		x, y = self.project2d(*p)
		if x is not None:
			self.cbg.putpixel(x, y, clear)

	def line(self, p0, p1, clear=False):
		x0, y0 = self.project2d(*p0)
		if x0 is None:
			return
		x1, y1 = self.project2d(*p1)
		if x1 is None:
			return
		self.cbg.line(int(x0), int(y0), int(x1), int(y1), clear)

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

	def spinship(self, s):
		rx = 0.0
		ry = 0.0
		rz = 0.0
		dz = 0
		while True:
			self.setRotMat(rx, ry, rz)
			self.setTranslation((0, 0, dz))
			self.cbg.clear()
			self.draw_ship(s)
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
			self.cbg.clear()
			self.cube(120, 120, 120)
			self.setRotMat(rz, rx, ry, (70, 0, 0))
			self.setTranslation((-50, 50, 50))
			self.cube(60, 60, 60)
			ry += 0.1
			rz += 0.03
			sleep(0.04)

def main():
	c = CBG()
	#c.liney()
	d = G3d(c)
	#d.spincube()
	d.spinship(ShipReader("cobra_mk3.ship"))
	c.end()

if __name__ == "__main__":
	main()
