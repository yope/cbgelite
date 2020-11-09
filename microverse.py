
from cbg import CBG, G3d
from ship import ShipReader
import random
from time import monotonic
from math import sqrt, pi
from quaternion import *
from time import sleep

random.seed(monotonic())

class Object3D:
	def __init__(self, mv, pos, ship):
		self.debug = False
		self.mv = mv
		self.g3d = mv.g3d
		self.pos = pos
		self.ship = ship
		self.nosev = (0, 0, 1)
		self.sidev = (1, 0, 0)
		self.roofv = (0, 1, 0)
		self.roll = 0.0
		self.pitch = 0.0
		self.qwroll = aangle2q((0, 0, 1), 0.0)
		self.qwpitch = aangle2q((1, 0, 0), 0.0)
		self.qwtot = qmult(self.qwpitch, self.qwroll)
		self.qltot = qmult(self.qwpitch, self.qwroll)
		self.local_roll_pitch(0.0, 0.0)
		self.world_roll_pitch(0.0, 0.0)

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
		self.sidev = normalize(self._qrot((1, 0, 0)))
		self.roofv = normalize(self._qrot((0, 1, 0)))

	def _qlrot(self, p):
		return qmult(qmult(self.qltot, (0.0, ) + p), self.qlcon)[1:]

	def _qwrot(self, p):
		return qmult(qmult(self.qwtot, (0.0, ) + p), self.qwcon)[1:]

	def _qrot(self, p):
		return self._qwrot(self._qlrot(p))

	def _scale_add(self, p, q, n):
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

	def draw(self):
		s = self.ship
		g = self.g3d

		if self.debug:
			# Draw local coordinate system
			g.line(self.pos, self._scale_add(self.nosev, self.pos, 300))
			g.line(self.pos, self._scale_add(self.sidev, self.pos, 300))
			g.line(self.pos, self._scale_add(self.roofv, self.pos, 300))

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
	def __init__(self, mv, init=False):
		self.mv = mv
		self.g3d = mv.g3d
		if init:
			self.pos = (
				random.uniform(-15, 15),
				random.uniform(-15, 15),
				random.uniform(1, 250)
			)
		else:
			self.reset()

	def reset(self):
		self.pos = (random.uniform(-15, 15), random.uniform(-15, 15), random.uniform(50.0, 250.0))

	def distance(self):
		return sqrt(sum((n*n for n in self.pos)))

	def draw(self):
		self.g3d.point(self.pos)

class Microverse:
	def __init__(self, cbg, g3d, ships):
		self.g3d = g3d
		self.cbg = cbg
		self.ships = ships
		self.objects = []
		self.particles = set()
		for i in range(20):
			self.particles.add(Particle(self, init=True))
		self.roll = 0.0
		self.pitch = 0.0
		self.set_roll_pitch(0.0, 0.0)

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
		obj = Object3D(self, pos, s)
		obj.local_roll_pitch(roll, pitch)
		self.objects.append(obj)
		return obj

	def draw(self):
		for o in self.objects:
			o.draw()
		for p in self.particles:
			p.draw()
			if p.distance() > 250:
				p.reset()

	def move(self, dz):
		dp = (0, 0, -dz)
		for o in self.objects:
			p = o.pos
			o.pos = (p[0] + dp[0], p[1] + dp[1], p[2] + dp[2])
		for o in self.particles:
			p = o.pos
			o.pos = (p[0] + dp[0], p[1] + dp[1], p[2] + dp[2])
