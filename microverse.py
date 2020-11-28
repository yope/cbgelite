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
from math import sqrt, pi, inf
from quaternion import *
from time import sleep
from sounds import SoundFX
from ai import CanisterAi

import asyncio

random.seed(monotonic())

soundfx = SoundFX()

class Object3D:
	def __init__(self, mv, pos, ship, name):
		self.sfx = soundfx
		self.debug = False
		self.alive = True
		self.ai = None
		self.name = name.replace("_", " ").upper()
		self.mv = mv
		self.g3d = mv.g3d
		self.pos = pos
		self.ship = ship
		self.energy = ship.opt_max_energy
		self.nosev = (0, 0, 1)
		self.sidev = (0, 1, 0)
		self.roofv = (1, 0, 0)
		self.distance = self.g3d.distv(self.pos)
		self.roll = 0.0
		self.pitch = 0.0
		self.qwroll = aangle2q((0, 0, 1), 0.0)
		self.qwpitch = aangle2q((1, 0, 0), 0.0)
		self.qwtot = qmult(self.qwpitch, self.qwroll)
		self.qltot = qmult(self.qwpitch, self.qwroll)
		self.local_roll_pitch(0.0, 0.0)
		self.world_roll_pitch(0.0, 0.0)
		self.shot_time = 0

	def die(self):
		self.sfx.play_short_explosion()
		self.vanish()
		self.mv.spawn_explosion(self.pos, self.ship.opt_can_on_demise)

	def vanish(self):
		self.alive = False
		self.mv.remove_object(self)

	def add_ai(self, AiCls):
		self.ai = AiCls(self)

	def handle(self):
		if self.ai:
			self.ai.handle()
		self.distance = self.g3d.distv(self.pos)
		if self.energy < self.ship.opt_max_energy:
			self.energy += 0.1

	def check_collision(self, d):
		d = self.distance - d - self.ship.opt_target_area
		return d <= 0.0

	def shoot(self, hit):
		if self.shot_time or self.mv.dead:
			return
		self.shot_time = 8
		pan = self.pos[0] / self.distance
		if hit:
			self.sfx.play_hit(pan)
			self.mv.get_hit(self.ship.opt_laser_power, self.pos)
		else:
			self.sfx.play_shot(pan)

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
		x, y, z = self.pos
		if z < 0:
			return False
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
		if self.shot_time > 0:
			if self.shot_time > 2:
				gvert = s.opt_gun_vertex // 4
				gp = self.transform(s.vert[gvert])
				gpd = g.distv(gp) / 14
				d0 = gpd * (16 - self.shot_time * 2)
				d1 = gpd * (19 - self.shot_time * 2)
				sp = self.scale_add(self.nosev, gp, d0)
				dp = self.scale_add(self.nosev, gp, d1)
				g.line(sp, dp)
			self.shot_time -= 1

class Particle:
	def __init__(self, g3d):
		self.g3d = g3d
		self.rad = 250
		self.maxdist = self.rad
		self.mindist = 50
		self.pos = (
			random.uniform(-self.rad, self.rad),
			random.uniform(-self.rad, self.rad),
			random.uniform(1, self.maxdist)
		)

	def reset(self, js=0.0):
		r = self.rad + js
		self.pos = (random.uniform(-r, r), random.uniform(-r, r), random.uniform(self.mindist+js/2, self.maxdist+js*2))

	def distance(self):
		return sqrt(sum((n*n for n in self.pos)))

	def draw(self, js):
		if js == 0.0:
			self.g3d.point(self.pos)
		else:
			x, y, z = self.pos
			z0 = min(max(5.0, z - js/10), z)
			self.g3d.line((x, y, z), (x, y, z0))
		if self.distance() > self.maxdist:
			self.reset(js)

class DustParticle(Particle):
	def __init__(self, g3d, pos):
		super().__init__(g3d)
		self.rad = 10000
		self.pos = pos

	def draw(self, js):
		self.g3d.point(self.pos)
		x, y, z = self.pos
		rnd = random.uniform
		self.pos = x + rnd(-1, 1), y + rnd(-1, 1), z + rnd(-1, 1)

class Planet:
	def __init__(self, mv, name, pos, dia):
		self.mv = mv
		self.g3d = mv.g3d
		self.name = name
		self.pos = pos
		self.diameter = dia
		self.fill = 0

	def draw(self):
		x, y, z = self.pos
		x0, y0 = self.g3d.project2d(x, y, z)
		if x0 is None:
			return
		x1, y1 = self.g3d.project2d(x + self.diameter, y, z)
		rp = int(x1 - x0)
		if (x0 - rp) > 400 or (x0 + rp) < 0 or (y0 - rp) > 200 or (y0 + rp) < 0:
			return
		rp = min(rp, 1000)
		self.g3d.cbg.ellipse(int(x0), int(y0), rp, rp, fill=self.fill)

	def move_z(self, dz):
		x, y, z = self.pos
		self.pos = (x, y, z + dz)

	def rotate_q(self):
		self.pos = self.g3d.rotate_q(self.pos)

class Sun(Planet):
	def __init__(self, mv, name, pos, dia):
		super().__init__(mv, name, pos, dia)
		self.fill = 2 # Fuzzy fill

class Microverse:
	def __init__(self, cbg, g3d, laser, ships, particles=400):
		self.sfx = soundfx
		self.loop = asyncio.get_event_loop()
		self.g3d = g3d
		self.cbg = cbg
		self.ships = ships
		self.laser = laser
		self.objects = []
		self.particles = set()
		self.max_particles = particles
		for i in range(particles):
			self.particles.add(Particle(self.g3d))
		if particles:
			pd = 300000
			pr = 15000
			dps = 1000000
			self.planet = Planet(self, "Lave", (0, 0, pd), pr)
			self.sun = Sun(self, "Lave's Sun", (0, 0, -dps + pd), 40000)
			self.station = self.spawn("coriolis_space_station", (pr*0.85, pr*0.85, pd), 0.0, 0.0)
		else:
			self.planet = None
			self.sun = None
			self.station = None
		self.roll = 0.0
		self.pitch = 0.0
		self.set_roll_pitch(0.0, 0.0)
		self.flashtext = ""
		self.flashtout = 0
		self.subtext = ""
		self.subtout = 0
		self.speed = 0.0
		self.jumpspeed = 0.0
		self.energy = 1.0
		self.front_shield = 1.0
		self.aft_shield = 1.0
		self.jumping = False
		self.dead = False

	def die(self):
		self.spawn_explosion((0,0,0), 4)
		self.sfx.play_explosion()
		self.move(-500)
		self.dead = True
		self.speed = 0
		self.jumping = False
		self.jumpspeed = 0.0

	def get_hit(self, power, pos):
		self._handle_hit(power / 2, pos)

	def get_planet_dist(self):
		if not self.planet:
			return inf
		return self.g3d.distv(self.planet.pos)

	def get_station_dist(self):
		if not self.station:
			return inf
		return self.station.distance

	def set_speed(self, speed):
		self.speed = speed

	def _handle_hit(self, amount, pos):
		if pos[2] < 0.0: # Hit from behind
			shield = self.aft_shield
		else:
			shield = self.front_shield
		energy = 150*self.energy + 20*shield - amount
		if energy < 0:
			self.die()
			return False
		self.energy = min(energy / 150, 1.0)
		shield = max(0.0, energy / 150 - 1.0)
		if pos[2] < 0.0:
			self.aft_shield = shield
		else:
			self.front_shield = shield
		return True

	def handle_collision_with(self, obj):
		if self._handle_hit(obj.energy, obj.pos):
			obj.die()
			return True
		return False

	def handle(self):
		self.move(self.speed + self.jumpspeed)
		for o in self.objects:
			o.handle()
			if not self.dead and o.check_collision(95): # Target area of Cobra MK III
				if not self.handle_collision_with(o):
					return False
		if self.station:
			self.station.local_roll_pitch(0.005, 0.0)
		if not self.dead:
			if self.energy < 1.0:
				self.energy += 0.0002
			elif self.aft_shield < 1.0:
				self.aft_shield += 0.0005
			elif self.front_shield < 1.0:
				self.front_shield += 0.0005
		return not self.dead

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
		if self.planet:
			self.planet.rotate_q()
		if self.sun:
			self.sun.rotate_q()

	def spawn(self, name, pos, roll, pitch):
		s = self.ships[name]
		obj = Object3D(self, pos, s, name)
		obj.local_roll_pitch(roll, pitch)
		self.objects.append(obj)
		return obj

	def _remove_particles(self, particles):
		for p in particles:
			self.particles.discard(p)

	def spawn_explosion(self, pos, can_on_demise):
		cans = random.randint(0, can_on_demise)
		rnd = random.uniform
		x, y, z = pos
		for i in range(cans):
			can = self.spawn("cargo_canister", (x + 50*i, y+20*i, z+40*i), rnd(0, 3), rnd(0, 3))
			can.add_ai(CanisterAi)
		particles = []
		for i in range(42):
			p = DustParticle(self.g3d, (x + rnd(-200, 200), y + rnd(-200, 200), z + rnd(-200, 200)))
			particles.append(p)
			self.particles.add(p)
		self.loop.call_later(10, self._remove_particles, particles)

	def remove_object(self, obj):
		self.objects.remove(obj)

	def set_flashtext(self, s):
		self.flashtext = s
		self.flashtout = 50

	def set_subtext(self, s):
		self.subtext = s
		self.subtout = 30

	def draw(self):
		trg = None
		for o in self.objects:
			o.draw()
			if o.on_target():
				trg = o
		for p in self.particles:
			p.draw(self.jumpspeed)
		if self.planet:
			self.planet.draw()
		if self.sun:
			self.sun.draw()
		if self.dead:
			return self.draw_dead()
		if self.flashtout:
			slen = len(self.flashtext) * 8
			x = (320 - slen) // 2
			self.cbg.drawtext(x, 16, self.flashtext)
			self.flashtout -= 1
		if self.subtout:
			slen = len(self.subtext) * 8
			x = (320 - slen) // 2
			self.cbg.drawtext(x, 160, self.subtext)
			self.subtout -= 1
		if self.laser:
			self.laser.draw(self, trg)

	def draw_dead(self):
		self.cbg.drawtext(120, 100, "GAME OVER!")

	def move(self, dz):
		for o in self.objects:
			x, y, z = o.pos
			o.pos = (x, y, z - dz)
		for o in self.particles:
			x, y, z = o.pos
			o.pos = (x, y, z - dz)
		if self.planet:
			self.planet.move_z(-dz)
		if self.sun:
			self.sun.move_z(-dz)

	def jump(self):
		if self.jumping:
			return
		if self.get_planet_dist() < 80000:
			self.set_subtext("Too Close")
			return
		j = self.loop.create_task(self.coro_jump())
		j.add_done_callback(lambda f: f.result())
		self.jumping = True

	async def _check_jump_dist(self, ramp=0.0):
		self.set_subtext("JUMP")
		for t in range(20):
			if self.get_planet_dist() < 80000 or self.dead:
				self.jumpspeed = 0.0
				return False
			self.jumpspeed += ramp
			await asyncio.sleep(0.1)
		return True

	async def coro_jump(self):
		self.sfx.play_jump()
		if not await self._check_jump_dist(15.0):
			return
		self.jumpspeed = 300.0
		for i in range(2):
			if not await self._check_jump_dist(0.0):
				return
		if not await self._check_jump_dist(-15.0):
			return
		self.jumpspeed = 0.0
		self.jumping = False

	def shot_fired(self, target):
		if target:
			self.sfx.play_myhit()
			if target.energy > 20:
				target.energy -= 20
			else:
				target.die()
		else:
			self.sfx.play_myshot()
