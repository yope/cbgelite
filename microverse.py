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
from math import sqrt, pi, inf, sin, cos
from quaternion import *
from time import sleep
from sounds import SoundFX
from ai import CanisterAi, BaseAi

import asyncio

random.seed(monotonic())

soundfx = SoundFX()

class Object3D:
	def __init__(self, g3d, pos):
		self.g3d = g3d
		self.pos = pos
		self.nosev = (0, 0, 1)
		self.lnosev = (0, 0, 1)
		self.sidev = (1, 0, 0)
		self.lsidev = (1, 0, 0)
		self.roofv = (0, 1, 0)
		self.distance = self.g3d.distv(self.pos)
		self.roll = 0.0
		self.pitch = 0.0
		self.qwroll = aangle2q((0, 0, 1), 0.0)
		self.qwpitch = aangle2q((1, 0, 0), 0.0)
		self.qwtot = qmult(self.qwpitch, self.qwroll)
		self.qltot = qmult(self.qwpitch, self.qwroll)
		self.local_roll_pitch(0.0, 0.0)
		self.world_roll_pitch(0.0, 0.0)

	def local_roll_pitch(self, roll, pitch):
		qroll = aangle2q(self.lnosev, roll)
		qpitch = aangle2q(self.lsidev, pitch)
		self.qltot = qmult(qmult(qpitch, qroll), self.qltot)
		self.qlcon = qconj(self.qltot)
		self.lsidev = self._qlrot((1, 0, 0))
		self.lnosev = self._qlrot((0, 0, 1))

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

	def handle(self):
		self.distance = self.g3d.distv(self.pos)

class Ship3D(Object3D):
	def __init__(self, mv, pos, ship, name):
		super().__init__(mv.g3d, pos)
		self.sfx = soundfx
		self.debug = False
		self.alive = True
		self.ai = None
		self.name = name.replace("_", " ").upper()
		self.mv = mv
		self.ship = ship
		self.energy = ship.opt_max_energy
		self.shot_time = 0

	def die(self):
		self.sfx.play_short_explosion()
		self.vanish()
		self.mv.spawn_explosion(self.pos, self.ship.opt_can_on_demise)
		bounty = self.ship.opt_bounty * 1000
		self.mv.cd.bitcoin += bounty / 100000000
		self.mv.set_flashtext("Bounty: {} sats".format(bounty))

	def vanish(self):
		self.alive = False
		self.mv.remove_object(self)

	def add_ai(self, AiCls):
		self.ai = AiCls(self)

	def handle(self):
		super().handle()
		if self.ai:
			self.ai.handle()
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

	def on_target(self):
		x, y, z = self.pos
		if z < 0:
			return False
		r = self.ship.opt_target_area
		if (x + r) > 0 and (x - r) < 0 and (y + r) > 0 and (y - r) < 0:
			return True
		else:
			return False

	def draw(self, pattern=None):
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
			if not g.visible(p0, n):
				continue
			for ei in fe:
				e = s.edge[ei]
				p0 = self.transform(s.vert[e[0]])
				p1 = self.transform(s.vert[e[1]])
				g.line(p0, p1, pattern=pattern)
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
		self.vec = (0, 0, 0)

	def set_dir(self, vx, vy, vz):
		self.vec = (vx / 15, vy / 15, vz / 15)

	def draw(self, js):
		self.g3d.point(self.pos)
		x, y, z = self.pos
		vx, vy, vz = self.vec
		rnd = random.uniform
		self.pos = x + vx + rnd(-1, 1), y + vy + rnd(-1, 1), z + vz + rnd(-1, 1)

class Planet(Object3D):
	def __init__(self, mv, name, pos, dia):
		super().__init__(mv.g3d, pos)
		self.mv = mv
		self.name = name
		self.diameter = 2 * dia / 3
		self.fill = 0
		self.local_roll_pitch(0.7, 1.3)

	def draw(self):
		x, y, z = self.pos
		x0, y0 = self.g3d.project2d(x, y, z)
		if x0 is None:
			return
		x1, y1 = self.g3d.project2d(x, y + self.diameter, z)
		rp = int(abs(y1 - y0))
		if (x0 - rp) > 400 or (x0 + rp) < 0 or (y0 - rp) > 200 or (y0 + rp) < 0:
			return
		rp0 = min(rp, 1000)
		self.g3d.cbg.ellipse(int(x0), int(y0), rp0, rp0, fill=self.fill)
		if self.fill == 0:
			self.draw_crater(rp, rp0)

	def draw_crater(self, rp, rp0):
		g = self.g3d
		sf = rp / rp0
		r = sf * self.diameter / 2
		r3 = r / 2
		h = 4 * r / 5
		y0 = -h
		x0 = 0
		z0 = r3
		n = self.normrotate((0, -1, 0))
		p0 = self.transform((x0, y0, z0))
		if not g.visible(p0, n):
			return
		phi = 2 * pi / 20
		for i in range(1, 21):
			x = r3 * sin(i * phi)
			z = r3 * cos(i * phi)
			p = self.transform((x, y0, z))
			g.line(p0, p)
			p0 = p

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
	VIEW_FRONT = "pz"
	VIEW_REAR = "nz"
	VIEW_RIGHT = "px"
	VIEW_LEFT = "nx"
	def __init__(self, cbg, g3d, laser, ships, cd, universe, particles=400, hyperspace=False):
		self.sfx = soundfx
		self.loop = asyncio.get_event_loop()
		self.g3d = g3d
		self.cbg = cbg
		self.ships = ships
		self.laser = laser
		self.cd = cd
		self.universe = universe
		self.objects = []
		self.particles = set()
		self.max_particles = particles
		for i in range(particles):
			self.particles.add(Particle(self.g3d))
		if particles:
			s = self.universe.get_system_by_index(self.cd.galaxy, self.cd.system)
			dps = 1000000
			pr = s.radius * 3
			if hyperspace:
				pd = 300000
				self.sun = Sun(self, s.name+"'s Sun", (0, 0, -dps + pd), 40000)
				self.station = self.spawn("coriolis_space_station", (pr*0.85, pr*0.85, pd), 0.0, 0.0)
			else:
				pd = pr * 0.84
				self.sun = Sun(self, s.name + "'s Sun", (dps, 0, pd), 40000)
				self.station = self.spawn("coriolis_space_station", (0, 0, -256), 0.0, 0.0)
			self.planet = Planet(self, s.name, (0, 0, pd), pr)
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
		self.stopped = False
		self.countdown = False
		self.hyperspacing = False
		self.cd.docked = False
		self.view_names = {
				self.VIEW_FRONT: "Front View",
				self.VIEW_REAR: "Rear View",
				self.VIEW_RIGHT: "Right View",
				self.VIEW_LEFT: "Left View"
			}
		self.set_view(self.VIEW_FRONT)
		self.tactic_task = self.loop.create_task(self.coro_tactic())

	def set_view(self, view):
		self.g3d.set_camera(view)
		self.view = view
		self.view_name = self.view_names[view]
		self.view_name_x = (320 - len(self.view_name) * 8) // 2

	def get_view(self):
		return self.view

	async def coro_tactic(self):
		cd = self.cd
		ntrans = 0
		rocks = ("asteroid", "rock", "boulder")
		enemies = ("cobra_mkiii", "anaconda", "python", "boa", "mamba", "krait",
				"adder", "gecko", "cobra_mki", "asp_mkii", "fer-de-lance",
				"sidewinder", "moray_start_boat")
		rnd = random.uniform
		while not cd.docked and not self.dead:
			dice = random.random()
			ds = 1000000 if not self.station else self.station.distance
			if ds > 55000 and len(self.objects) < 12:
				if dice < 0.05:
					if not self.planet:
						continue
					pp = self.planet.pos
					pvn = self.g3d.normalize(pp)
					n = random.choice(rocks)
					d = rnd(20000, 25000)
					self.spawn(n, (pvn[0] * d + rnd(-200, 200), pvn[1] * d + rnd(-200, 200), pvn[2] * d + rnd(-200, 200)),
							rnd(0, 6.2), rnd(0, 6.2))
				elif 0.10 < dice < 0.135:
					n = random.choice(enemies)
					r = rnd(7000, 15000)
					a = rnd(0, 3.1)
					x = r * cos(a)
					z = r * sin(a)
					y = rnd(-3000, 3000)
					s = self.spawn(n, (x, y, z), rnd(0, 6.2), rnd(0, 6.2))
					s.add_ai(BaseAi)
					self.cbg.log("Added {} at {!r}".format(n, (x, y, z)))
			await asyncio.sleep(2.0)

	def stop(self):
		self.stopped = True
		for o in self.objects:
			o.vanish()

	def restart(self):
		self.stopped = False
		for p in self.particles:
			p.reset()

	def hyperspace(self):
		if self.countdown:
			return
		if self.cd.target == self.cd.system:
			return
		d = self.universe.get_distance_by_index(self.cd.galaxy, self.cd.system, self.cd.target)
		if d > self.cd.fuel:
			self.set_subtext("Not enough fuel!")
			return
		st = self.universe.get_system_by_index(self.cd.galaxy, self.cd.target)
		hct = self.loop.create_task(self.hyperspace_countdown(st, d))
		hct.add_done_callback(lambda fut: fut.result())
		self.countdown = True

	async def hyperspace_countdown(self, st, d):
		t = 9
		while not self.dead and t > 0:
			self.set_subtext("Hyperspace to {} {}".format(st.name, t))
			await asyncio.sleep(1)
			t -= 1
		self.countdown = False
		if t == 0:
			self.hyperspacing = True
		self.cd.fuel -= d

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

	def handle_docking(self):
		self.cd.docked = True

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
				if o is self.station:
					alignn = self.g3d.dot(o.nosev, (0, 0, 1))
					alignr = abs(self.g3d.dot(o.sidev, (0, 1, 0)))
					dx = abs(o.pos[0])
					dy = abs(o.pos[1])
					if alignn < -0.96 and dx < 40 and dy < 30 and alignr > 0.85:
						self.cbg.log("DOCKED!", alignn, alignr, dx, dy)
						self.handle_docking()
						return False
					self.cbg.log("NOT DOCKED!", alignn, alignr, dx, dy)
				if not self.handle_collision_with(o):
					return False
		if self.station:
			self.station.local_roll_pitch(0.005, 0.0)
		if self.planet:
			self.planet.handle()
			self.planet.local_roll_pitch(0.01, 0.0)
		if not self.dead:
			if self.energy < 1.0:
				self.energy += 0.0002
			elif self.aft_shield < 1.0:
				self.aft_shield += 0.0005
			elif self.front_shield < 1.0:
				self.front_shield += 0.0005
		return not self.dead and not self.hyperspacing

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
			self.planet.world_roll_pitch(roll, pitch)
		if self.sun:
			self.sun.rotate_q()

	def spawn(self, name, pos, roll, pitch):
		s = self.ships[name]
		obj = Ship3D(self, pos, s, name)
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
			xp, yp, zp = x + rnd(-20, 20), y + rnd(-20, 20), z + rnd(-20, 20)
			vx, vy, vz = xp - x, yp - y, zp - z
			p = DustParticle(self.g3d, (xp, yp, zp))
			p.set_dir(vx, vy, vz)
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
		if self.particles: # FIXME!
			self.cbg.drawtext(self.view_name_x, 8, self.view_name)
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
		if self.get_planet_dist() < 60000:
			self.set_subtext("Too Close")
			return
		j = self.loop.create_task(self.coro_jump())
		j.add_done_callback(lambda f: f.result())
		self.jumping = True

	async def _check_jump_dist(self, ramp=0.0):
		self.set_subtext("JUMP")
		for t in range(20):
			if self.get_planet_dist() < 60000 or self.dead:
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
