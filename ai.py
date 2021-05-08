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
import random

random.seed()

class BaseAi:
	MOVE_AWAY = 0
	MOVE_RANDOM = 1
	MOVE_TO = 2
	def __init__(self, obj):
		self.obj = obj
		self.g3d = obj.g3d
		self.cbg = obj.mv.cbg
		self.loop = asyncio.get_event_loop()
		self.task = self.loop.create_task(self.task())
		self.max_speed = obj.ship.opt_max_speed / 2
		self.speed = self.max_speed / 2
		self.roll = 0.0
		self.randpitch = 0.0
		self.strat = self.MOVE_TO
		self.dn = 0.0
		self.task.add_done_callback(lambda fut: fut.result())

	def handle(self):
		o = self.obj
		g = self.g3d
		o.pos = o.scale_add(o.nosev, o.pos, self.speed)
		if o.distance > 50000:
			self.obj.vanish()
			return
		hvec = g.normalize(tuple(-x for x in o.pos))
		self.dn = dn = g.dot(o.nosev, hvec)
		ds = g.dot(o.sidev, hvec)
		dr = g.dot(o.roofv, hvec)
		if self.dn > 0.95:
			canshoot = True
		else:
			canshoot = False
		p = 0.0
		r = self.roll
		if self.strat is self.MOVE_TO:
			if dn > ds and dn > dr:
				if dr > 0.0:
					p = -0.02
				else:
					p = 0.02
			elif ds > dn and ds > dr:
				r = 0.02
			elif dr > ds and dr > dn:
				p = -0.02
		elif self.strat is self.MOVE_AWAY:
			if self.dn > -0.5:
				p = 0.01
		else: # MOVE_RANDOM
			p = self.randpitch
			#self.cbg.log(o.name + " move random {:6.1f}".format(self.dist))
		if r or p:
			o.local_roll_pitch(r, p)

	async def _movement_strategy(self, x, ts):
		o = self.obj
		if x > 0.9:
			self.roll = 0.02
		elif x < 0.1:
			self.roll = -0.02
		else:
			self.roll = 0.0
		if x > 0.98 and self.strat is self.MOVE_TO:
			self.strat = self.MOVE_RANDOM
			self.speed = self.max_speed
			ts = 0
		elif self.strat is self.MOVE_RANDOM and x < 0.3 and o.angry:
			self.strat = self.MOVE_TO
			self.speed = self.max_speed * 0.7
			ts = 0
		elif self.strat is self.MOVE_AWAY and o.distance >= 5000:
			self.strat = self.MOVE_TO
			self.speed = self.max_speed * 0.9
			ts = 0
		elif self.strat is self.MOVE_TO and o.distance <= 2000:
			self.strat = self.MOVE_AWAY
			self.speed = self.max_speed * 0.8
			ts = 0
		ts += 1
		if ts > 500:
			self.strat = self.MOVE_RANDOM
			speed = self.max_speed * 0.85
			ts = 0
		if self.strat is self.MOVE_RANDOM:
			self.roll = random.uniform(-0.06, 0.06)
			self.randpitch = random.uniform(-0.06, 0.06)
			await asyncio.sleep(0.2)
		return ts

	async def _shooting_strategy(self, x, ts):
		o = self.obj
		if self.dn > 0.975 and o.distance < 30000:
			if x < 0.3 and o.angry:
				o.shoot(True)
		elif self.dn > 0.95 and o.distance < 25000:
			if x < 0.2 and o.angry:
				o.shoot(False)
		return ts

	async def _missile_strategy(self, x, ts):
		o = self.obj
		if o.angry and o.missiles and o.energy < (o.ship.opt_max_energy / 2):
			if x < (0.03 * o.missiles):
				o.launch_missile()
		return ts

	async def task(self):
		ts = 0
		while self.obj.alive:
			await asyncio.sleep(0.1)
			x = random.random()
			ts = await self._movement_strategy(x, ts)
			ts = await self._shooting_strategy(x, ts)
			ts = await self._missile_strategy(x, ts)

class CanisterAi:
	def __init__(self, obj):
		self.obj = obj
		rnd = random.uniform
		self.vec = (rnd(-1, 1), rnd(-1, 1), rnd(-1, 1))
		self.roll = rnd(-0.01, 0.01)
		self.pitch = rnd(-0.01, 0.01)
		self.speed = rnd(0.0, 0.6)

	def handle(self):
		o = self.obj
		o.local_roll_pitch(self.roll, self.pitch)
		o.pos = o.scale_add(self.vec, o.pos, self.speed)

class MissileAi:
	def __init__(self, obj):
		self.obj = obj
		self.trg = None
		self.g3d = obj.g3d
		self.cbg = obj.mv.cbg
		self.max_speed = obj.ship.opt_max_speed / 1.5
		self.min_speed = self.max_speed / 8
		self.speed = self.max_speed

	def add_target(self, target):
		self.trg = target

	def _hit_target(self):
		return self.obj.hit_target(self.trg)

	def handle(self):
		o = self.obj
		g = self.g3d
		t = self.trg
		o.pos = o.scale_add(o.nosev, o.pos, self.speed)
		if o.distance > 50000:
			self.obj.vanish()
			return
		if not t.alive:
			o.target_lost()
			return
		tdir = g.sub(t.pos, o.pos)
		tdist = g.distv(tdir)
		if tdist < 150:
			self._hit_target()
			return
		sdist = g.distv(o.pos)
		if sdist < 800:
			# Try to move away from cobra at max speed before slowing down.
			return
		hvec  = g.normalize(tdir)
		dn = g.dot(o.nosev, hvec)
		ds = g.dot(o.sidev, hvec)
		dr = g.dot(o.roofv, hvec)
		p = 0.0
		r = 0.0
		if dn > 0.7:
			self.speed = self.max_speed
		else:
			self.speed = self.min_speed
		ddn = abs(1 - dn) / 2
		if ddn > abs(dr) and ddn > abs(ds):
			if dr > 0.0:
				p = -0.04
			else:
				p = 0.04
		elif abs(dr) > abs(ds):
			if dr > 0.0:
				p = -0.04
			else:
				p = 0.04
		else:
			if ds > 0.0:
				r = 0.04
			else:
				r = -0.04
		if r or p:
			o.local_roll_pitch(r, p)

class MissileTargetDummy:
	def __init__(self):
		self.pos = (0, 0, 0)
		self.alive = True

class EnemyMissileAi(MissileAi):
	def __init__(self, obj):
		super().__init__(obj)
		self.trg = MissileTargetDummy()

	def _hit_target(self):
		self.obj.hit_player()

class ThargoidAi(BaseAi):
	pass
