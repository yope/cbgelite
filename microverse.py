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

from cbg import CBG, G3d
from ship import ShipReader
import random
from time import monotonic
from math import sqrt, pi
from quaternion import *
from time import sleep

random.seed(monotonic())

class Object3D:
	def __init__(self, mv, pos, ship, name):
		self.debug = False
		self.alive = True
		self.ai = None
		self.name = name.replace("_", " ").upper()
		self.mv = mv
		self.g3d = mv.g3d
		self.pos = pos
		self.ship = ship
		self.nosev = (0, 0, 1)
		self.sidev = (0, 1, 0)
		self.roofv = (1, 0, 0)
		self.roll = 0.0
		self.pitch = 0.0
		self.qwroll = aangle2q((0, 0, 1), 0.0)
		self.qwpitch = aangle2q((1, 0, 0), 0.0)
		self.qwtot = qmult(self.qwpitch, self.qwroll)
		self.qltot = qmult(self.qwpitch, self.qwroll)
		self.local_roll_pitch(0.0, 0.0)
		self.world_roll_pitch(0.0, 0.0)

	def add_ai(self, AiCls):
		self.ai = AiCls(self)

	def handle(self):
		if self.ai:
			self.ai.handle()

	def local_roll_pitch(self, roll, pitch):
		self.roll += roll
		self.pitch += pitch
		pi2 = pi * 2
		if self.roll > pi2:
			self.roll -= pi2
		elif self.roll < 0.0:
			self.roll += pi2
		if self.pitch > pi2:
			self.pitch -= pi2
		elif self.pitch < 0.0:
			self.pitch += pi2
		qroll = aangle2q((0, 0, 1), self.roll)
		qpitch = aangle2q((1, 0, 0), self.pitch)
		self.qltot = qmult(qpitch, qroll)
		self.qlcon = qconj(self.qltot)

	def world_roll_pitch(self, roll, pitch):
		self.qwroll = aangle2q((0, 0, 1), roll)
		self.qwpitch = aangle2q((1, 0, 0), pitch)
		self.qwtot = qmult(qmult(self.qwpitch, self.qwroll), self.qwtot)
		self.qwcon = qconj(self.qwtot)
		self.nosev = normalize(self._qrot((0, 0, 1)))
		self.sidev = normalize(self._qrot((0, 1, 0)))
		self.roofv = normalize(self._qrot((1, 0, 0)))

	def _qlrot(self, p):
		return qmult(qmult(self.qltot, (0.0, ) + p), self.qlcon)[1:]

	def _qwrot(self, p):
		return qmult(qmult(self.qwtot, (0.0, ) + p), self.qwcon)[1:]

	def _qrot(self, p):
		return self._qwrot(self._qlrot(p))

	def scale_add(self, p, q, n):
		return p[0] * n + q[0], p[1] * n + q[1], p[2] * n + q[2]

	def transform(self, p):
		p = self._qrot(p)
		x, y, z = self.pos
		return (p[0] + x, p[1] + y, p[2] + z)

	def normrotate(self, p):
		return self._qrot(p)

	def get_viewpos(self):
		return self.pos

	def in_view(self):
		vp = self.g3d.normalize(self.pos)
		return not (-0.7 < self.g3d.dot(vp, (0, 0, 1)) < 0.7)

	def on_target(self):
		x, y, x = self.pos
		r = self.ship.opt_target_area
		if (x + r) > 0 and (x - r) < 0 and (y + r) > 0 and (y - r) < 0:
			return True
		else:
			return False

	def draw(self):
		s = self.ship
		g = self.g3d

		if self.debug:
			# Draw local coordinate system
			g.line(self.pos, self.scale_add(self.nosev, self.pos, 300))
			g.line(self.pos, self.scale_add(self.sidev, self.pos, 300))
			g.line(self.pos, self.scale_add(self.roofv, self.pos, 300))

		for f in s.face:
			fe = s.face[f]
			n = self.normrotate(s.norm[f])
			p0 = self.transform(s.vert[s.edge[fe[0]][0]])
			vcop = g.normalize((p0[0], p0[1], p0[2] + g.persp))
			dp = g.dot(vcop, n)
			if dp > 0:
				continue
			vangle = g.dot(vcop, (0, 0, 1))
			if -0.7 < vangle < 0.7:
				continue
			for ei in fe:
				e = s.edge[ei]
				p0 = self.transform(s.vert[e[0]])
				p1 = self.transform(s.vert[e[1]])
				g.line(p0, p1)

class Particle:
	def __init__(self, mv):
		self.mv = mv
		self.g3d = mv.g3d
		self.rad = 250
		self.maxdist = self.rad
		self.mindist = 50
		self.pos = (
			random.uniform(-self.rad, self.rad),
			random.uniform(-self.rad, self.rad),
			random.uniform(1, self.maxdist)
		)

	def reset(self):
		self.pos = (random.uniform(-self.rad, self.rad), random.uniform(-self.rad, self.rad), random.uniform(self.mindist, self.maxdist))

	def distance(self):
		return sqrt(sum((n*n for n in self.pos)))

	def draw(self):
		self.g3d.point(self.pos)
		if self.distance() > self.maxdist:
			self.reset()

class Microverse:
	def __init__(self, cbg, g3d, laser, ships, particles=400):
		self.g3d = g3d
		self.cbg = cbg
		self.ships = ships
		self.laser = laser
		self.objects = []
		self.particles = set()
		for i in range(particles):
			self.particles.add(Particle(self))
		self.roll = 0.0
		self.pitch = 0.0
		self.set_roll_pitch(0.0, 0.0)
		self.flashtext = ""
		self.flashtout = 0

	def handle(self):
		for o in self.objects:
			o.handle()

	def get_objects(self):
		return self.objects

	def set_roll_pitch(self, roll, pitch):
		self.roll += roll
		self.pitch += pitch
		self.g3d.setRotQ(pitch, 0.0, roll)
		for o in self.objects:
			o.pos = self.g3d.rotate_q(o.pos)
			o.world_roll_pitch(roll, pitch)
		for o in self.particles:
			o.pos = self.g3d.rotate_q(o.pos)

	def spawn(self, name, pos, roll, pitch):
		s = self.ships[name]
		obj = Object3D(self, pos, s, name)
		obj.local_roll_pitch(roll, pitch)
		self.objects.append(obj)
		return obj

	def set_flashtext(self, s):
		self.flashtext = s
		self.flashtout = 50

	def draw(self):
		for o in self.objects:
			o.draw()
		for p in self.particles:
			p.draw()
		if self.flashtout:
			slen = len(self.flashtext) * 8
			x = (320 - slen) // 2
			self.cbg.drawtext(x, 16, self.flashtext)
			self.flashtout -= 1

	def move(self, dz):
		for o in self.objects:
			x, y, z = o.pos
			o.pos = (x, y, z - dz)
		for o in self.particles:
			x, y, z = o.pos
			o.pos = (x, y, z - dz)
